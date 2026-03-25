"""
Logging setup for Media Porter.

Outputs:
  - File: ~/.media-mporter/logs/mporter.log  (rotating, 5 MB × 3 files)
  - Console: WARNING+ only (stays quiet during normal use)

Use in any module:
    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path


LOG_DIR  = Path.home() / ".media-mporter" / "logs"
LOG_FILE = LOG_DIR / "mporter.log"

FILE_FORMAT    = "%(asctime)s  %(levelname)-8s  %(name)s  —  %(message)s"
CONSOLE_FORMAT = "%(levelname)-8s  %(message)s"
DATE_FORMAT    = "%Y-%m-%d %H:%M:%S"


def setup(level: str = "DEBUG") -> None:
    """
    Call once at app startup (main.py).
    level: overall log level for the file handler ("DEBUG" | "INFO" | "WARNING")
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # Avoid duplicate handlers if setup() called more than once
    if root.handlers:
        return

    # ── File handler (rotating) ─────────────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, level.upper(), logging.DEBUG))
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))

    # ── Console handler (warnings only) ─────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger(__name__).info(
        "Logging started → %s  (level: %s)", LOG_FILE, level
    )


def get_log_path() -> Path:
    return LOG_FILE
