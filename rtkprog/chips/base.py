# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass(frozen=True)
class ChipConfig:
    # Name of the Chip
    name: str

    # Chip ID (last byte of the probe response)
    chip_id: int

    # Fallback for chip identification, magic word read from ROM address 0x00032000
    magic_word: int | None

    # Firmware loader files (filenames only, resolved against the fw/ directory)
    loader_firmware_files: tuple[str, ...]

    # Flash memory map
    flash_start: int
    flash_end: int
    flash_page_size: int

    # MAC address location in flash, None if MAC operations are not supported
    flash_address_mac: int | None

    # eFuse register address, None if not supported
    efuse_register: int | None
    # Offset in eFuse response where the 2-byte CRC16 starts, None if not supported
    efuse_crc16_offset: int | None

    # Chip-specific trigger address / value for starting the FW loader
    fw_loader_trigger_addr: int
    fw_loader_trigger_value: int

    @property
    def flash_size(self) -> int:
        return self.flash_end - self.flash_start
