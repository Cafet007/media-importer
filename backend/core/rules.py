"""
Rules Engine — maps a MediaFile to its destination path on the external drive.

Folder structure (Option B — separate roots):

  Photography/          ← photo_base
    RAW/   YYYY-MM-DD/  filename.ARW
    JPG/   YYYY-MM-DD/  filename.JPG

  Footage/              ← video_base
    YYYY-MM-DD/         filename.MP4

Date used: captured_at from EXIF/video metadata.
Fallback:  file modification time if no metadata date.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import MediaFile, MediaType


@dataclass
class DestinationConfig:
    photo_base: Path    # e.g. /Volumes/External/Photography
    video_base: Path    # e.g. /Volumes/External/Footage

    @classmethod
    def from_drive(cls, drive_root: Path) -> "DestinationConfig":
        """Convenience: build config from external drive root."""
        return cls(
            photo_base=drive_root / "Photography",
            video_base=drive_root / "Footage",
        )


def destination(file: MediaFile, config: DestinationConfig) -> Path:
    """
    Return the full destination path for a file.

    Examples:
      DSC05432.ARW  2026-03-16  → Photography/RAW/2026-03-16/DSC05432.ARW
      IMG_001.JPG   2026-03-22  → Photography/JPG/2026-03-22/IMG_001.JPG
      C0001.MP4     2026-03-24  → Footage/2026-03-24/C0001.MP4
    """
    date_folder = _date(file).strftime("%Y-%m-%d")

    if file.media_type == MediaType.VIDEO:
        return config.video_base / date_folder / file.name
    elif file.media_type == MediaType.RAW:
        return config.photo_base / "RAW" / date_folder / file.name
    elif file.media_type == MediaType.PHOTO:
        return config.photo_base / "JPG" / date_folder / file.name
    else:
        return config.photo_base / "OTHER" / date_folder / file.name


def _date(file: MediaFile) -> datetime:
    if file.captured_at:
        return file.captured_at
    return datetime.fromtimestamp(os.path.getmtime(file.path))
