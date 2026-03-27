# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

import sys
from logging import Logger

from serial.serialutil import SerialException

from .args import (
    CmdArgs,
    EfuseArgs,
    EraseArgs,
    GlobalArgs,
    MacArgs,
    ReadArgs,
    ResetArgs,
    TerminalArgs,
    WriteArgs,
    get_args,
)
from .bluetooth_mac import BluetoothMAC
from .chips import ChipConfig
from .com_interface_bootloader import EFUSE_CRC16_UNBURNED, BootloaderComInterface
from .com_interface_firmware_loader import FirmwareLoaderComInterface
from .exceptions import CRCError, ProtocolError, UnknownChipError, ValidationError
from .logging import configure_logging
from .serial import SerialInterface
from .validation import (
    WritePlanEntry,
    validate_write_plan,
)


def _contains_mac_addr_fully(address: int, size: int, chip: ChipConfig):
    flash_address_mac = chip.flash_address_mac
    return (
        flash_address_mac >= address
        and flash_address_mac + BluetoothMAC.MAC_ADDRESS_SIZE <= address + size
    )


def _patch_mac_addr(log: Logger, data, address, chip: ChipConfig, mac: BluetoothMAC):
    if not (_contains_mac_addr_fully(address, len(data), chip)):
        raise Exception("mac address location not within data")
    flash_address_mac = chip.flash_address_mac

    log.info(f"Patching MAC Address: {mac}")
    return (
        data[: flash_address_mac - address]
        + mac.to_bytes(reverse=True)
        + data[flash_address_mac - address + BluetoothMAC.MAC_ADDRESS_SIZE :]
    )


def _cmd_write(
    log: Logger, args: WriteArgs, fw_loader: FirmwareLoaderComInterface, chip: ChipConfig
) -> None:
    mac_to_set = args.mac

    # Build write plan for pre-flight validation
    write_plan: list[WritePlanEntry] = []
    for rec in args.records:
        with open(rec.file, "rb") as f:
            f.seek(0, 2)
            payload_size = f.tell() - rec.seek
        patch_mac = bool(
            mac_to_set and _contains_mac_addr_fully(rec.address, payload_size, chip)
        )
        write_plan.append(WritePlanEntry(rec.address, payload_size, rec.file, patch_mac))

    validate_write_plan(chip, write_plan)

    if isinstance(mac_to_set, BluetoothMAC) and not any(e.patch_mac for e in write_plan):
        fw_loader.write_mac(mac_to_set)

    for rec in args.records:
        with open(rec.file, "rb") as f:
            f.seek(rec.seek)
            data = f.read()
        if mac_to_set and _contains_mac_addr_fully(rec.address, len(data), chip):
            if mac_to_set == "auto":
                data = _patch_mac_addr(log, data, rec.address, chip, fw_loader.read_mac())
            else:
                data = _patch_mac_addr(log, data, rec.address, chip, mac_to_set)

        fw_loader.write(rec.address, data)


def _cmd_read(args: ReadArgs, fw_loader: FirmwareLoaderComInterface) -> None:
    if args.regions:
        for rec in args.regions:
            data = fw_loader.read(rec.address, rec.size)
            with open(rec.file, "wb") as f:
                f.write(data)
    else:
        data = fw_loader.read_all()
        with open(args.output, "wb") as f:
            f.write(data)


def _cmd_erase(args: EraseArgs, fw_loader: FirmwareLoaderComInterface) -> None:
    if args.regions:
        for region in args.regions:
            fw_loader.erase_sectors(region.address, region.size)
    else:
        fw_loader.erase_all()


def _cmd_mac(log: Logger, args: MacArgs, fw_loader: FirmwareLoaderComInterface) -> None:
    if args.mac:
        fw_loader.write_mac(args.mac)
    else:
        mac = fw_loader.read_mac()
        log.info("MAC Address: %s", mac)


def _cmd_reset(transport: SerialInterface) -> None:
    transport.reset_into_run()


def _cmd_terminal(transport: SerialInterface) -> None:
    transport.reset_into_run(clear_input_buffer=True)
    transport.run_terminal()


def _cmd_efuse(log: Logger, session: BootloaderComInterface, chip: ChipConfig):
    if chip.efuse_register is None or chip.efuse_crc16_offset is None:
        log.info(f"Reading eFuse status not supported for {chip.name} (yet)")
        return

    crc16 = session.read_efuse_crc16(chip)
    status = (
        "Not burned" if crc16 == EFUSE_CRC16_UNBURNED else f"Burned, CRC16: {crc16.hex()}"
    )
    log.info(f"eFuse status: {status}")


def _run(global_args: GlobalArgs, cmd_args: CmdArgs, log: Logger) -> None:
    with SerialInterface(global_args.port) as transport:
        match cmd_args:
            case ResetArgs():
                _cmd_reset(transport)
                return
            case TerminalArgs():
                transport.set_baud(global_args.baud)
                _cmd_terminal(transport)
                return

        transport.reset_into_bootloader()
        session = BootloaderComInterface(transport)
        chip = session.probe_chip()

        match cmd_args:
            case EfuseArgs():
                _cmd_efuse(log=log, session=session, chip=chip)
                return

        session.upload_firmware_loader(chip=chip)
        session.start_firmware_loader(chip=chip)
        fw_loader = FirmwareLoaderComInterface(transport=transport, chip=chip)

        match cmd_args:
            case WriteArgs():
                _cmd_write(log, cmd_args, fw_loader, chip)
            case ReadArgs():
                _cmd_read(cmd_args, fw_loader)
            case EraseArgs():
                _cmd_erase(cmd_args, fw_loader)
            case MacArgs():
                _cmd_mac(log, cmd_args, fw_loader)


def main() -> None:
    global_args, cmd_args = get_args()
    log = configure_logging(global_args.v, global_args.quiet)

    for attempt in range(1, global_args.attempts + 1):
        try:
            _run(global_args, cmd_args, log)
            sys.exit(0)
        except ValidationError as exc:
            log.error("Validation error: %s", exc)
            sys.exit(1)  # No point retrying a validation failure
        except (SerialException, ProtocolError, CRCError, UnknownChipError) as exc:
            if attempt < global_args.attempts:
                log.warning(
                    "Attempt %d/%d failed: %s — retrying",
                    attempt,
                    global_args.attempts,
                    exc,
                )
            else:
                log.error("Error: %s", exc)

    sys.exit(1)
