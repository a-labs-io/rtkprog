# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0


class BluetoothMAC:
    MAC_ADDRESS_SIZE = 6

    def __init__(self, value):
        """
        Accepts:
        - bytes (length 6) in reverse byte order
        - string like 'AABBCCDDEEFF', 'AA:BB:CC:DD:EE:FF', or 'AA-BB-CC-DD-EE-FF'
        """
        if isinstance(value, (bytes, bytearray)):
            if len(value) != self.MAC_ADDRESS_SIZE:
                raise ValueError(
                    f"Binary MAC must be exactly {self.MAC_ADDRESS_SIZE} bytes"
                )
            # reverse byte order
            self._bytes = bytes(reversed(value))

        elif isinstance(value, str):
            cleaned = value.replace(":", "").replace("-", "").lower()
            if len(cleaned) != self.MAC_ADDRESS_SIZE * 2 or not all(
                c in "0123456789abcdef" for c in cleaned
            ):
                raise ValueError(f"Invalid MAC string: {value}")
            self._bytes = bytes.fromhex(cleaned)

        else:
            raise TypeError("Unsupported type for BluetoothMAC")

    @classmethod
    def from_reverse_bytes(cls, b: bytes):
        """Explicit constructor for reverse byte order input"""
        return cls(b)

    @classmethod
    def from_string(cls, s: str):
        """Explicit constructor for string input"""
        return cls(s)

    def to_bytes(self, reverse=False) -> bytes:
        """Return bytes, optionally reversed"""
        return bytes(reversed(self._bytes)) if reverse else self._bytes

    def __str__(self):
        """Colon-separated representation"""
        return ":".join(f"{b:02X}" for b in self._bytes)

    def __repr__(self):
        return f"BluetoothMAC('{str(self)}')"

    def __eq__(self, other):
        if isinstance(other, BluetoothMAC):
            return self._bytes == other._bytes
        return NotImplemented

    def __hash__(self):
        return hash(self._bytes)
