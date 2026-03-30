# Media Porter — Project Plan

## Vision
A cross-platform desktop app (Mac + Windows) that imports media from camera SD cards
into a user-defined folder structure on an external hard drive. Built for photographers
and videographers who want automatic, rule-based organization of their footage.

---

## Tech Stack

| Layer        | Technology                        | Status      |
|--------------|-----------------------------------|-------------|
| Language     | Python 3.11+                      | ✅ Done      |
| GUI          | PySide6 (Qt6)                     | ✅ Done      |
| File ops     | `pathlib`, `shutil`               | ✅ Done      |
| Photo meta   | `Pillow`, `exifread`              | ✅ Done      |
| Video meta   | `pymediainfo`                     | ✅ Done      |
| Dedup        | filename + size (fast scan dedup) | ✅ Done      |
| Dedup        | `hashlib` SHA256 (post-copy verify)| ⬜ Planned  |
| Database     | SQLite + SQLAlchemy               | ⬜ Planned   |
| SD detection | polling (DriveWatcher)            | ✅ Done      |
| Packaging    | PyInstaller (`.app` / `.exe`)     | ⬜ Planned   |
| Config       | TOML (`tomllib` / `tomli-w`)      | ⬜ Planned   |

---

## Project Structure

```
media-porter/
├── backend/
│   ├── core/
│   │   ├── scanner.py          ✅ scan SD card, camera profile detection
│   │   ├── camera_profiles.py  ✅ Sony/Canon/Nikon/Fuji/GoPro/DJI profiles
│   │   ├── metadata.py         ✅ EXIF / video metadata extraction
│   │   ├── inspector.py        ✅ kind + capture date with fallback chain
│   │   ├── models.py           ✅ MediaFile, MediaType, classify()
│   │   ├── rules.py            ✅ destination path engine (Option B layout)
│   │   ├── importer.py         ✅ chunked copy, progress, cancel support
│   │   ├── dedup.py            ✅ filename+size index, filter_new()
│   │   └── safety.py           ✅ protected paths, atomic copy, space guard
│   ├── db/
│   │   ├── models.py           ⬜ SQLAlchemy ORM models
│   │   └── repository.py       ⬜ import history CRUD
│   └── utils/
│       ├── detector.py         ✅ DriveInfo, list_drives(), DriveWatcher
│       ├── registry.py         ✅ DriveRegistry persisted to drives.json
│       ├── log_setup.py        ✅ rotating file log + console handler
│       └── config.py           ⬜ load/save user settings (TOML)
├── gui/
│   ├── main_window.py          ✅ main window, scan/import workers, cancel
│   └── widgets/
│       ├── source_panel.py     ✅ two-section panel (Camera Cards / Storage Drives)
│       ├── dest_panel.py       ✅ destination path picker, auto-fill from drive
│       ├── file_table.py       ✅ 5-col table, in-progress/copied/failed status
│       ├── rules_editor.py     ⬜ visual rule template editor
│       └── settings_panel.py   ⬜ preferences, folder naming, config
├── tests/
│   ├── test_scanner.py         ✅
│   ├── test_safety.py          ✅
│   ├── test_detector.py        ✅
│   ├── test_rules.py           ⬜
│   ├── test_dedup.py           ⬜
│   └── test_importer.py        ⬜
├── main.py                     ✅ entry point, dark palette, logging setup
├── pyproject.toml
├── requirements.txt
└── PLAN.md
```

---

## Data Flow

```
SD Card (DCIM/ + PRIVATE/M4ROOT/CLIP/)
    └─► Scanner + CameraProfiles  → MediaFile list (path, size, type)
            └─► Inspector         → enriched with capture date (EXIF / video meta / mtime)
                    └─► DedupChecker  → filter_new() via filename+size index
                            └─► Rule Engine   → compute destination path
                                    └─► safe_copy()   → atomic temp→rename, chunked progress
                                            └─► DB (planned) → record import history
```

---

## Folder Naming Rule Engine

