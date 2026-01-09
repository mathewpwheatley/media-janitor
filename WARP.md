# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A collection of Python utilities for managing and organizing photo/video libraries. The scripts are designed to work with external media drives and organize files by date using EXIF metadata.

**Core Architecture:**
- Three standalone scripts, each handling a specific media management task
- All scripts support dry-run mode to preview changes before execution
- Uses EXIF metadata extraction for photo date detection with graceful fallback to file modification times
- Designed for Family shared drive structure: `/Volumes/Family/{Incoming,Photos,Videos}`

## Scripts

### organize_media.py
Primary media organization tool that sorts folders from an incoming directory into dated year/month structure.

**Key Features:**
- Classifies folders as photo or video-dominant based on file counts
- Interactive mode with folder rename, ungroup, accept, or skip options
- UNGROUP mode: breaks up folders and distributes files individually by their dates
- Handles EXIF metadata corruption gracefully with fallback to file modification times

**Configuration Constants** (edit at top of file):
- `ROOT`: Source directory to scan (default: `/Volumes/Family/Incoming`)
- `PHOTO_ROOT`: Photo destination (default: `/Volumes/Family/Photos`)
- `VIDEO_ROOT`: Video destination (default: `/Volumes/Family/Videos`)
- `DRY_RUN`: Set to `False` to apply changes (default: `True`)
- `INTERACTIVE`: Set to `False` for batch processing (default: `True`)

**Supported formats:**
- Photos: `.jpg`, `.jpeg`, `.png`, `.heic`, `.tif`, `.tiff`, `.nef`, `.cr2`, `.arw`
- Videos: `.mp4`, `.mov`, `.avi`, `.mkv`, `.mts`

### folder_flatten.py
Flattens nested folder structures into a single directory, handling duplicate filenames by keeping the largest file.

**Usage:**
- `python folder_flatten.py <source> [target] [--dry-run]`
- If no target provided, creates `<source>/flattened/`

### folder_counts.py
Analyzes and displays folder statistics in a tree view with aggregated photo/video/other file counts.

**Usage:**
- `python folder_counts.py <root>`
- Displays recursive counts for all subdirectories

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install ExifRead
```

### Running Scripts
```bash
# Always test with dry-run first
python organize_media.py  # DRY_RUN defaults to True

# Flatten a folder structure
python folder_flatten.py "/path/to/source" --dry-run

# View folder statistics
python folder_counts.py "/Volumes/Family/Incoming"
```

### Testing Changes
Since there are no formal tests, validate changes by:
1. Running with `DRY_RUN = True` and reviewing output
2. Testing on a small sample directory first
3. Checking that EXIF parsing handles corrupted metadata gracefully
4. Verifying duplicate file handling logic preserves larger files

## Project-Specific Patterns

**EXIF Handling:**
The `get_photo_date()` function in `organize_media.py` uses a defensive approach:
- Stops tag parsing early with `stop_tag="EXIF DateTimeOriginal"` and `details=False`
- Wraps string conversion in try-catch to handle slice/corruption errors
- Falls back to file modification time on any parsing failure

**File Classification:**
All scripts share common extension sets defined as `PHOTO_EXT` and `VIDEO_EXT`. When modifying supported formats, update consistently across:
- `organize_media.py` (lines 14-25)
- `folder_counts.py` (lines 7-19)

**Safety Features:**
- All scripts skip hidden files (starting with `.`)
- Duplicate detection prevents data loss
- Dry-run mode is default for destructive operations
- Year folders (4-digit names) are automatically skipped to avoid re-processing

## Python Environment
- Python 3.14.2
- Virtual environment in `venv/`
- Main dependency: `ExifRead 3.5.1`
