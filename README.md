# Media Mporter

A cross-platform desktop application for importing media from camera SD cards to an external hard drive. Built for photographers and videographers who want automatic, rule-based file organisation with zero risk of data loss.

---

## Features

- **Automatic SD card detection** — detects cards via direct slot or USB dongle
- **Camera-aware scanning** — handles Sony, Canon, Nikon, Fuji, GoPro, DJI folder structures (Sony MP4s in `PRIVATE/M4ROOT/CLIP/` are found automatically)
- **Smart deduplication** — skips files already on your drive (filename + size match)
- **Rule-based folder organisation** — RAW, JPG and video files sorted into dated subfolders
- **Non-destructive** — always copies, never moves or deletes; source card is never touched
- **Atomic file copy** — writes to a temp file first, renames only on success; no partial files on failure
- **Pre-import space check** — warns before starting if destination drive lacks space
- **Continuous progress** — per-file and within-file progress bar (updates every 4 MB)
- **Cancel anytime** — stop import cleanly between files; already-copied files are kept
- **Full logging** — rotating log at `~/.media-mporter/logs/mporter.log`

---

## Supported File Types

| Type  | Extensions |
|-------|-----------|
| RAW   | `.arw` `.cr2` `.cr3` `.nef` `.dng` `.raf` `.rw2` |
| Photo | `.jpg` `.jpeg` `.heic` `.png` `.tif` `.tiff` |
| Video | `.mp4` `.mov` `.mts` `.m2ts` `.avi` `.mkv` |

---

## Folder Structure

Files are organised on the destination drive by type and capture date from EXIF / video metadata:

```
External Drive/
├── Photography/
│   ├── RAW/
│   │   └── 2026-03-24/
│   │       └── DSC06001.ARW
│   └── JPG/
│       └── 2026-03-24/
│           └── DSC06001.JPG
└── Footage/
    └── 2026-03-24/
        └── C0001.MP4
```

Date folders use the **capture date from metadata**, not today's date.

---

## Requirements

- Python 3.11+
- macOS or Windows
- [MediaInfo](https://mediaarea.net/en/MediaInfo) (required by `pymediainfo` for video metadata)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/yourname/media-mporter.git
cd media-mporter

# Create and activate conda environment
conda create -n media-mporter python=3.11 -y
conda activate media-mporter

# Install dependencies
pip install -e ".[dev]"
```

---

## Running

```bash
conda activate media-mporter
python main.py
```

---

## Usage

1. **Plug in your SD card** — it appears under **Camera Cards** in the left panel
2. **Select your external drive** — click it under **Storage Drives**; destination paths are auto-filled
3. **Click Scan Card** — the app scans the card and shows all files with New / Already Imported status
4. **Click Import New Files** — only new files are copied; progress updates per chunk
5. **Cancel anytime** — the current file finishes cleanly, already-copied files are kept

---

## CLI Tools

```bash
# Scan an SD card and list all media files
python scan_card.py /Volumes/Untitled

# Import new files from SD card to external drive
python import_card.py /Volumes/Untitled /Volumes/External

# Show kind + capture date for all files
python inspect_files.py /Volumes/Untitled
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
media-mporter/
├── backend/
│   ├── core/
│   │   ├── scanner.py          # SD card scan with camera profile detection
│   │   ├── camera_profiles.py  # per-brand folder structure profiles
│   │   ├── inspector.py        # extract kind + capture date from any file
│   │   ├── metadata.py         # EXIF (exifread/Pillow) + video (pymediainfo)
│   │   ├── models.py           # MediaFile, MediaType
│   │   ├── rules.py            # destination path engine
│   │   ├── importer.py         # chunked copy engine with progress + cancel
│   │   ├── dedup.py            # filename+size dedup index
│   │   └── safety.py           # safety guards, atomic copy, space checks
│   └── utils/
│       ├── detector.py         # drive detection (Mac diskutil / Windows ctypes)
│       ├── registry.py         # drive role registry (persisted JSON)
│       └── log_setup.py        # rotating file log + console handler
├── gui/
│   ├── main_window.py          # main window, workers, signals
│   └── widgets/
│       ├── source_panel.py     # Camera Cards / Storage Drives sections
│       ├── dest_panel.py       # destination path pickers
│       └── file_table.py       # file list with live status updates
├── tests/
├── main.py                     # entry point
└── pyproject.toml
```

---

## Safety Guarantees

| Rule | How it's enforced |
|---|---|
| Never write to SD card | Source drive registered as protected on detection |
| Never delete any file | `guard_delete()` always raises — unconditional |
| Never overwrite existing files | Existence check before every copy |
| No partial files on failure | Atomic temp file → rename on success only |
| Space check before import | Batch check per destination drive, blocks import if insufficient |

---

## Logs

```
~/.media-mporter/
├── logs/
│   ├── mporter.log        # current log (up to 5 MB)
│   ├── mporter.log.1      # previous
│   └── mporter.log.2
└── drives.json            # saved drive registry
```

---

## Roadmap

- [ ] Persistent config (TOML) — save destination paths across launches
- [ ] Import history database (SQLite) — bulletproof dedup, import log viewer
- [ ] Post-copy SHA256 verification
- [ ] Customisable folder naming templates
- [ ] Settings panel
- [ ] PyInstaller packaging — `.app` for Mac, `.exe` for Windows

See [PLAN.md](PLAN.md) for full detail.

---

## License

MIT