User configures templates per file type. Variables resolved from EXIF/video metadata.

### Available variables
| Variable         | Example            | Source                |
|------------------|--------------------|-----------------------|
| `{year}`         | `2026`             | EXIF DateTimeOriginal |
| `{month}`        | `03`               | EXIF                  |
| `{month_name}`   | `March`            | EXIF                  |
| `{day}`          | `15`               | EXIF                  |
| `{date}`         | `2026-03-15`       | EXIF                  |
| `{camera_make}`  | `Sony`             | EXIF Make             |
| `{camera_model}` | `ILCE-6300`        | EXIF Model            |
| `{ext}`          | `arw`              | file extension        |
| `{original_name}`| `DSC06001`         | source filename stem  |
| `{counter}`      | `001`              | auto-increment        |
| `{media_type}`   | `Photos/Videos/Raw`| file type             |

### Default rule templates
```toml
[rules]
photo = "Photos/{year}/{month}-{month_name}/{date}_{counter}.{ext}"
video = "Videos/{year}/{month}-{month_name}/{date}_{counter}.{ext}"
raw   = "Raw/{year}/{month}-{month_name}/{original_name}.{ext}"
```

### Current hardcoded layout (Option B — implemented)
```
Photography/
  RAW/   YYYY-MM-DD/   DSC06001.ARW
  JPG/   YYYY-MM-DD/   DSC06001.JPG

Footage/
  YYYY-MM-DD/          C0001.MP4
```
> Template engine will replace hardcoded layout in a future phase.

### Example output (template engine)
```
External HDD/
├── Photos/
│   └── 2026/
│       └── 03-March/
│           ├── 2026-03-15_001.jpg
│           └── 2026-03-15_002.jpg
├── Videos/
│   └── 2026/
│       └── 03-March/
│           └── 2026-03-15_001.mp4
└── Raw/
    └── 2026/
        └── 03-March/
            └── DSC06001.arw
```

---

## Database Schema

```sql
-- import history
CREATE TABLE imports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash    TEXT NOT NULL UNIQUE,   -- SHA256 of file content
    source_path  TEXT NOT NULL,
    dest_path    TEXT NOT NULL,
    file_size    INTEGER,
    media_type   TEXT,                  -- photo | video | raw
    camera_make  TEXT,
    camera_model TEXT,
    captured_at  DATETIME,
    imported_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- import sessions
CREATE TABLE sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_root  TEXT NOT NULL,
    dest_root    TEXT NOT NULL,
    total_files  INTEGER,
    imported     INTEGER,
    skipped      INTEGER,
    errors       INTEGER,
    started_at   DATETIME,
    finished_at  DATETIME
);
```

---

## Safety System (implemented)

| Rule | Implementation |
|---|---|
| Never write to SD card | Protected path registry, `guard_write()` |
| Never delete | `guard_delete()` always raises — unconditional |
| Never overwrite | Existence check before copy |
| Space check per file | `guard_space()` before each copy |
| Space check full batch | `check_batch_space()` before import starts, groups by device |
| Atomic copy | Write to `.mporter_tmp_` → rename on success |
| Temp cleanup | `finally` block deletes temp on failure |
| Block scanning dest drive | `_is_dest_drive()` check in GUI before scan |

---

## Build Phases

### Phase 1 — Core Engine ✅ Complete
- [x] `scanner.py` — walk DCIM + Sony PRIVATE/M4ROOT/CLIP/, classify files
- [x] `camera_profiles.py` — per-brand folder structure profiles
- [x] `metadata.py` — EXIF from JPG/RAW, metadata from MP4
- [x] `inspector.py` — kind + date with fallback chain
- [x] `models.py` — MediaFile, MediaType, classify()
- [x] `rules.py` — destination path engine (Option B layout)
- [x] `importer.py` — chunked copy, progress callback, cancel support
- [x] `dedup.py` — filename+size index, filter_new()
- [x] `safety.py` — full safety guard suite + batch space check
- [x] CLI scripts: `scan_card.py`, `import_card.py`, `inspect_files.py`

