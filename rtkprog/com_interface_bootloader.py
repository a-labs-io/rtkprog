# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from pathlib import Path
from struct import pack

from crccheck.crc import CrcArc

from .chips import CHIP_REGISTRY, ChipConfig
from .exceptions import (
    CRCError,
    ProtocolError,
    UnknownChipError,
    UnsupportedOperationError,
)
from .serial import SerialInterface

_FW_DIR: Path = Path(os.environ.get("RTKPROG_FW_DIR", Path(__file__).parent.parent / "fw"))

_HCI_START_FW_LOADER_PREFIX: bytes = b"\x01\x62\xfc\x09\x20"
_START_FW_LOADER_RESPONSE_HEADER: bytes = b"\x04\x0e\x04\x02\x62\xfc"
_START_FW_LOADER_RESPONSE_LENGTH: int = 93
_EUID_OFFSET: int = 69
_EUID_LENGTH: int = 14

# Chip probe
INIT_PROBE_TX: bytes = b"\x01\x61\xfc\x05\x20\x00\x20\x03\x00"
INIT_PROBE_RX_LENGTH: int = 11

# Firmware-loader
HCI_OPCODE_WRITE_RAM: bytes = b"\x01\x20\xfc"
LOADER_CHUNK_SIZE: int = 0xFC  # 252 bytes per frame
LOADER_FRAME_ACK_HEADER: bytes = b"\x04\x0e\x05\x02\x20\xfc\x00"

# eFuse
EFUSE_RESPONSE_LENGTH: int = 11
EFUSE_RESPONSE_PREFIX: bytes = b"\x04\x0e\x08\x02\x61\xfc\x00\xff"
EFUSE_CRC16_UNBURNED: bytes = b"\xff\xff"
EFUSE_CRC16_SIZE: int = 2


class BootloaderComInterface:
    """Communication with Realtek chip in bootloader mode."""

    def __init__(
        self,
        transport: SerialInterface,
    ) -> None:
        self._transport = transport
        self._log = logging.getLogger("rtkprog.bootloader")

    def probe_chip(self) -> ChipConfig:
        self._log.info("Probing chip")
        self._transport.transmit(INIT_PROBE_TX)
        response = self._transport.receive(INIT_PROBE_RX_LENGTH)
        chip = CHIP_REGISTRY.get(response)
        if chip is None:
            raise UnknownChipError(f"Unrecognised chip init response: {response.hex()}")
        self._log.info("Detected: %s", chip.name)
        return chip

    def upload_firmware_loader(self, chip: ChipConfig) -> None:
        self._log.info("Uploading firmware loader")
        firmware = b"".join(
            (_FW_DIR / name).read_bytes() for name in chip.loader_firmware_files
        )
        for frame_index, offset in enumerate(range(0, len(firmware), LOADER_CHUNK_SIZE)):
            chunk = firmware[offset : offset + LOADER_CHUNK_SIZE]
            frame_byte = pack("B", frame_index & 0xFF)
            packet = HCI_OPCODE_WRITE_RAM + pack("B", len(chunk) + 1) + frame_byte + chunk
            expected_ack = LOADER_FRAME_ACK_HEADER + frame_byte

            self._transport.transmit(packet)
            ack = self._transport.receive(len(expected_ack))
            if ack != expected_ack:
                raise ProtocolError(
                    f"Loader frame {frame_index}: unexpected ack {ack.hex()}"
                )

    def start_firmware_loader(self, chip: ChipConfig) -> None:
        self._log.info("Starting firmware loader")
        request = _HCI_START_FW_LOADER_PREFIX + chip.fw_loader_params
        self._transport.transmit(request)
        response = self._transport.receive(_START_FW_LOADER_RESPONSE_LENGTH)

        header_len = len(_START_FW_LOADER_RESPONSE_HEADER)
        header, payload = response[:header_len], response[header_len:]

        if CrcArc.calc(payload) != 0:
            raise CRCError("Firmware loader start response CRC mismatch")
        if header != _START_FW_LOADER_RESPONSE_HEADER:
            raise ProtocolError(
                f"Unexpected firmware loader response header: {header.hex()}"
            )

        euid = payload[_EUID_OFFSET : _EUID_OFFSET + _EUID_LENGTH]
        self._log.info("EUID: %s", " ".join(f"{b:02X}" for b in euid))

    def read_efuse_crc16(self, chip: ChipConfig) -> bytes:
        if chip.efuse_register is None:
            raise UnsupportedOperationError(
                f"{chip.name} does not support eFuse operations"
            )

        packet = b"\x01\x61\xfc\x05\x20" + pack("<I", chip.efuse_register)
        self._transport.transmit(packet)
        response = self._transport.receive(EFUSE_RESPONSE_LENGTH)

        if (
            len(response) != EFUSE_RESPONSE_LENGTH
            or response[:8] != EFUSE_RESPONSE_PREFIX
        ):
            raise ProtocolError(f"Unexpected eFuse response: {response.hex()}")

        if chip.efuse_crc16_offset is None:
            raise UnsupportedOperationError(
                f"{chip.name}: efuse_register is set but efuse_crc16_offset is missing"
            )

        return response[
            chip.efuse_crc16_offset : chip.efuse_crc16_offset + EFUSE_CRC16_SIZE
        ]
