"""
Camera profiles — defines where each camera brand stores photos, videos,
and other useful files on an SD card.

Used by the scanner to find all media regardless of folder structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CameraProfile:
    name: str
    # Glob patterns relative to SD card root to find media
    photo_paths: list[str]
    video_paths: list[str]
    extra_paths: list[str] = field(default_factory=list)  # thumbnails, telemetry, etc.
    # Folder name fragments that identify this camera brand
    dcim_markers: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Known camera profiles
# ---------------------------------------------------------------------------

PROFILES: list[CameraProfile] = [

    CameraProfile(
        name="Sony Alpha / ZV / RX",
        dcim_markers=["MSDCF", "SONY"],
        photo_paths=["DCIM/**/*"],
        video_paths=[
            "PRIVATE/M4ROOT/CLIP/*.MP4",   # XAVC S / XAVC HS (MP4)
            "PRIVATE/M4ROOT/CLIP/*.mp4",
            "AVCHD/BDMV/STREAM/*.MTS",     # AVCHD (older bodies)
            "AVCHD/BDMV/STREAM/*.mts",
        ],
        extra_paths=[
            "PRIVATE/M4ROOT/SUB/*.JPG",    # video proxy thumbnails
            "PRIVATE/M4ROOT/MEDIAPRO.XML", # media index
        ],
    ),

    CameraProfile(
        name="Canon EOS / PowerShot",
        dcim_markers=["CANON", "EOS"],
        photo_paths=["DCIM/**/*"],
        video_paths=["DCIM/**/*"],         # videos inside DCIM same as photos
        extra_paths=[
            "MISC/*.CTG",                  # catalog files
        ],
    ),

    CameraProfile(
        name="Nikon",
        dcim_markers=["NCD", "NIKON", "NKN"],
        photo_paths=["DCIM/**/*"],
        video_paths=["DCIM/**/*"],
        extra_paths=[
            "PRIVATE/NIKON/**/*",
        ],
    ),

    CameraProfile(
        name="Fujifilm",
        dcim_markers=["FUJI", "FJI"],
        photo_paths=["DCIM/**/*"],
        video_paths=["DCIM/**/*"],
    ),

    CameraProfile(
        name="GoPro",
        dcim_markers=["GOPRO", "GOPR"],
        photo_paths=["DCIM/**/*"],
        video_paths=["DCIM/**/*"],
        extra_paths=[
            "DCIM/**/*.LRV",               # low-res proxy videos
            "DCIM/**/*.THM",               # thumbnails
        ],
    ),

    CameraProfile(
        name="DJI Drone",
        dcim_markers=["DJI"],
        photo_paths=["DCIM/**/*"],
        video_paths=["DCIM/**/*"],
        extra_paths=[
            "DCIM/**/*.SRT",               # subtitle/telemetry files
            "DCIM/**/*.srt",
        ],
    ),

    CameraProfile(
        name="Generic / Unknown",
        dcim_markers=[],
        photo_paths=["DCIM/**/*"],
        video_paths=["DCIM/**/*"],
    ),
]


def detect_profile(sd_root: Path) -> CameraProfile:
    """
    Identify which camera created this SD card by inspecting DCIM subfolder names.
    Falls back to Generic if no match found.
    """
    dcim = sd_root / "DCIM"

    # Check for Sony-specific PRIVATE folder first (strong signal)
    if (sd_root / "PRIVATE" / "M4ROOT").exists():
        return _find("Sony Alpha / ZV / RX")

    if (sd_root / "AVCHD").exists():
        return _find("Sony Alpha / ZV / RX")

    if dcim.exists():
        subfolder_names = [p.name.upper() for p in dcim.iterdir() if p.is_dir()]
        for profile in PROFILES:
            for marker in profile.dcim_markers:
                if any(marker in name for name in subfolder_names):
                    return profile

    return _find("Generic / Unknown")


def _find(name: str) -> CameraProfile:
    return next((p for p in PROFILES if p.name == name), PROFILES[-1])


def all_search_roots(sd_root: Path, profile: CameraProfile) -> list[Path]:
    """
    Return all directories that should be scanned for this camera's files.
    Deduplicates — e.g. Canon has DCIM for both photos and videos.
    """
    roots: set[Path] = set()

    for pattern_list in (profile.photo_paths, profile.video_paths):
        for pattern in pattern_list:
            # Extract the top-level folder from the glob pattern
            top = pattern.split("/")[0]
            candidate = sd_root / top
            if candidate.exists():
                roots.add(candidate)

    return list(roots)
