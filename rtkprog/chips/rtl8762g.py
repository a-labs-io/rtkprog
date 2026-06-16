# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from .base import ChipConfig

RTL8762G = ChipConfig(
    name="RTL8762G",
    chip_id=0x29,
    magic_word=0xE9C568A6,
    loader_firmware_files=("RTL8762G_FW_B.bin", "flash_avl.bin"),
    flash_start=0x4001000,
    flash_end=0x4080000,
    flash_page_size=0x1000,
    flash_address_mac=0x400150B,
    efuse_register=0x0014F7BC,
    efuse_crc16_offset=9,
    fw_loader_trigger_addr=0x0013DB38,
    fw_loader_trigger_value=0x00147831,
)
