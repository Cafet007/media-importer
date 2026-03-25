"""
Media Inspector — extracts file kind and capture date from any media file.

Focused on two things only:
  1. Kind  → PHOTO | RAW | VIDEO
  2. Date  → when the shot or video was captured

Fallback chain per type:
  RAW/Photo : exifread → Pillow EXIF → file modification time
  Video     : pymediainfo (encoded_date, tagged_date) → file modification time
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import MediaType, classify

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    path: Path
    kind: MediaType          # PHOTO | RAW | VIDEO | UNKNOWN
    captured_at: datetime | None
    date_source: str         # where the date came from: "exif" | "video_meta" | "file_mtime" | "none"

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def date_str(self) -> str:
        if self.captured_at:
            return self.captured_at.strftime("%Y-%m-%d %H:%M:%S")
        return "unknown"

    def __str__(self) -> str:
        return f"{self.name}  [{self.kind.value}]  {self.date_str}  (via {self.date_source})"


def inspect(path: str | Path) -> FileInfo:
    """
    Inspect a single file — return its kind and capture date.
    Never raises. Falls back to file modification time if metadata unavailable.
    """
    path = Path(path)
    kind = classify(path)

    captured_at, source = _get_date(path, kind)

    return FileInfo(path=path, kind=kind, captured_at=captured_at, date_source=source)


def inspect_all(paths: list[Path]) -> list[FileInfo]:
    """Inspect a list of files. Returns results in the same order."""
    return [inspect(p) for p in paths]


# ---------------------------------------------------------------------------
# Date extraction with fallbacks
# ---------------------------------------------------------------------------

def _get_date(path: Path, kind: MediaType) -> tuple[datetime | None, str]:
    """Return (datetime, source_label). Falls back through multiple strategies."""

    if kind in (MediaType.PHOTO, MediaType.RAW):
        # Strategy 1: exifread (best for RAW + JPEG)
        dt = _date_from_exifread(path)
        if dt:
            return dt, "exif"

        # Strategy 2: Pillow (JPEG fallback)
        dt = _date_from_pillow(path)
        if dt:
            return dt, "exif_pillow"

    elif kind == MediaType.VIDEO:
        # Strategy 1: pymediainfo container metadata
        dt = _date_from_pymediainfo(path)
        if dt:
            return dt, "video_meta"

    # Final fallback: file system modification time
    dt = _date_from_mtime(path)
    if dt:
        return dt, "file_mtime"

    return None, "none"


def _date_from_exifread(path: Path) -> datetime | None:
    try:
        import exifread
        with open(path, "rb") as fh:
            tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal", details=False)
        for tag in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
            val = tags.get(tag)
            if val:
                dt = _parse_exif_date(str(val))
                if dt:
                    return dt
    except Exception as e:
        logger.debug("exifread failed for %s: %s", path.name, e)
    return None


def _date_from_pillow(path: Path) -> datetime | None:
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        with Image.open(path) as img:
            raw = img._getexif()  # type: ignore[attr-defined]
        if not raw:
            return None
        exif = {TAGS.get(k, k): v for k, v in raw.items()}
        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            val = exif.get(key)
            if val:
                dt = _parse_exif_date(str(val))
                if dt:
                    return dt
    except Exception as e:
        logger.debug("Pillow failed for %s: %s", path.name, e)
    return None


def _date_from_pymediainfo(path: Path) -> datetime | None:
    try:
        from pymediainfo import MediaInfo
        info = MediaInfo.parse(path)
        for track in info.tracks:
            if track.track_type == "General":
                for attr in ("encoded_date", "tagged_date", "recorded_date"):
                    raw = getattr(track, attr, None)
                    if raw:
                        dt = _parse_video_date(str(raw))
                        if dt:
                            return dt
    except Exception as e:
        logger.debug("pymediainfo failed for %s: %s", path.name, e)
    return None


def _date_from_mtime(path: Path) -> datetime | None:
    try:
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Date parsers
# ---------------------------------------------------------------------------

def _parse_exif_date(value: str) -> datetime | None:
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d %H:%M:%S%z"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _parse_video_date(value: str) -> datetime | None:
    # Handles: "2026-03-16 10:18:09 UTC", "UTC 2024-03-15 10:30:00", "2024-03-15T10:30:00"
    value = value.replace("UTC", "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y:%m:%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None
