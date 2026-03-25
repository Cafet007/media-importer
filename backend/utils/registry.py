"""
Drive Registry — persists user-assigned roles for drives, keyed by serial number.

Roles:
  CAMERA_SOURCE    — SD card / camera storage to import FROM
  MEDIA_DEST       — External hard drive to import TO
  IGNORED          — User explicitly dismissed this drive

Storage: ~/.media-mporter/drives.json
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .detector import DriveInfo

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path.home() / ".media-mporter" / "drives.json"


class DriveRole(str, Enum):
    CAMERA_SOURCE = "camera_source"   # import FROM this drive
    MEDIA_DEST    = "media_dest"      # import TO this drive
    IGNORED       = "ignored"         # user dismissed, don't ask again
    UNASSIGNED    = "unassigned"      # never seen before


class DriveRegistry:
    """
    Persists drive role assignments keyed by unique_id (serial number or volume UUID).

    Usage:
        registry = DriveRegistry()

        # Assign a role
        registry.assign(drive, DriveRole.CAMERA_SOURCE)

        # Look up a role
        role = registry.role_of(drive)

        # Get all known camera sources
        sources = registry.all_of_role(DriveRole.CAMERA_SOURCE)
    """

    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self._path = path
        self._data: dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def role_of(self, drive: DriveInfo) -> DriveRole:
        """Return the assigned role for a drive, or UNASSIGNED if never seen."""
        entry = self._data.get(drive.unique_id)
        if not entry:
            return DriveRole.UNASSIGNED
        try:
            return DriveRole(entry["role"])
        except (KeyError, ValueError):
            return DriveRole.UNASSIGNED

    def assign(self, drive: DriveInfo, role: DriveRole) -> None:
        """Assign a role to a drive and persist it."""
        self._data[drive.unique_id] = {
            "role":          role.value,
            "label":         drive.label,
            "serial_number": drive.serial_number,
            "volume_uuid":   drive.volume_uuid,
            "protocol":      drive.protocol,
            "filesystem":    drive.filesystem,
            "total_gb":      drive.total_gb,
        }
        self._save()
        logger.info("Assigned %s → %s", drive.label, role.value)

    def unassign(self, drive: DriveInfo) -> None:
        """Remove a drive's assignment (forget it)."""
        self._data.pop(drive.unique_id, None)
        self._save()

    def is_known(self, drive: DriveInfo) -> bool:
        return drive.unique_id in self._data

    def all_of_role(self, role: DriveRole) -> list[dict]:
        """Return all stored entries with the given role."""
        return [v for v in self._data.values() if v.get("role") == role.value]

    def camera_sources(self) -> list[dict]:
        return self.all_of_role(DriveRole.CAMERA_SOURCE)

    def media_destinations(self) -> list[dict]:
        return self.all_of_role(DriveRole.MEDIA_DEST)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
                logger.debug("Loaded drive registry (%d entries)", len(self._data))
            except Exception as exc:
                logger.warning("Could not load drive registry: %s", exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))
        logger.debug("Saved drive registry (%d entries)", len(self._data))
