"""Tests for backend/core/scanner.py"""

import tempfile
from pathlib import Path

import pytest

from backend.core.models import MediaType
from backend.core.scanner import ScanResult, scan


@pytest.fixture()
def fake_sd(tmp_path: Path) -> Path:
    """Create a fake SD card DCIM structure."""
    dcim = tmp_path / "DCIM" / "100CANON"
    dcim.mkdir(parents=True)

    (dcim / "IMG_0001.JPG").write_bytes(b"fake-jpeg")
    (dcim / "IMG_0002.CR3").write_bytes(b"fake-raw")
    (dcim / "MVI_0003.MP4").write_bytes(b"fake-video")
    (dcim / ".DS_Store").write_bytes(b"system")
    (dcim / "THUMB.THM").write_bytes(b"thumbnail")

    return tmp_path


def test_scan_counts(fake_sd: Path) -> None:
    result = scan(fake_sd)
    assert result.total == 3
    assert len(result.photos) == 1
    assert len(result.raws) == 1
    assert len(result.videos) == 1


def test_scan_skips_system_files(fake_sd: Path) -> None:
    result = scan(fake_sd)
    names = [f.name for f in result.files]
    assert ".DS_Store" not in names
    assert "THUMB.THM" not in names


def test_scan_summary(fake_sd: Path) -> None:
    result = scan(fake_sd)
    summary = result.summary()
    assert "3 files" in summary
    assert "1 photos" in summary
    assert "1 RAW" in summary
    assert "1 videos" in summary


def test_scan_progress_callback(fake_sd: Path) -> None:
    calls: list[tuple[int, int]] = []

    def cb(done: int, total: int, path: Path) -> None:
        calls.append((done, total))

    scan(fake_sd, progress_cb=cb)
    assert len(calls) > 0


def test_scan_nonexistent_raises() -> None:
    with pytest.raises(FileNotFoundError):
        scan("/nonexistent/path")


def test_scan_file_not_dir_raises(tmp_path: Path) -> None:
    f = tmp_path / "file.jpg"
    f.write_bytes(b"x")
    with pytest.raises(NotADirectoryError):
        scan(f)
