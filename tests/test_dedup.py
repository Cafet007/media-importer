"""Tests for backend/core/dedup.py — filename+size index dedup checker."""

from datetime import datetime
from pathlib import Path

import pytest

from backend.core.dedup import DedupChecker
from backend.core.models import MediaFile, MediaType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_file(name: str, size: int = 1024, media_type: MediaType = MediaType.PHOTO) -> MediaFile:
    f = MediaFile(path=Path(name), media_type=media_type, size=size)
    f.captured_at = datetime(2026, 3, 24)
    return f


def _write_file(directory: Path, name: str, content: bytes = b"x") -> Path:
    p = directory / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

def test_build_index_empty_dir(tmp_path):
    checker = DedupChecker(tmp_path)
    count = checker.build_index()
    assert count == 0


def test_build_index_nonexistent_dir(tmp_path):
    checker = DedupChecker(tmp_path / "does_not_exist")
    count = checker.build_index()
    assert count == 0


def test_build_index_counts_files(tmp_path):
    _write_file(tmp_path, "JPG/2026-03-24/IMG001.JPG", b"a" * 100)
    _write_file(tmp_path, "JPG/2026-03-24/IMG002.JPG", b"b" * 200)
    _write_file(tmp_path, "RAW/2026-03-24/DSC001.ARW", b"c" * 300)

    checker = DedupChecker(tmp_path)
    count = checker.build_index()
    assert count == 3


def test_build_index_skips_hidden_files(tmp_path):
    _write_file(tmp_path, "JPG/2026-03-24/.DS_Store", b"system")
    _write_file(tmp_path, "JPG/2026-03-24/IMG001.JPG", b"a" * 100)

    checker = DedupChecker(tmp_path)
    count = checker.build_index()
    assert count == 1


# ---------------------------------------------------------------------------
# exists()
# ---------------------------------------------------------------------------

def test_exists_true_when_name_and_size_match(tmp_path):
    content = b"x" * 500
    _write_file(tmp_path, "JPG/2026-03-24/IMG001.JPG", content)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    f = _make_file("IMG001.JPG", size=len(content))
    assert checker.exists(f) is True


def test_exists_false_when_name_matches_but_size_differs(tmp_path):
    _write_file(tmp_path, "JPG/2026-03-24/IMG001.JPG", b"x" * 500)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    f = _make_file("IMG001.JPG", size=999)  # different size
    assert checker.exists(f) is False


def test_exists_false_when_name_not_in_index(tmp_path):
    _write_file(tmp_path, "JPG/2026-03-24/IMG001.JPG", b"x" * 100)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    f = _make_file("IMG999.JPG", size=100)
    assert checker.exists(f) is False


def test_exists_case_insensitive(tmp_path):
    content = b"x" * 200
    _write_file(tmp_path, "JPG/2026-03-24/img001.jpg", content)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    f = _make_file("IMG001.JPG", size=len(content))
    assert checker.exists(f) is True


def test_exists_auto_builds_index(tmp_path):
    content = b"x" * 100
    _write_file(tmp_path, "IMG001.JPG", content)

    checker = DedupChecker(tmp_path)
    # Don't call build_index — exists() should call it automatically
    f = _make_file("IMG001.JPG", size=len(content))
    assert checker.exists(f) is True


# ---------------------------------------------------------------------------
# filter_new()
# ---------------------------------------------------------------------------

def test_filter_new_splits_correctly(tmp_path):
    content_a = b"a" * 100
    content_b = b"b" * 200
    _write_file(tmp_path, "IMG001.JPG", content_a)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    existing_file = _make_file("IMG001.JPG", size=len(content_a))
    new_file      = _make_file("IMG002.JPG", size=len(content_b))

    new, existing = checker.filter_new([existing_file, new_file])
    assert new      == [new_file]
    assert existing == [existing_file]


def test_filter_new_all_new_when_dest_empty(tmp_path):
    checker = DedupChecker(tmp_path / "empty")
    checker.build_index()

    files = [_make_file(f"IMG00{i}.JPG", size=100) for i in range(5)]
    new, existing = checker.filter_new(files)

    assert len(new)      == 5
    assert len(existing) == 0


def test_filter_new_all_existing(tmp_path):
    files = [_make_file(f"IMG00{i}.JPG", size=100 * (i + 1)) for i in range(3)]
    for f in files:
        _write_file(tmp_path, f.name, b"x" * f.size)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    new, existing = checker.filter_new(files)
    assert len(new)      == 0
    assert len(existing) == 3


def test_filter_new_same_name_different_sizes_both_new(tmp_path):
    """Same filename in dest but different size → treat as new (not a match)."""
    _write_file(tmp_path, "IMG001.JPG", b"x" * 100)

    checker = DedupChecker(tmp_path)
    checker.build_index()

    f = _make_file("IMG001.JPG", size=999)  # different size
    new, existing = checker.filter_new([f])
    assert len(new) == 1
    assert len(existing) == 0
