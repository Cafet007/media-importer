"""
Inspect kind + date for all media files on the SD card.
Run: python3 inspect_files.py
"""

from backend.utils.detector import list_drives
from backend.core.scanner import scan_card
from backend.core.inspector import inspect

def main() -> None:
    drives = [d for d in list_drives() if d.is_camera_card]
    if not drives:
        print("No SD card detected.")
        return

    drive = drives[0]
    print(f"\nSD Card: {drive.label}  ({drive.mount_point})\n")

    result = scan_card(drive.mount_point)

    # Inspect every file
    no_date = []
    by_kind: dict[str, list] = {}

    for mf in result.files:
        info = inspect(mf.path)
        by_kind.setdefault(info.kind.value, []).append(info)
        if not info.captured_at:
            no_date.append(info)

    # Summary per kind
    print(f"{'Kind':<8}  {'Count':>6}  {'Date source breakdown'}")
    print("-" * 50)
    for kind, infos in sorted(by_kind.items()):
        sources: dict[str, int] = {}
        for i in infos:
            sources[i.date_source] = sources.get(i.date_source, 0) + 1
        src_str = "  ".join(f"{s}:{n}" for s, n in sources.items())
        print(f"  {kind:<8}  {len(infos):>6}  {src_str}")

    print(f"\nTotal: {result.total} files")

    if no_date:
        print(f"\nFiles with no date ({len(no_date)}):")
        for info in no_date:
            print(f"  {info.name}")
    else:
        print("\nAll files have a date.")

    # Show sample — first 5 of each kind
    for kind, infos in sorted(by_kind.items()):
        print(f"\n--- {kind.upper()} samples ---")
        for info in infos[:5]:
            print(f"  {info}")

if __name__ == "__main__":
    main()
