"""Tests for backend/utils/detector.py"""

from pathlib import Path
import pytest
from backend.utils.detector import DriveInfo, list_drives, find_camera_cards, DriveWatcher


def _make_drive(label="TestDrive", protocol="USB", filesystem="ExFAT",
                total=500_000_000_000, free=100_000_000_000,
                removable=True, has_dcim=False, volume_uuid=None):
    return DriveInfo(
        mount_point=Path(f"/Volumes/{label}"),
        label=label,
        protocol=protocol,
        filesystem=filesystem,
        total_bytes=total,
        free_bytes=free,
        is_removable=removable,
        has_dcim=has_dcim,
        volume_uuid=volume_uuid,
    )


def test_sd_card_detected_by_protocol():
    drive = _make_drive(protocol="Secure Digital", has_dcim=True)
    assert drive.is_camera_card is True
    assert drive.is_external_drive is False


def test_sd_card_via_dongle_detected_by_dcim():
    """SD card through USB dongle shows USB protocol — DCIM is the key signal."""
    drive = _make_drive(protocol="USB", has_dcim=True)
    assert drive.is_camera_card is True


def test_external_drive_no_dcim():
    drive = _make_drive(protocol="USB", has_dcim=False)
    assert drive.is_external_drive is True
    assert drive.is_camera_card is False


def test_thunderbolt_drive_is_external():
    drive = _make_drive(protocol="Thunderbolt", has_dcim=False)
    assert drive.is_external_drive is True


def test_internal_drive_excluded():
    drive = _make_drive(protocol="Apple Fabric", removable=False)
    assert drive.is_internal is True
    assert drive.is_camera_card is False
    assert drive.is_external_drive is False


def test_unique_id_prefers_volume_uuid():
    drive = _make_drive(volume_uuid="ABC-123")
    assert drive.unique_id == "ABC-123"


def test_unique_id_falls_back_to_mount_point():
    drive = _make_drive(label="Untitled")
    assert drive.unique_id == str(Path("/Volumes/Untitled"))


def test_drive_str_shows_kind():
    drive = _make_drive(protocol="USB", has_dcim=False)
    assert "External Drive" in str(drive)


def test_watcher_detects_insert(tmp_path):
    """Simulate a card inserted by patching _mount_points."""
    import time
    import backend.utils.detector as det

    original = det._mount_points
    inserted = []

    dcim = tmp_path / "DCIM"
    dcim.mkdir()

    det._mount_points = lambda: []
    watcher = DriveWatcher(on_insert=inserted.append, on_remove=None, poll_interval=0.1)
    watcher.start()

    det._mount_points = lambda: [tmp_path]
    time.sleep(0.5)
    watcher.stop()
    det._mount_points = original

    assert len(inserted) == 1
    assert inserted[0].mount_point == tmp_path


def test_watcher_detects_remove(tmp_path):
    """Simulate a card removed."""
    import time
    import backend.utils.detector as det

    original = det._mount_points
    removed = []

    dcim = tmp_path / "DCIM"
    dcim.mkdir()

    det._mount_points = lambda: [tmp_path]
    watcher = DriveWatcher(on_insert=lambda d: None, on_remove=removed.append, poll_interval=0.1)
    watcher.start()

    det._mount_points = lambda: []
    time.sleep(0.5)
    watcher.stop()
    det._mount_points = original

    assert len(removed) == 1
