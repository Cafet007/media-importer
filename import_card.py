"""
Import new files from SD card → external drive.
Run: python3 import_card.py
"""

from pathlib import Path
from backend.utils.detector import list_drives
from backend.core.scanner import scan_card
from backend.core.inspector import inspect_all
from backend.core.importer import run_import
from backend.core.rules import DestinationConfig

# ── Configure your destinations ─────────────────────────────────────────────
DEST_CONFIG = DestinationConfig(
    photo_base = Path("/Volumes/External/Photography"),
    video_base = Path("/Volumes/External/Footage"),
)
# ────────────────────────────────────────────────────────────────────────────


def main() -> None:
    # 1. Find SD card
    drives = [d for d in list_drives() if d.is_camera_card]
    if not drives:
        print("No SD card detected.")
        return

    drive = drives[0]
    print(f"\nSD Card : {drive.label}  ({drive.total_gb} GB, {drive.free_gb} GB free)")
    print(f"Photos  → {DEST_CONFIG.photo_base}")
    print(f"Videos  → {DEST_CONFIG.video_base}\n")

    # Create destination folders if they don't exist yet
    for p in (DEST_CONFIG.photo_base, DEST_CONFIG.video_base):
        if not p.exists():
            print(f"Creating: {p}")
            p.mkdir(parents=True, exist_ok=True)

    # 2. Scan
    print("Scanning SD card...")
    result = scan_card(drive.mount_point)
    print(f"Found   : {result.summary()}\n")

    # 3. Inspect (kind + date for all files)
    print("Reading metadata...")
    infos = inspect_all([f.path for f in result.files])

    # Patch captured_at back onto MediaFile objects
    info_map = {i.path: i for i in infos}
    for f in result.files:
        info = info_map.get(f.path)
        if info and info.captured_at:
            f.captured_at = info.captured_at

    # 4. Import
    print("Checking for new files...\n")

    def progress(done, total, name):
        pct = int(done / total * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"  [{bar}] {pct:3d}%  {name:<30}", end="\r")

    import_result = run_import(result.files, DEST_CONFIG, progress_cb=progress)
    print()  # clear progress line

    # 5. Report
    print(f"\n{'─'*50}")
    print(import_result.summary())
    print(f"{'─'*50}")

    if import_result.copied:
        print(f"\nCopied:")
        for file, dest in import_result.copied[:20]:
            # Show relative to the appropriate base
            base = DEST_CONFIG.video_base if "Footage" in str(dest) else DEST_CONFIG.photo_base
            try:
                rel = dest.relative_to(base.parent)
            except ValueError:
                rel = dest
            print(f"  {file.name:<30} → {rel}")
        if len(import_result.copied) > 20:
            print(f"  ... and {len(import_result.copied) - 20} more")

    if import_result.skipped:
        print(f"\nSkipped (already imported): {len(import_result.skipped)} files")

    if import_result.failed:
        print(f"\nFailed ({len(import_result.failed)}):")
        for file, err in import_result.failed:
            print(f"  {file.name}: {err}")


if __name__ == "__main__":
    main()
