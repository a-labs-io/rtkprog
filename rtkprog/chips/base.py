# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass(frozen=True)
class ChipConfig:
    # Name of the Chip
    name: str

    # Probe response
    init_response: bytes

    # Firmware loader files (filenames only, resolved against the fw/ directory)
    loader_firmware_files: tuple[str, ...]

    # Flash memory map
    flash_start: int
    flash_end: int
    flash_page_size: int

    # MAC address location in flash
    flash_address_mac: int

    # eFuse register address, None if not supported
    efuse_register: int | None
    # Offset in eFuse response where the 2-byte CRC16 starts, None if not supported
    efuse_crc16_offset: int | None

    # Chip-specific parameter bytes for the start FW loader command
    fw_loader_params: bytes

    @property
    def flash_size(self) -> int:
        return self.flash_end - self.flash_start
