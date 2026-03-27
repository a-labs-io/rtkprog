# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

from argparse import ArgumentTypeError
from dataclasses import dataclass

from .bluetooth_mac import BluetoothMAC
from .chips import ChipConfig
from .exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class WriteRecord:
    address: int
    seek: int
    file: str


@dataclass(frozen=True, slots=True)
class ReadRecord:
    address: int
    size: int
    file: str


@dataclass(frozen=True, slots=True)
class EraseRegion:
    address: int
    size: int


@dataclass(frozen=True, slots=True)
class WritePlanEntry:
    address: int
    size: int
    label: str
    patch_mac: bool


def auto_int(value: str) -> int:
    """Accept integers in any base (decimal, 0x hex, 0o octal)."""
    return int(value, 0)


def mac_address(value: str) -> BluetoothMAC:
    """Parse a MAC address in XXXXXXXXXXXX or XX:XX:XX:XX:XX:XX format."""
    return BluetoothMAC.from_string(value)


def mac_or_auto(value: str) -> BluetoothMAC | str:
    """Parse a MAC address or the literal 'auto'."""
    if value.lower() == "auto":
        return "auto"
    return BluetoothMAC.from_string(value)


def write_record(value: str) -> WriteRecord:
    """Parse ADDRESS,SEEK,FILE into a WriteRecord."""
    try:
        parts = [p for p in value.split(",") if p]
        if len(parts) != 3:
            raise ValueError
        return WriteRecord(
            address=auto_int(parts[0]),
            seek=auto_int(parts[1]),
            file=parts[2],
        )
    except (ValueError, IndexError):
        raise ArgumentTypeError(
            f"'{value}' is not a valid write record — expected ADDRESS,SEEK,FILE"
        )


def read_record(value: str) -> ReadRecord:
    """Parse ADDRESS,SIZE,FILE into a ReadRecord."""
    try:
        parts = [p for p in value.split(",") if p]
        if len(parts) != 3:
            raise ValueError
        return ReadRecord(
            address=auto_int(parts[0]),
            size=auto_int(parts[1]),
            file=parts[2],
        )
    except (ValueError, IndexError):
        raise ArgumentTypeError(
            f"'{value}' is not a valid read record — expected ADDRESS,SIZE,FILE"
        )


def erase_region(value: str) -> EraseRegion:
    """Parse ADDRESS,SIZE into an EraseRegion."""
    try:
        parts = [p for p in value.split(",") if p]
        if len(parts) != 2:
            raise ValueError
        return EraseRegion(
            address=auto_int(parts[0]),
            size=auto_int(parts[1]),
        )
    except (ValueError, IndexError):
        raise ArgumentTypeError(
            f"'{value}' is not a valid erase region — expected ADDRESS,SIZE"
        )


def validate_write_plan(chip: ChipConfig, entries: list[WritePlanEntry]) -> None:
    """Validate WritePlanEntry entries before touching flash."""
    page_size = chip.flash_page_size

    for entry in entries:
        if entry.address % page_size != 0:
            raise ValidationError(
                f"{entry.label}: address 0x{entry.address:08x} is not page-aligned "
                f"(page size 0x{page_size:x})"
            )
        if entry.address < chip.flash_start:
            raise ValidationError(
                f"{entry.label}: address 0x{entry.address:08x} is below flash start "
                f"0x{chip.flash_start:08x}"
            )
        pages_needed = (entry.size + page_size - 1) // page_size
        end = entry.address + pages_needed * page_size
        if end > chip.flash_end:
            raise ValidationError(
                f"{entry.label}: end 0x{end:08x} exceeds flash end 0x{chip.flash_end:08x}"
            )

    for a, b in zip(
        sorted(entries, key=lambda e: e.address),
        sorted(entries, key=lambda e: e.address)[1:],
    ):
        if a.address + a.size > b.address:
            raise ValidationError(
                f"{a.label} (0x{a.address:08x}+0x{a.size:x}) overlaps "
                f"{b.label} (0x{b.address:08x})"
            )
