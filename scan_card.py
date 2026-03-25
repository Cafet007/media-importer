"""
Scan the connected camera SD card and list all media files found.
Run: python3 scan_card.py
"""

from backend.utils.detector import list_drives
from backend.utils.registry import DriveRegistry, DriveRole
from backend.core.scanner import scan_card
from backend.core.metadata import extract_all


def main() -> None:
    registry = DriveRegistry()
    drives = list_drives()

    # Find camera cards — either assigned by user or auto-detected via DCIM
    camera_drives = [
        d for d in drives
        if registry.role_of(d) == DriveRole.CAMERA_SOURCE or d.is_camera_card
    ]

    if not camera_drives:
        print("No camera SD card detected. Plug in your SD card and try again.")
        return

    for drive in camera_drives:
        print(f"\n{'='*60}")
        print(f"SD Card : {drive.label}")
        print(f"Protocol: {drive.protocol}")
        print(f"Size    : {drive.total_gb} GB ({drive.free_gb} GB free)")
        print(f"Serial  : {drive.serial_number or 'n/a'}")
        print(f"UUID    : {drive.volume_uuid or 'n/a'}")
        print(f"{'='*60}")

        print("\nDetecting camera profile and scanning all media folders...")

        def progress(done, total, path):
            if total > 0:
                pct = int(done / total * 100)
                print(f"  [{pct:3d}%] {path.name}", end="\r")

        result = scan_card(drive.mount_point, progress_cb=progress)
        print()  # clear progress line

        print(f"\nCamera  : {result.profile.name if result.profile else 'Unknown'}")
        print(f"Found: {result.summary()}")
        print(f"  Photos : {len(result.photos)}")
        print(f"  RAW    : {len(result.raws)}")
        print(f"  Videos : {len(result.videos)}")

        if result.total == 0:
            continue

        print("\nExtracting metadata...")
        extract_all(result.files)

        # Group by date
        by_date: dict[str, list] = {}
        for f in result.files:
            date_key = f.captured_at.strftime("%Y-%m-%d") if f.captured_at else "Unknown date"
            by_date.setdefault(date_key, []).append(f)

        print(f"\nFiles by date ({len(by_date)} days):\n")
        for date in sorted(by_date):
            files = by_date[date]
            photos = [f for f in files if f.media_type.value == "photo"]
            raws   = [f for f in files if f.media_type.value == "raw"]
            videos = [f for f in files if f.media_type.value == "video"]
            print(f"  {date}  —  {len(files)} files  "
                  f"({len(photos)} photos, {len(raws)} RAW, {len(videos)} videos)")

        print("\nAll files:\n")
        for f in result.files:
            date_str = f.captured_at.strftime("%Y-%m-%d %H:%M") if f.captured_at else "no date"
            cam  = f.camera_model or "unknown camera"
            size = f"{f.size_mb:.1f} MB"
            print(f"  {f.name:<30} {date_str}  {cam:<20} {size:>8}")


if __name__ == "__main__":
    main()
