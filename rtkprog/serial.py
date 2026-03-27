# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import select
import sys
from time import sleep

from serial import Serial

_DEFAULT_BAUD: int = 115200

# Hardware timing constants (seconds)
_RESET_PIN_HOLD: float = 0.1
_BOOT_PIN_HOLD_PRE: float = 0.1
_BOOT_PIN_HOLD_POST: float = 0.4
_POST_RESET_DELAY: float = 0.2
_IDLE_BEFORE_RESET: float = 0.1


class SerialInterface:
    """Low-level serial transport: raw I/O and hardware reset/mode control."""

    def __init__(self, port: str) -> None:
        self._log = logging.getLogger("rtkprog.transport")
        self._serial = Serial(
            port,
            baudrate=_DEFAULT_BAUD,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2,
        )

    @property
    def serial(self) -> Serial:
        return self._serial

    def close(self) -> None:
        self._serial.close()

    def __enter__(self) -> "SerialInterface":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def transmit(self, data: bytes) -> None:
        self._serial.write(data)
        self._serial.flush()
        self._log.debug("TX: %s", data.hex())

    def receive(self, length: int) -> bytes:
        data = self._serial.read(length)
        self._log.debug("RX: %s", data.hex())
        return data

    def set_baud(self, baud: int) -> None:
        self._serial.baudrate = baud

    def reset_into_bootloader(self) -> None:
        """Reset the device and hold it in ROM bootloader mode."""
        self._log.debug("Resetting into bootloader mode")
        self._serial.baudrate = _DEFAULT_BAUD
        self._serial.dtr = False
        self._serial.rts = False
        sleep(_IDLE_BEFORE_RESET)
        self._serial.rts = False
        self._serial.dtr = True  # BOOT/LOG=LOW => bootloader mode
        sleep(_BOOT_PIN_HOLD_PRE)
        self._serial.rts = True  # RST=LOW => chip in reset
        sleep(_RESET_PIN_HOLD)
        self._serial.rts = False  # RST=HIGH => device boots into bootloader
        sleep(_BOOT_PIN_HOLD_POST)
        self._serial.dtr = False  # release BOOT/LOG
        sleep(_POST_RESET_DELAY)
        self._serial.reset_input_buffer()

    def reset_into_run(self, clear_input_buffer=False) -> None:
        """Reset the device and let it boot into its application firmware."""
        self._log.debug("Resetting into run application mode")
        self._serial.baudrate = _DEFAULT_BAUD
        self._serial.rts = False
        self._serial.dtr = False  # BOOT/LOG=HIGH => normal boot
        sleep(_BOOT_PIN_HOLD_PRE)
        self._serial.rts = True  # RST=LOW => chip in reset
        sleep(_RESET_PIN_HOLD)
        if clear_input_buffer:
            sleep(0.5)
            self._serial.reset_input_buffer()
        self._serial.rts = False  # RST=HIGH => device boots into application
        sleep(_POST_RESET_DELAY)

    def run_terminal(self):
        stdin_fd = sys.stdin.fileno()
        serial_fd = self._serial.fileno()
        try:
            while True:
                # Wait for data on either the serial port or stdin
                readable, _, _ = select.select([serial_fd, stdin_fd], [], [], 0.1)

                for fd in readable:
                    if fd == serial_fd:
                        # Data from serial port -> write to stdout
                        data = self._serial.read(self._serial.in_waiting or 1)
                        if data:
                            sys.stdout.buffer.write(data)
                            sys.stdout.buffer.flush()

                    elif fd == stdin_fd:
                        # Data from stdin -> write to serial port
                        data = os.read(stdin_fd, 4096)
                        if data:
                            self._serial.write(data)

        except (KeyboardInterrupt, OSError):
            pass
