# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from .base import ChipConfig

RTL8762C = ChipConfig(
    name="RTL8762C",
    init_response=b"\x04\x0e\x08\x02\x61\xfc\x00\xf2\xfe\x38\x68",
    loader_firmware_files=("RTL8762C_FW_B.bin", "flash_avl.bin"),
    flash_start=0x00801000,
    flash_end=0x00880000,
    flash_page_size=0x1000,
    flash_address_mac=0x00801409,
    efuse_register=0x002028C8,
    efuse_crc16_offset=8,
    fw_loader_params=b"\x34\x12\x20\x00\x31\x38\x20\x00",
)
