# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0


class RTKError(Exception):
    """Base exception for all rtkprog errors."""


class ProtocolError(RTKError):
    """Raised when a device response does not match the expected protocol bytes."""


class CRCError(RTKError):
    """Raised when a CRC check on a received payload fails."""


class ValidationError(RTKError):
    """Raised when a write plan fails pre-flight validation."""


class UnknownChipError(RTKError):
    """Raised when the device init response does not match any known chip."""


class UnsupportedOperationError(RTKError):
    """Raised when an operation is not supported by the detected chip."""
