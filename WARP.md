# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A CLI tool for managing and organizing photo/video libraries.

**Core Architecture:**
- Unified CLI tool (`media-janitor`) with six subcommands
- Most commands support dry-run mode to preview changes
- Most commands support interactive mode by default so changes can be reviewed before execution
- Uses EXIF metadata extraction for photo date detection with graceful fallback to file modification times
- Uses content hashing (MD5) for reliable duplicate detection
- Uses Pillow for image health validation

## Package Structure

```
__init__.py       # Package initialization and version
cli.py            # Main CLI entry point with argparse
common.py         # Shared constants (PHOTO_EXT, VIDEO_EXT), types (FolderAction, Stats)
organize.py       # Media organization logic
flatten.py        # Folder flattening logic
count.py          # Folder statistics logic
dedupe.py         # Duplicate file detection and removal using MD5 hashing
fix_dates.py      # Fix file dates using EXIF metadata or filename patterns
health_check.py   # Media library health scanning (corruption, thumbnails, ghost files)
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
- `source`: Source directory to scan for media folders
- `photo-dest`: Destination directory for photo folders
- `video-dest`: Destination directory for video folders

**Optional Flags:**
- `--dry-run`: Show what would be done
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

### media-janitor dedupe
Find and remove duplicate files based on content hash (MD5).

**Key Features:**
- Uses MD5 hash to compare file content, not just filenames
- Displays space savings before deletion
- Groups duplicates and shows which files will be kept/deleted
- Keeps shortest path (typically the "original" location)

**Arguments:**
- `root`: Root directory to scan for duplicates (required)

**Flags:**
- `--dry-run`: Show what would be done

### media-janitor fix-dates
Fix file modification dates using EXIF metadata or filename patterns.

**Key Features:**
- Extracts dates from EXIF metadata (most reliable)
- Falls back to filename patterns (IMG_YYYYMMDD, YYYY-MM-DD, etc.)
- Only processes media files (photos and videos)
- Shows before/after dates for each file

**Arguments:**
- `root`: Root directory to scan (required)

**Flags:**
- `--dry-run`: Show what would be done

**Supported filename patterns:**
- `IMG_20220105_143022.jpg`
- `2022-01-05_14-30-22.jpg`
- `20220105_143022.jpg`
- `Screenshot 2022-01-05 at 14.30.22.png`

### media-janitor health-check
Scan media library for corrupted files, ghost files, and thumbnails with intelligent date-based thresholds.

**Key Features:**
- Detects zero-byte "ghost" files
- Identifies corrupted images that won't open
- Finds low-resolution thumbnails masquerading as full-size images
- Uses date-based thresholds (older photos can legitimately be smaller)
- Can delete problematic files with dry-run and interactive modes
- Groups issues by type with actionable recommendations

**Arguments:**
- `root`: Root directory to scan (required)

**Flags:**
- `--dry-run`: Show what would be done
- `--no-interactive`: Batch check all files, deleting unhealthy files

**Date-based detection thresholds:**

Pre-2000 photos:
- Min size: 5KB, Min resolution: 320x320px
- Videos: 50KB minimum

2000s photos:
- Min size: 10KB, Min resolution: 480x480px
- Videos: 100KB minimum

2010+ photos:
- Min size: 20KB, Min resolution: 640x640px
- Videos: 200KB minimum

**Interactive mode options:**
- `d` = delete file
- `v` = view/preview file (opens in default viewer)
- `s` or Enter = skip file

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
# Organize media files (dry-run)
media-janitor organize "/Incoming" "/Photos" "/Videos" --dry-run

# Execute organization
media-janitor organize "/Incoming" "/Photos" "/Videos"

# Flatten a folder structure (dry-run)
media-janitor flatten "/path/to/source" --dry-run

# Execute flatten
media-janitor flatten "/path/to/source"

# View folder statistics
media-janitor count "/Incoming"

# Find duplicates (dry-run)
media-janitor dedupe "/Photos" --dry-run

# Execute dedupe
media-janitor dedupe "/Photos"

# Fix file dates (dry-run)
media-janitor fix-dates "/Photos" --dry-run

# Execute fix file dates
media-janitor fix-dates "/Photos"

# Check library health (dry-run)
media-janitor health-check "/Photos" --dry-run

# Delete problematic files (batch mode)
media-janitor health-check "/Photos" --no-interactive

# Delete problematic files (interactive mode - review each file)
media-janitor health-check "/Photos"

# View command help
media-janitor --help
media-janitor organize --help
media-janitor dedupe --help
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

**Safety Features:**
- All scripts skip hidden files (starting with `.`)
- Duplicate detection prevents data loss
- Dry-run mode is default for destructive operations
- Year folders (4-digit names) are automatically skipped to avoid re-processing

## Python Environment
- Python 3.14.2
- Virtual environment in `venv/`
- Dependencies:
  - `ExifRead >= 3.0.0` (EXIF metadata parsing)
  - `Pillow >= 10.0.0` (Image validation and health checks)
