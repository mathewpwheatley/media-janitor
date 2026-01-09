"""Fix file creation dates using EXIF metadata or filename patterns."""

import os
import re
from datetime import datetime
from typing import Optional

import exifread

from constants import PHOTO_EXT, VIDEO_EXT


def extract_date_from_exif(file_path: str) -> Optional[datetime]:
    """Extract original capture date from EXIF metadata."""
    try:
        with open(file_path, "rb") as f:
            tags = exifread.process_file(
                f, stop_tag="EXIF DateTimeOriginal", details=False
            )
            date_tag = tags.get("EXIF DateTimeOriginal")

            if date_tag:
                try:
                    return datetime.strptime(str(date_tag), "%Y:%m:%d %H:%M:%S")
                except (ValueError, IndexError, TypeError):
                    pass
    except Exception:
        pass

    return None


def extract_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Extract date from common filename patterns.

    Supports patterns like:
    - IMG_20220105_143022.jpg
    - 2022-01-05_14-30-22.jpg
    - 20220105_143022.jpg
    - Screenshot 2022-01-05 at 14.30.22.png
    """
    # Pattern 1: IMG_YYYYMMDD_HHMMSS
    pattern1 = r"(?:IMG|VID|DSC)?_?(\d{4})(\d{2})(\d{2})(?:_(\d{2})(\d{2})(\d{2}))?"
    match = re.search(pattern1, filename)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour = int(match.group(4)) if match.group(4) else 0
        minute = int(match.group(5)) if match.group(5) else 0
        second = int(match.group(6)) if match.group(6) else 0

        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass

    # Pattern 2: YYYY-MM-DD
    pattern2 = r"(\d{4})-(\d{2})-(\d{2})"
    match = re.search(pattern2, filename)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return datetime(year, month, day)
        except ValueError:
            pass

    return None


def get_correct_date(file_path: str) -> Optional[datetime]:
    """
    Get the correct date for a file, trying multiple sources in priority order.

    Priority:
    1. EXIF metadata (most reliable)
    2. Filename pattern
    3. None if neither works
    """
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename.lower())[1]

    # Try EXIF for photo files
    if ext in PHOTO_EXT:
        exif_date = extract_date_from_exif(file_path)
        if exif_date:
            return exif_date

    # Try filename pattern for all files
    filename_date = extract_date_from_filename(filename)
    if filename_date:
        return filename_date

    return None


def fix_dates(root: str, dry_run: bool = True) -> None:
    """
    Fix file modification dates using EXIF or filename patterns.

    Args:
        root: Root directory to scan
        dry_run: If True, only show what would be done
    """
    if not os.path.exists(root):
        print(f"Error: {root} is not accessible.")
        return

    print(f"Scanning {root} for files with fixable dates...\n")

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.startswith("."):
                continue

            file_path = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename.lower())[1]

            # Only process media files
            if ext not in PHOTO_EXT and ext not in VIDEO_EXT:
                continue

            # Get current modification time
            current_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

            # Get correct date
            correct_date = get_correct_date(file_path)

            if correct_date is None:
                skipped_count += 1
                continue

            # Check if date needs fixing (allow 1 second tolerance for rounding)
            time_diff = abs((correct_date - current_mtime).total_seconds())
            if time_diff < 1:
                continue

            # Fix the date
            if dry_run:
                print(f"[DRY RUN] {filename}")
                print(f"  Current:  {current_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Correct:  {correct_date.strftime('%Y-%m-%d %H:%M:%S')}")
                fixed_count += 1
            else:
                try:
                    # Set access and modification times
                    timestamp = correct_date.timestamp()
                    os.utime(file_path, (timestamp, timestamp))
                    print(f"Fixed: {filename}")
                    print(
                        f"  {current_mtime.strftime('%Y-%m-%d %H:%M:%S')} -> {correct_date.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    fixed_count += 1
                except Exception as e:
                    print(f"  [!] Could not fix {filename}: {e}")
                    error_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Files fixed: {fixed_count}")
    print(f"Files skipped (no date found): {skipped_count}")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print(f"{'='*60}")

    if dry_run and fixed_count > 0:
        print("\n[DRY RUN] Run without --dry-run to actually fix dates")
