# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from .base import ChipConfig
from .rtl8752h import RTL8752H
from .rtl8762c import RTL8762C
from .rtl8762g import RTL8762G

CHIP_REGISTRY: dict[bytes, ChipConfig] = {
    RTL8762C.init_response: RTL8762C,
    RTL8762G.init_response: RTL8762G,
    RTL8752H.init_response: RTL8752H,
}

__all__ = ["ChipConfig", "CHIP_REGISTRY", "RTL8762C", "RTL8762G", "RTL8752H"]
