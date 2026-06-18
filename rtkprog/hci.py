# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

import struct
from enum import IntEnum

from .exceptions import ProtocolError


class OpCode(IntEnum):
    VENDOR_READ = 0xFC61
    VENDOR_WRITE = 0xFC62
    READ_RTK_CHIP_ID = 0xFC6F
    READ_RTK_ROM_VERSION = 0xFC6D
    LOAD_FIRMWARE = 0xFC20


class RegType(IntEnum):
    NORMAL = 0x20
    AON = 0x03


class HciEventStatus(IntEnum):
    SUCCESS = 0x00
    IC_TYPE_ERR = 0x04


_COMMAND_PACKET_TYPE = 0x01
_EVENT_PACKET_TYPE = 0x04
_COMMAND_COMPLETE_EVENT_CODE = 0x0E

# HCI Command packet header:
# Packet_Type | OpCode | Parameter_Length
_COMMAND_HEADER = struct.Struct("<BHB")

# HCI Command complete event header:
# Packet_Type | Event_Code | Parameter_Length | Num_HCI_Cmd_Packets | OpCode | Status
_EVENT_HEADER = struct.Struct("<BBBBHB")

EVENT_PREFIX_LENGTH = 3


class HciCommand:
    """HCI Command packet
    Format: ``0x01 | OpCode | Parameter_Length | Parameters``.
    """

    def __init__(self, opcode: OpCode | int, params: bytes = b"") -> None:
        self.opcode = int(opcode)
        self.params = params

    def to_bytes(self) -> bytes:
        header = _COMMAND_HEADER.pack(_COMMAND_PACKET_TYPE, self.opcode, len(self.params))
        return header + self.params

    def __bytes__(self) -> bytes:
        return self.to_bytes()


class CommandCompleteEvent:
    def __init__(
        self, opcode: int, status: int, return_params: bytes, raw: bytes
    ) -> None:
        self.opcode = opcode
        self.status = status
        self.return_params = return_params
        self.raw = raw

    @classmethod
    def parse(cls, data: bytes) -> "CommandCompleteEvent":
        if len(data) < _EVENT_HEADER.size:
            raise ProtocolError(f"Truncated Command Complete event: {data.hex()}")
        packet_type, event_code, _len, _num_cmd_packets, opcode, status = (
            _EVENT_HEADER.unpack_from(data)
        )
        if packet_type != _EVENT_PACKET_TYPE:
            raise ProtocolError(f"Not an HCI event packet: {data.hex()}")
        if event_code != _COMMAND_COMPLETE_EVENT_CODE:
            raise ProtocolError(f"Not a CommandComplete event: {data.hex()}")
        return cls(
            opcode=opcode,
            status=status,
            return_params=data[_EVENT_HEADER.size :],
            raw=bytes(data),
        )

    def check(self, opcode: OpCode | int) -> "CommandCompleteEvent":
        if self.opcode != int(opcode):
            raise ProtocolError(
                f"Unexpected OpCode 0x{self.opcode:04X} (expected 0x{int(opcode):04X})"
            )
        if self.status != HciEventStatus.SUCCESS:
            raise ProtocolError(
                f"Command 0x{self.opcode:04X} failed with status 0x{self.status:02X}"
            )
        return self
