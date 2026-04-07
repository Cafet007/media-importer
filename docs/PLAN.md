# Media Porter — Project Plan

## Vision
A cross-platform desktop app (Mac + Windows) that imports media from camera SD cards
into a user-defined folder structure on an external hard drive. Built for photographers
and videographers who want safe, verified, rule-based organization of their footage.

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
| Dedup        | `hashlib` SHA256 (post-copy verify)| 🔧 Phase 1 |
| Database     | SQLite + SQLAlchemy               | 🔧 Phase 2  |
| SD detection | polling (DriveWatcher)            | ✅ Done      |
| Packaging    | PyInstaller (`.app` / `.exe`)     | ⬜ Phase 3  |
| Config       | TOML (`tomllib` / `tomli-w`)      | 🔧 Phase 2  |

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
│   ├── test_rules.py           ✅
│   ├── test_dedup.py           ✅
│   └── test_importer.py        ✅
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
                                            └─► SHA256 verify  → confirm dest matches source
                                                    └─► DB → record import history
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
> Template engine will replace hardcoded layout in Phase 2.

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
    imported_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id   INTEGER REFERENCES sessions(id)
);

-- import sessions
CREATE TABLE sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,                  -- user-defined shoot/job name
    source_root  TEXT NOT NULL,
    dest_root    TEXT NOT NULL,
    backup_root  TEXT,                  -- second destination (dual backup)
    total_files  INTEGER,
    imported     INTEGER,
    skipped      INTEGER,
    errors       INTEGER,
    verified     INTEGER,               -- files that passed SHA256 check
    started_at   DATETIME,
    finished_at  DATETIME
);
```

---

## Safety System

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
| Post-copy verification | SHA256 source vs dest after every file (Phase 1) |

### Known Safety Bugs (Phase 1 fixes)
- Source card is only registered as protected inside `detector.py`; GUI `list_drives()` does not register it — card may not be guarded during import
- `safety.py` creates the destination directory before `guard_write()` runs — a misconfigured dest could cause writes into a protected path
- Duplicate filename identity uses bare `f.name` in several places — two files named `IMG_0001.JPG` from different folders can be miscounted or shown with wrong status

---

## Known Bugs (to fix in Phase 1)

| # | File | Line | Description |
|---|------|------|-------------|
| 1 | `backend/utils/detector.py` + `gui/widgets/source_panel.py` | 110 / 17, 207 | Source card not registered as protected in GUI path |
| 2 | `backend/core/safety.py` | 177–180 | Dest dir created before `guard_write()` runs |
| 3 | `gui/main_window.py`, `backend/core/importer.py`, `gui/widgets/file_table.py` | 379, 423 / 125 / 242 | Duplicate filename identity uses bare name, not `(name, size)` |
| 4 | `import_card.py` | 58 | CLI progress callback accepts 3 args, importer passes 5 |
| 5 | `gui/main_window.py` | 460 | Per-file progress bar shows batch bytes, not file bytes |

---

## Roadmap

### Phase 1 — Fix & Stabilize ✅ Target: April 2026
**Goal: app is safe and trustworthy on real shoots**

**Week 1 — Critical bugs**
- [ ] Fix safety gap: register source card as protected in GUI, not just in `detector.py`
- [ ] Fix write-before-guard: move dest dir creation to after `guard_write()` in `safety.py`
- [ ] Fix duplicate filename identity: use `(name, size)` tuples instead of bare names throughout
- [ ] Fix broken CLI: align `import_card.py` progress callback to 5-argument signature

**Week 2 — Core missing features**
- [ ] Post-copy SHA256 verification: hash source before copy, hash dest after, show pass/fail
- [ ] Fix progress bars: per-file bar shows file bytes, overall bar shows batch bytes
- [ ] Resume/recovery: on relaunch after crash, skip already-copied files via dedup
- [ ] Session report: plain text or CSV — copied, skipped, failed, verification result per file

**Exit criteria:** 10 real testers use it on actual card ingests with zero data-loss incidents.

---

### Phase 2 — Paid V1 ⬜ Target: June 2026
**Goal: first version worth charging for**

**Storage & History**
- [ ] SQLite import history via `db/repository.py` (schema above)
- [ ] Replace filename+size dedup with SHA256 hash dedup against history DB
- [ ] History panel: searchable by date, camera, session

**Workflow**
- [ ] Dual-destination copy: main drive + backup drive simultaneously
- [ ] Job/session naming before import (client name, shoot name)
- [ ] Presets: save and recall destination path + folder rule per workflow
- [ ] Sidecar awareness: keep RAW + JPG + XMP + LRV/THM together

**Settings & Config**
- [ ] `config.py` with TOML persistence: last destination, last drive, folder rules
- [ ] Settings panel: chunk size, verification mode, default paths
- [ ] Template rule engine: replace hardcoded layout with `{year}/{month_name}` variables

**Pricing at launch**

| Tier | Price | Limits |
|------|-------|--------|
| Free | $0 | Single destination, no presets, no history search |
| Pro  | $89 one-time | Dual backup, presets, full history, verification badge |

---

### Phase 3 — Pro Differentiation ⬜ Target: Sept–Nov 2026
**Goal: photographers describe it as part of their normal shoot workflow**

- [ ] Auto-ingest on card insert (skip manual scan step)
- [ ] Queue multiple cards / jobs
- [ ] Rename rules during import (not just folder structure)
- [ ] Drive health warnings: destination space forecast before import starts
- [ ] Watch-folder / hot-folder mode for studio use
- [ ] Conflict resolution UI: show files that hit destination-exists collision
- [ ] Error log panel + retry failed files
- [ ] Thumbnail preview before import
- [ ] App icon, PyInstaller `.app` bundle, `create-dmg` script
- [ ] Windows drive detection testing + `.exe` packaging


---

## What Not to Build
- AI culling or editing features
- Cloud gallery or social publishing
- Digital asset management (DAM)
- Mobile companion app

These will not be built unless demand is proven by paying users requesting them.

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
3. **Verified** — SHA256 hash check after every copy confirms data integrity
4. **Fast dedup** — filename+size index for scan (avoids hashing 600 RAW files upfront); SHA256 for DB history
5. **Camera-aware scanning** — Sony stores videos in PRIVATE/M4ROOT/CLIP/, not DCIM
6. **Rule templates** — user-configurable, stored in TOML, editable via GUI (Phase 2)
7. **Offline-first** — no cloud, no login, fully local
8. **Resumable imports** — interrupted import re-runs skip already-copied files via dedup
9. **Cross-platform paths** — `pathlib.Path` throughout, no hardcoded separators
10. **Chunked copy** — 4 MB chunks, continuous progress bar, cancel between files

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
