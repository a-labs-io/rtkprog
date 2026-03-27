# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from .base import ChipConfig

RTL8762G = ChipConfig(
    name="RTL8762G",
    init_response=b"\x04\x0e\x08\x02\x61\xfc\x00\xa6\x68\xc5\xe9",
    loader_firmware_files=("RTL8762G_FW_B.bin", "flash_avl.bin"),
    flash_start=0x4001000,
    flash_end=0x4080000,
    flash_page_size=0x1000,
    flash_address_mac=0x400150B,
    efuse_register=0x0014F7BC,
    efuse_crc16_offset=9,
    fw_loader_params=b"\x38\xdb\x13\x00\x31\x78\x14\x00",
)
