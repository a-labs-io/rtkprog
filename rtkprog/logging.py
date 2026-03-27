# SPDX-FileCopyrightText: 2026 A Labs GmbH
# SPDX-License-Identifier: Apache-2.0

import logging


def configure_logging(verbose: int, quiet: bool) -> logging.Logger:
    logger = logging.getLogger("rtkprog")

    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
