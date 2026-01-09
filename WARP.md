# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A CLI tool for managing and organizing photo/video libraries.

**Core Architecture:**
- Unified CLI tool (`media-janitor`) with three subcommands
- All commands support dry-run mode to preview changes before execution
- Uses EXIF metadata extraction for photo date detection with graceful fallback to file modification times

## Package Structure

```
__init__.py       # Package initialization and version
cli.py            # Main CLI entry point with argparse
common.py         # Shared constants (PHOTO_EXT, VIDEO_EXT), types (FolderAction, Stats)
organize.py       # Media organization logic
flatten.py        # Folder flattening logic
count.py          # Folder statistics logic
pyproject.toml    # Package configuration and dependencies
```

## Commands

### media-janitor organize
Organize media files from a source directory into dated year/month folder structures.

**Key Features:**
- Classifies folders as photo or video-dominant based on file counts
- Interactive mode with folder rename, ungroup, accept, or skip options
- UNGROUP mode: breaks up folders and distributes files individually by their dates
- Handles EXIF metadata corruption gracefully with fallback to file modification times

**Required Arguments:**
- `--source`: Source directory to scan for media folders
- `--photo-dest`: Destination directory for photo folders
- `--video-dest`: Destination directory for video folders

**Optional Flags:**
- `--dry-run`: Show what would be done (default behavior)
- `--execute`: Actually execute the moves
- `--no-interactive`: Run in batch mode without prompting

**Supported formats:**
- Photos: `.jpg`, `.jpeg`, `.png`, `.heic`, `.tif`, `.tiff`, `.nef`, `.cr2`, `.arw`
- Videos: `.mp4`, `.mov`, `.avi`, `.mkv`, `.mts`

### media-janitor flatten
Flatten nested folder structures into a single directory, handling duplicate filenames by keeping the largest file.

**Arguments:**
- `source`: Source folder to flatten (required)
- `target`: Target folder for flattened files (optional, defaults to `<source>/flattened`)

**Flags:**
- `--dry-run`: Show what would be done without making changes

### media-janitor count
Analyze and display folder statistics in a tree view with aggregated photo/video/other file counts.

**Arguments:**
- `root`: Root directory to scan (required)

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install package in editable mode (for development)
pip install -e .
```

### Running Commands
```bash
# Organize media files (dry-run by default)
media-janitor organize --source "/Incoming" \
  --photo-dest "/Photos" \
  --video-dest "/Videos"

# Execute organization (actually move files)
media-janitor organize --source "/Incoming" \
  --photo-dest "/Photos" \
  --video-dest "/Videos" \
  --execute

# Flatten a folder structure (dry-run)
media-janitor flatten "/path/to/source" --dry-run

# View folder statistics
media-janitor count "/Incoming"

# View command help
media-janitor --help
media-janitor organize --help
```

### Testing Changes
Since there are no formal tests, validate changes by:
1. Running commands with dry-run (default for organize and flatten) and reviewing output
2. Testing on a small sample directory first
3. Checking that EXIF parsing handles corrupted metadata gracefully
4. Verifying duplicate file handling logic preserves larger files

## Project-Specific Patterns

**EXIF Handling:**
The `get_photo_date()` function in `organize.py` uses a defensive approach:
- Stops tag parsing early with `stop_tag="EXIF DateTimeOriginal"` and `details=False`
- Wraps string conversion in try-catch to handle slice/corruption errors
- Falls back to file modification time on any parsing failure

**File Classification:**
All commands share common extension sets defined in `common.py` as `PHOTO_EXT` and `VIDEO_EXT`. When modifying supported formats, update only in `common.py` - all commands import from there.

**Safety Features:**
- All scripts skip hidden files (starting with `.`)
- Duplicate detection prevents data loss
- Dry-run mode is default for destructive operations
- Year folders (4-digit names) are automatically skipped to avoid re-processing

## Python Environment
- Python 3.14.2
- Virtual environment in `venv/`
- Main dependency: `ExifRead 3.5.1`
