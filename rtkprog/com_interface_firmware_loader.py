# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

import logging
from enum import IntEnum
from struct import pack, unpack
from time import sleep

from crccheck.crc import CrcArc

from .bluetooth_mac import BluetoothMAC
from .chips import ChipConfig
from .exceptions import CRCError, ProtocolError
from .serial import SerialInterface


class FirmwareLoaderOpcode(IntEnum):
    """FW Loader UART opcodes"""

    CHANGE_BAUD = 0x1010
    ERASE_SECTOR = 0x1030
    WRITE = 0x1032
    READ = 0x1033
    VERIFY = 0x1050


class FirmwareLoaderComInterface:
    """Communication with Realtek chip in firmware loader mode."""

    _MARKER = 0x87
    _HEADER_SIZE = 8  # marker(1) + opcode(2) + status(1) + payload_len(4)
    _CRC_SIZE = 2
    _POST_BAUD_CHANGE_DELAY: float = 0.4  # seconds to wait after baud-rate switch

    def __init__(self, transport: SerialInterface, chip: ChipConfig) -> None:
        self._transport = transport
        self._log = logging.getLogger("rtkprog.fwloader")
        self._chip = chip

    def _execute(
        self,
        opcode: FirmwareLoaderOpcode,
        params: bytes = b"",
        expected_payload_size: int = 0,
    ) -> bytes:

        # Build & transmit
        opcode_bytes = pack("<H", opcode)
        request = bytes([self._MARKER]) + opcode_bytes + params
        request += pack("<H", CrcArc.calc(request))
        self._transport.transmit(request)

        # Receive
        response_len = self._HEADER_SIZE + expected_payload_size + self._CRC_SIZE
        response = self._transport.receive(response_len)

        # Validate
        if CrcArc.calc(response) != 0:
            raise CRCError(f"{opcode.name}: response CRC mismatch")

        expected_header = bytes([self._MARKER]) + opcode_bytes
        if response[:3] != expected_header:
            raise ProtocolError(
                f"{opcode.name}: opcode mismatch in response: {response[:3].hex()}"
            )

        status = response[3]
        if status != 0x00:
            raise ProtocolError(f"{opcode.name}: failed with status 0x{status:02x}")

        payload_len = unpack("<I", response[4:8])[0]
        if payload_len != expected_payload_size:
            raise ProtocolError(
                f"{opcode.name}: expected {expected_payload_size} payload bytes, "
                f"got {payload_len}"
            )

        if expected_payload_size:
            return response[self._HEADER_SIZE : -self._CRC_SIZE]
        return b""

    def erase_page(self, address: int) -> None:
        self._log.debug("Erasing page at 0x%08x", address)
        self._execute(
            FirmwareLoaderOpcode.ERASE_SECTOR,
            pack("<II", address, self._chip.flash_page_size),
        )

    def erase_sectors(self, address: int, size: int) -> None:
        page_size = self._chip.flash_page_size
        num_pages = (size + page_size - 1) // page_size
        self._log.info("Erasing %d page(s) at 0x%08x", num_pages, address)
        for i in range(num_pages):
            self.erase_page(address + i * page_size)

    def erase_all(self) -> None:
        self._log.info("Erasing entire flash (%d KB)", self._chip.flash_size // 1024)
        for address in range(
            self._chip.flash_start, self._chip.flash_end, self._chip.flash_page_size
        ):
            self.erase_page(address)

    def write(self, address: int, data: bytes) -> None:
        self._write_pages(address, data)

    def read_mac(self) -> BluetoothMAC:
        page_size = self._chip.flash_page_size
        page_start = (self._chip.flash_address_mac // page_size) * page_size
        page_offset = self._chip.flash_address_mac - page_start
        page = self.read(page_start, page_size)
        return BluetoothMAC.from_reverse_bytes(page[page_offset : page_offset + 6])

    def _write_pages(self, address: int, data: bytes) -> None:
        self.erase_sectors(address, len(data))
        page_size = self._chip.flash_page_size
        self._log.info("Writing %d bytes to 0x%08x", len(data), address)

        for offset in range(0, len(data), page_size):
            chunk = data[offset : offset + page_size]
            chunk_addr = address + offset

            self._execute(
                FirmwareLoaderOpcode.WRITE,
                pack("<II", chunk_addr, len(chunk)) + chunk,
            )
            self._execute(
                FirmwareLoaderOpcode.VERIFY,
                pack("<II", chunk_addr, len(chunk)) + pack("<H", CrcArc.calc(chunk)),
            )

    def read(self, address: int, size: int) -> bytes:
        page_size = self._chip.flash_page_size
        self._log.info("Reading %d bytes from 0x%08x", size, address)
        buffer = b""
        for offset in range(0, size, page_size):
            chunk_size = min(page_size, size - offset)
            buffer += self._execute(
                FirmwareLoaderOpcode.READ,
                pack("<II", address + offset, chunk_size),
                expected_payload_size=chunk_size,
            )
            self._log.info("Read %d / %d bytes", offset + chunk_size, size)
        return buffer

    def read_all(self):
        return self.read(self._chip.flash_start, self._chip.flash_size)

    def write_mac(self, mac: BluetoothMAC) -> None:
        page_size = self._chip.flash_page_size
        page_start = (self._chip.flash_address_mac // page_size) * page_size
        page_offset = self._chip.flash_address_mac - page_start

        self._log.info("Writing MAC %s", mac)
        page = bytearray(self.read(page_start, page_size))
        page[page_offset : page_offset + 6] = mac.to_bytes(reverse=True)
        self._write_pages(page_start, bytes(page))

    def change_baud(self, baud: int) -> None:
        self._log.info("Changing baud rate to %d", baud)
        self._execute(
            FirmwareLoaderOpcode.CHANGE_BAUD,
            pack("<I", baud) + b"\xff",
        )
        self._transport.set_baud(baud)
        sleep(self._POST_BAUD_CHANGE_DELAY)
