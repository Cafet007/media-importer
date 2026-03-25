"""
Rules Engine — maps a MediaFile to its destination path on the external drive.

Supports user-configurable template strings with variables:
  {year}, {month}, {month_name}, {day}, {date},
  {camera_make}, {camera_model}, {ext}, {original_name}, {counter}, {media_type}

Templates are relative to photo_base (for photos/raw) or video_base (for video).

Default layout (matches original hardcoded Option B):
  photo  → JPG/{date}/{original_name}.{ext}       → Photography/JPG/2026-03-24/DSC05432.JPG
  raw    → RAW/{date}/{original_name}.{ext}        → Photography/RAW/2026-03-24/DSC05432.ARW
  video  → {date}/{original_name}.{ext}            → Footage/2026-03-24/C0001.MP4
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import MediaFile, MediaType

logger = logging.getLogger(__name__)

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Default templates — relative to photo_base / video_base
DEFAULT_TEMPLATES = {
    "photo": "JPG/{date}/{original_name}.{ext}",
    "raw":   "RAW/{date}/{original_name}.{ext}",
    "video": "{date}/{original_name}.{ext}",
}

# Reference card shown in the rules editor
TEMPLATE_VARIABLES = [
    ("{year}",         "2026",         "4-digit year"),
    ("{month}",        "03",           "2-digit month"),
    ("{month_name}",   "March",        "Full month name"),
    ("{day}",          "24",           "2-digit day"),
    ("{date}",         "2026-03-24",   "Full date YYYY-MM-DD"),
    ("{camera_make}",  "Sony",         "Camera brand"),
    ("{camera_model}", "ILCE-6300",    "Camera model"),
    ("{ext}",          "arw",          "Lowercase file extension"),
    ("{original_name}","DSC06001",     "Original filename stem"),
    ("{counter}",      "001",          "Auto-increment counter"),
    ("{media_type}",   "Raw",          "Photos / Videos / Raw"),
]


@dataclass
class DestinationConfig:
    photo_base: Path    # e.g. /Volumes/External/Photography
    video_base: Path    # e.g. /Volumes/External/Footage
    templates: dict = field(default_factory=lambda: dict(DEFAULT_TEMPLATES))

    @classmethod
    def from_drive(cls, drive_root: Path) -> "DestinationConfig":
        return cls(
            photo_base=drive_root / "Photography",
            video_base=drive_root / "Footage",
        )


def resolve_template(template: str, file: MediaFile, counter: int = 1) -> str:
    """Resolve a template string using a MediaFile's metadata."""
    date = _date(file)
    variables = {
        "year":          date.strftime("%Y"),
        "month":         date.strftime("%m"),
        "month_name":    _MONTH_NAMES[date.month - 1],
        "day":           date.strftime("%d"),
        "date":          date.strftime("%Y-%m-%d"),
        "camera_make":   (file.camera_make  or "Unknown").replace(" ", "-"),
        "camera_model":  (file.camera_model or "Unknown").replace(" ", "-"),
        "ext":           file.path.suffix.lstrip(".").lower(),
        "original_name": file.path.stem,
        "counter":       f"{counter:03d}",
        "media_type":    _media_label(file),
    }
    try:
        return template.format(**variables)
    except KeyError as e:
        logger.warning("Unknown template variable %s in %r — using original filename", e, template)
        return file.name


def destination(file: MediaFile, config: DestinationConfig, counter: int = 1) -> Path:
    """Return the full destination path for a file using the configured template."""
    key = _template_key(file)
    template = config.templates.get(key, DEFAULT_TEMPLATES.get(key, "{date}/{original_name}.{ext}"))
    rel = resolve_template(template, file, counter)
    base = config.video_base if file.media_type == MediaType.VIDEO else config.photo_base
    return base / rel


def preview_template(template: str, key: str = "photo") -> str:
    """
    Return an example resolved path string for live preview in the rules editor.
    Uses fake sample metadata so no real files are needed.
    """
    class _Sample:
        camera_make  = "Sony"
        camera_model = "ILCE-6300"
        captured_at  = datetime(2026, 3, 24, 10, 18)

    if key == "video":
        _Sample.path = Path("C0001.MP4")
        _Sample.media_type = MediaType.VIDEO
    elif key == "raw":
        _Sample.path = Path("DSC06001.ARW")
        _Sample.media_type = MediaType.RAW
    else:
        _Sample.path = Path("DSC06001.JPG")
        _Sample.media_type = MediaType.PHOTO

    return resolve_template(template, _Sample(), counter=1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _template_key(file: MediaFile) -> str:
    if file.media_type == MediaType.VIDEO:
        return "video"
    if file.media_type == MediaType.RAW:
        return "raw"
    return "photo"


def _media_label(file: MediaFile) -> str:
    if file.media_type == MediaType.VIDEO:
        return "Videos"
    if file.media_type == MediaType.RAW:
        return "Raw"
    return "Photos"


def _date(file: MediaFile) -> datetime:
    if file.captured_at:
        return file.captured_at
    return datetime.fromtimestamp(os.path.getmtime(file.path))
