"""Tests for backend/core/rules.py — template engine and destination path resolution."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest

from backend.core.models import MediaFile, MediaType
from backend.core.rules import (
    DEFAULT_TEMPLATES,
    DestinationConfig,
    destination,
    preview_template,
    resolve_template,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_file(
    name: str,
    media_type: MediaType,
    captured_at: Optional[datetime] = None,
    camera_make: Optional[str] = None,
    camera_model: Optional[str] = None,
    size: int = 1024,
) -> MediaFile:
    f = MediaFile(path=Path(name), media_type=media_type, size=size)
    f.captured_at = captured_at or datetime(2026, 3, 24, 10, 18)
    f.camera_make = camera_make
    f.camera_model = camera_model
    return f


@pytest.fixture()
def config(tmp_path: Path) -> DestinationConfig:
    return DestinationConfig(
        photo_base=tmp_path / "Photography",
        video_base=tmp_path / "Footage",
    )


# ---------------------------------------------------------------------------
# resolve_template
# ---------------------------------------------------------------------------

def test_resolve_date_vars():
    f = _make_file("DSC001.ARW", MediaType.RAW, datetime(2026, 3, 24))
    result = resolve_template("{year}/{month}/{day}", f)
    assert result == "2026/03/24"


def test_resolve_month_name():
    f = _make_file("DSC001.ARW", MediaType.RAW, datetime(2026, 3, 24))
    assert resolve_template("{month_name}", f) == "March"


def test_resolve_date_full():
    f = _make_file("DSC001.ARW", MediaType.RAW, datetime(2026, 3, 24))
    assert resolve_template("{date}", f) == "2026-03-24"


def test_resolve_original_name_and_ext():
    f = _make_file("DSC06001.ARW", MediaType.RAW, datetime(2026, 3, 24))
    assert resolve_template("{original_name}.{ext}", f) == "DSC06001.arw"


def test_resolve_ext_lowercased():
    f = _make_file("C0001.MP4", MediaType.VIDEO, datetime(2026, 3, 24))
    assert resolve_template("{ext}", f) == "mp4"


def test_resolve_camera_make():
    f = _make_file("IMG.JPG", MediaType.PHOTO, camera_make="Sony")
    assert resolve_template("{camera_make}", f) == "Sony"


def test_resolve_camera_make_unknown_when_missing():
    f = _make_file("IMG.JPG", MediaType.PHOTO, camera_make=None)
    assert resolve_template("{camera_make}", f) == "Unknown"


def test_resolve_camera_make_spaces_replaced():
    f = _make_file("IMG.JPG", MediaType.PHOTO, camera_make="Canon Inc")
    assert resolve_template("{camera_make}", f) == "Canon-Inc"


def test_resolve_counter():
    f = _make_file("IMG.JPG", MediaType.PHOTO)
    assert resolve_template("{counter}", f, counter=7) == "007"
    assert resolve_template("{counter}", f, counter=42) == "042"


def test_resolve_media_type_labels():
    assert resolve_template("{media_type}", _make_file("a.JPG", MediaType.PHOTO))  == "Photos"
    assert resolve_template("{media_type}", _make_file("a.ARW", MediaType.RAW))    == "Raw"
    assert resolve_template("{media_type}", _make_file("a.MP4", MediaType.VIDEO))  == "Videos"


def test_resolve_unknown_variable_returns_filename():
    f = _make_file("IMG.JPG", MediaType.PHOTO)
    # Should not raise — falls back to filename
    result = resolve_template("{nonexistent}", f)
    assert result == "IMG.JPG"


# ---------------------------------------------------------------------------
# destination()
# ---------------------------------------------------------------------------

def test_destination_photo_default(config, tmp_path):
    f = _make_file("DSC001.JPG", MediaType.PHOTO, datetime(2026, 3, 24))
    dest = destination(f, config)
    assert dest == config.photo_base / "JPG" / "2026-03-24" / "DSC001.jpg"


def test_destination_raw_default(config, tmp_path):
    f = _make_file("DSC001.ARW", MediaType.RAW, datetime(2026, 3, 24))
    dest = destination(f, config)
    assert dest == config.photo_base / "RAW" / "2026-03-24" / "DSC001.arw"


def test_destination_video_default(config, tmp_path):
    f = _make_file("C0001.MP4", MediaType.VIDEO, datetime(2026, 3, 24))
    dest = destination(f, config)
    assert dest == config.video_base / "2026-03-24" / "C0001.mp4"


def test_destination_custom_template(config):
    config.templates["photo"] = "{year}/{month_name}/{original_name}.{ext}"
    f = _make_file("IMG001.JPG", MediaType.PHOTO, datetime(2026, 3, 24))
    dest = destination(f, config)
    assert dest == config.photo_base / "2026" / "March" / "IMG001.jpg"


def test_destination_video_uses_video_base(config):
    f = _make_file("C0001.MP4", MediaType.VIDEO, datetime(2026, 3, 24))
    dest = destination(f, config)
    assert str(dest).startswith(str(config.video_base))


def test_destination_photo_uses_photo_base(config):
    f = _make_file("DSC001.JPG", MediaType.PHOTO, datetime(2026, 3, 24))
    dest = destination(f, config)
    assert str(dest).startswith(str(config.photo_base))


# ---------------------------------------------------------------------------
# preview_template()
# ---------------------------------------------------------------------------

def test_preview_photo_returns_string():
    result = preview_template("JPG/{date}/{original_name}.{ext}", "photo")
    assert "2026" in result
    assert result.endswith(".jpg")


def test_preview_video_returns_string():
    result = preview_template("{date}/{original_name}.{ext}", "video")
    assert "2026" in result
    assert result.endswith(".mp4")


def test_preview_raw_returns_string():
    result = preview_template("RAW/{date}/{original_name}.{ext}", "raw")
    assert "RAW" in result
    assert result.endswith(".arw")


# ---------------------------------------------------------------------------
# DEFAULT_TEMPLATES
# ---------------------------------------------------------------------------

def test_default_templates_keys_present():
    assert "photo" in DEFAULT_TEMPLATES
    assert "raw"   in DEFAULT_TEMPLATES
    assert "video" in DEFAULT_TEMPLATES


def test_default_templates_are_strings():
    for key, val in DEFAULT_TEMPLATES.items():
        assert isinstance(val, str), f"template[{key!r}] should be str"
