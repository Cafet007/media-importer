"""
Quick CLI to assign roles to connected drives.
Run: python3 assign_drives.py
"""

from backend.utils.detector import list_drives
from backend.utils.registry import DriveRegistry, DriveRole

ROLE_LABELS = {
    "1": ("Camera Card (import FROM)",  DriveRole.CAMERA_SOURCE),
    "2": ("Media Storage (import TO)",  DriveRole.MEDIA_DEST),
    "3": ("Ignore this drive",          DriveRole.IGNORED),
}


def main() -> None:
    registry = DriveRegistry()
    drives = list_drives()

    if not drives:
        print("No drives detected.")
        return

    print("\n=== Connected Drives ===\n")

    for i, drive in enumerate(drives, 1):
        role = registry.role_of(drive)
        known = f"[{role.value}]" if registry.is_known(drive) else "[NEW]"
        print(f"  {i}. {drive.label}  {known}")
        print(f"     Protocol   : {drive.protocol}")
        print(f"     Filesystem : {drive.filesystem}")
        print(f"     Capacity   : {drive.total_gb} GB  ({drive.free_gb} GB free)")
        print(f"     Serial     : {drive.serial_number or 'n/a'}")
        print(f"     Volume UUID: {drive.volume_uuid or 'n/a'}")
        print(f"     Has DCIM   : {drive.has_dcim}")
        print()

    print("Assign a role (or press Enter to skip):\n")

    for drive in drives:
        role = registry.role_of(drive)
        status = f"currently: {role.value}" if registry.is_known(drive) else "not yet assigned"
        print(f"Drive: {drive.label}  ({status})")
        for key, (label, _) in ROLE_LABELS.items():
            print(f"  {key}) {label}")
        print("  Enter) Skip")

        choice = input("  > ").strip()
        if choice in ROLE_LABELS:
            _, new_role = ROLE_LABELS[choice]
            registry.assign(drive, new_role)
            print(f"  Saved: {drive.label} → {new_role.value}\n")
        else:
            print("  Skipped.\n")

    print("\n=== Current assignments ===")
    print(f"  Camera sources : {[e['label'] for e in registry.camera_sources()]}")
    print(f"  Media destinations: {[e['label'] for e in registry.media_destinations()]}")
    print(f"\nSaved to: {registry._path}\n")


if __name__ == "__main__":
    main()