### Phase 2 — Drive Detection + Logging ✅ Complete
- [x] `detector.py` — DriveInfo, list_drives(), find_camera_cards(), DriveWatcher
- [x] `registry.py` — DriveRegistry persisted to drives.json
- [x] `log_setup.py` — RotatingFileHandler (5MB×3) + console WARNING+
- [x] Logging wired throughout all backend + GUI modules

### Phase 3 — GUI ✅ Complete (base)
- [x] `main_window.py` — dark Fusion theme, scan/import workers, cancel button
- [x] `source_panel.py` — two sections: Camera Cards / Storage Drives
- [x] `dest_panel.py` — path pickers, auto-fill from selected drive
- [x] `file_table.py` — file list, New/In Progress/Copied/Failed status, auto-scroll
- [x] Pre-import space check with blocking error dialog
- [x] Within-file progress bar (chunked, updates every 4 MB)
- [x] Import button re-evaluation after dest config changes

### Phase 4 — Config + Database ⬜ Next
- [ ] `config.py` — save/load TOML to `~/.media-porter/config.toml`
  - Persist destination paths across launches
  - Store last selected drive UUIDs
  - Store folder naming rules
- [ ] `db/models.py` + `db/repository.py` — SQLAlchemy import history
  - Replace filename+size dedup with SHA256 hash dedup via DB
  - Record every imported file with source, dest, date, camera
- [ ] Post-copy SHA256 verification — confirm copied file matches source
- [ ] Import history viewer panel in GUI

### Phase 5 — Rules Editor + Settings ⬜ Planned
- [ ] `config.py` rule template parser — resolve `{year}`, `{month_name}` etc.
- [ ] Replace hardcoded `rules.py` layout with template engine
- [ ] `settings_panel.py` — folder naming prefs, default paths, chunk size
- [ ] `rules_editor.py` — visual template editor with live path preview
- [ ] Conflict resolution UI — show files that hit DESTINATION EXISTS

### Phase 6 — Polish + Packaging ⬜ Planned
- [ ] App icon (`.icns` for Mac, `.ico` for Windows)
- [ ] PyInstaller spec for Mac `.app` bundle
- [ ] `create-dmg` script for distributable `.dmg`
- [ ] PyInstaller spec for Windows `.exe`
- [ ] Windows drive detection testing + fixes
- [ ] Error log panel + retry failed imports
- [ ] Thumbnail preview before import

---

## Supported File Types

| Category | Extensions                                          |
|----------|-----------------------------------------------------|
| Photo    | `.jpg`, `.jpeg`, `.heic`, `.png`, `.tif`, `.tiff`  |
| Raw      | `.cr2`, `.cr3`, `.nef`, `.arw`, `.dng`, `.raf`, `.rw2` |
| Video    | `.mp4`, `.mov`, `.mts`, `.m2ts`, `.avi`, `.mkv`    |

---

## Key Design Decisions

1. **Non-destructive** — always copy, never move; source SD card is untouched
2. **Safety first** — protected path registry, atomic copy, no overwrite, no delete
3. **Fast dedup** — filename+size index for scan (avoids hashing 600 RAW files upfront); SHA256 for DB history (planned)
4. **Camera-aware scanning** — Sony stores videos in PRIVATE/M4ROOT/CLIP/, not DCIM
5. **Rule templates** — user-configurable, stored in TOML, editable via GUI (planned)
6. **Offline-first** — no cloud, no login, fully local
7. **Resumable imports** — interrupted import re-runs skip already-copied files via dedup
8. **Cross-platform paths** — `pathlib.Path` throughout, no hardcoded separators
9. **Chunked copy** — 4 MB chunks, continuous progress bar, cancel between files

---

## Dependencies (requirements.txt)

```
PySide6>=6.6
Pillow>=10.0
exifread>=3.0
pymediainfo>=6.0
tomli-w>=1.0
SQLAlchemy>=2.0
```
