"""
Dedup Checker — determines if a file from the SD card already exists
on the external drive.

Two strategies (in order):
  1. Filename match  — fast, check if same filename exists in the destination folder
  2. Size match      — if filename differs, check size as a quick secondary signal

We deliberately avoid SHA256 hashing during the scan phase — hashing 600 RAW
files (each ~24 MB) takes significant time. Hash-based dedup is reserved for
the import phase to confirm before overwriting.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .models import MediaFile
from .rules import destination

logger = logging.getLogger(__name__)


class DedupChecker:
    """
    Checks whether files already exist on the destination drive.

    Usage:
        checker = DedupChecker(base=Path("/Volumes/External/Photography"))
        checker.build_index()   # scan existing files once

        for file in sd_files:
            if checker.exists(file):
                print(f"Already imported: {file.name}")
    """

    def __init__(self, base: Path) -> None:
        self.base = base
        # Maps filename → set of sizes (handles same name in multiple date folders)
        self._name_index: dict[str, set[int]] = {}
        self._indexed = False

    def build_index(self) -> int:
        """
        Scan the destination base folder and build a filename+size index.
        Returns the number of files indexed.
        """
        self._name_index.clear()
        count = 0

        if not self.base.exists():
            logger.info("Destination base does not exist yet: %s", self.base)
            self._indexed = True
            return 0

        for path in self.base.rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                size = path.stat().st_size
                self._name_index.setdefault(path.name.upper(), set()).add(size)
                count += 1

        self._indexed = True
        logger.info("Dedup index built: %d existing files in %s", count, self.base)
        return count

    def exists(self, file: MediaFile) -> bool:
        """
        Return True if this file appears to already be on the destination drive.
        Checks by filename + size match.
        """
        if not self._indexed:
            self.build_index()

        key = file.name.upper()
        if key not in self._name_index:
            return False

        # Filename matches — check size to reduce false positives
        return file.size_bytes in self._name_index[key]

    def filter_new(self, files: list[MediaFile]) -> tuple[list[MediaFile], list[MediaFile]]:
        """
        Split files into (new_files, already_imported).
        Builds index automatically on first call.
        """
        if not self._indexed:
            self.build_index()

        new, existing = [], []
        for f in files:
            if self.exists(f):
                existing.append(f)
            else:
                new.append(f)

        return new, existing
