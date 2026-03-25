"""Tests for the safety guard."""

import pytest
from pathlib import Path
from backend.core.safety import (
    protect, unprotect, is_protected,
    guard_write, guard_delete, guard_same_path, guard_space,
    SafetyError, _protected_roots,
)


@pytest.fixture(autouse=True)
def clear_protected():
    """Reset protected paths between tests."""
    _protected_roots.clear()
    yield
    _protected_roots.clear()


def test_protect_blocks_write(tmp_path):
    protect(tmp_path)
    with pytest.raises(SafetyError, match="WRITE BLOCKED"):
        guard_write(tmp_path / "photo.arw")


def test_protect_blocks_nested_write(tmp_path):
    protect(tmp_path)
    with pytest.raises(SafetyError, match="WRITE BLOCKED"):
        guard_write(tmp_path / "DCIM" / "100MSDCF" / "photo.arw")


def test_unprotected_path_allows_write(tmp_path):
    # Should not raise
    guard_write(tmp_path / "output" / "photo.arw")


def test_delete_always_blocked(tmp_path):
    with pytest.raises(SafetyError, match="DELETE BLOCKED"):
        guard_delete(tmp_path / "photo.arw")


def test_delete_blocked_even_on_unprotected(tmp_path):
    # Deletion is NEVER allowed, regardless of protection
    with pytest.raises(SafetyError, match="DELETE BLOCKED"):
        guard_delete(tmp_path / "anything.jpg")


def test_same_path_blocked(tmp_path):
    f = tmp_path / "photo.arw"
    with pytest.raises(SafetyError, match="SOURCE == DESTINATION"):
        guard_same_path(f, f)


def test_different_paths_allowed(tmp_path):
    src = tmp_path / "src" / "photo.arw"
    dst = tmp_path / "dst" / "photo.arw"
    guard_same_path(src, dst)  # should not raise


def test_is_protected_true(tmp_path):
    protect(tmp_path)
    assert is_protected(tmp_path / "DCIM" / "file.arw")


def test_is_protected_false(tmp_path):
    other = tmp_path / "other"
    assert not is_protected(other / "file.arw")
