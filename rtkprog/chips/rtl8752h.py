# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from .base import ChipConfig

RTL8752H = ChipConfig(
    name="RTL8752H",
    init_response=b"\x04\x0e\x08\x02\x61\xfc\x00\x01\x91\x20\x46",
    loader_firmware_files=("RTL8762H_FW_A.bin", "flash_avl.bin"),
    flash_start=0x00801000,
    flash_end=0x00880000,
    flash_page_size=0x1000,
    flash_address_mac=0x0080140B,
    efuse_register=None,
    efuse_crc16_offset=None,
    fw_loader_params=b"\xcc\x0a\x20\x00\x31\x48\x20\x00",
)
