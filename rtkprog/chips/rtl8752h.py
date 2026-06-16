# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from .base import ChipConfig

RTL8752H = ChipConfig(
    name="RTL8752H",
    chip_id=0x1F,
    magic_word=0x46209101,
    loader_firmware_files=("RTL8762H_FW_A.bin", "flash_avl.bin"),
    flash_start=0x00801000,
    flash_end=0x00880000,
    flash_page_size=0x1000,
    flash_address_mac=0x0080140B,
    efuse_register=None,
    efuse_crc16_offset=None,
    fw_loader_trigger_addr=0x00200ACC,
    fw_loader_trigger_value=0x00204831,
)
