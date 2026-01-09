"""Assign a specific date to all files in a folder."""

import os
import re
from datetime import datetime
from typing import Optional

from constants import PHOTO_EXT, VIDEO_EXT


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string with flexible formats.

    Supported formats:
    - YYYY (e.g., "2020")
    - YYYY-MM (e.g., "2020-06")
    - YYYY-MM-DD (e.g., "2020-06-15")
    - YYYY-MM-DD HH:MM (e.g., "2020-06-15 14:30")
    - YYYY-MM-DD HH:MM:SS (e.g., "2020-06-15 14:30:45")

    Missing components default to middle of parent period:
    - Missing month: June (month 6)
    - Missing day: 15th
    - Missing hour: 12:00
    - Missing minute: 00
    - Missing second: 00
    """
    date_str = date_str.strip()

    # Pattern: YYYY-MM-DD HH:MM:SS
    pattern_full = r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$'
    match = re.match(pattern_full, date_str)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        return datetime(year, month, day, hour, minute, second)

    # Pattern: YYYY-MM-DD HH:MM
    pattern_min = r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$'
    match = re.match(pattern_min, date_str)
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        return datetime(year, month, day, hour, minute, 0)

    # Pattern: YYYY-MM-DD
    pattern_day = r'^(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(pattern_day, date_str)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day, 12, 0, 0)

    # Pattern: YYYY-MM
    pattern_month = r'^(\d{4})-(\d{2})$'
    match = re.match(pattern_month, date_str)
    if match:
        year, month = map(int, match.groups())
        return datetime(year, month, 15, 12, 0, 0)

    # Pattern: YYYY
    pattern_year = r'^(\d{4})$'
    match = re.match(pattern_year, date_str)
    if match:
        year = int(match.group(1))
        # Middle of year: July 1st (month 7, day 1)
        return datetime(year, 7, 1, 12, 0, 0)

    raise ValueError(
        f"Invalid date format: '{date_str}'. "
        "Expected formats: YYYY, YYYY-MM, YYYY-MM-DD, "
        "YYYY-MM-DD HH:MM, or YYYY-MM-DD HH:MM:SS"
    )


def assign_date(source: str, date_str: str, dry_run: bool = False) -> None:
    """
    Assign a specific date to all media files in a folder.

    Args:
        source: Source folder containing files
        date_str: Date string to assign (flexible formats)
        dry_run: If True, only show what would be done
    """
    if not os.path.exists(source):
        print(f"Error: {source} is not accessible.")
        return

    # Parse the date
    try:
        target_date = parse_date_string(date_str)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print(f"\nAssigning date: {target_date.strftime('%Y-%m-%d %H:%M:%S')}")

    # Collect all media files
    media_files = []

    if os.path.isfile(source):
        # Single file mode
        print(f"Source file: {source}\n")
        filename = os.path.basename(source)
        ext = os.path.splitext(filename.lower())[1]

        if ext in PHOTO_EXT or ext in VIDEO_EXT:
            media_files.append(source)
        else:
            print(f"Error: {filename} is not a media file.")
            print(f"Supported formats: {', '.join(sorted(PHOTO_EXT | VIDEO_EXT))}")
            return
    else:
        # Directory mode
        print(f"Source folder: {source}\n")
        for root, _, files in os.walk(source):
            for filename in files:
                if filename.startswith("."):
                    continue

                ext = os.path.splitext(filename.lower())[1]
                if ext in PHOTO_EXT or ext in VIDEO_EXT:
                    file_path = os.path.join(root, filename)
                    media_files.append(file_path)

    if not media_files:
        print("No media files found in the specified folder.")
        return

    print(f"Found {len(media_files)} media file(s)\n")

    # Assign date to each file
    updated_count = 0
    skipped_count = 0
    error_count = 0

    timestamp = target_date.timestamp()

    for file_path in media_files:
        filename = os.path.basename(file_path)

        # Get current modification time
        try:
            current_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        except Exception as e:
            print(f"  [!] Could not read {filename}: {e}")
            error_count += 1
            continue

        # Check if already has the target date (within 1 second tolerance)
        time_diff = abs((target_date - current_mtime).total_seconds())
        if time_diff < 1:
            skipped_count += 1
            continue

        # Update the date
        if dry_run:
            print(f"[DRY RUN] {filename}")
            print(f"  Current:  {current_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  New:      {target_date.strftime('%Y-%m-%d %H:%M:%S')}")
            updated_count += 1
        else:
            try:
                os.utime(file_path, (timestamp, timestamp))
                print(f"Updated: {filename}")
                print(f"  {current_mtime.strftime('%Y-%m-%d %H:%M:%S')} -> {target_date.strftime('%Y-%m-%d %H:%M:%S')}")
                updated_count += 1
            except Exception as e:
                print(f"  [!] Could not update {filename}: {e}")
                error_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Files updated: {updated_count}")
    print(f"Files skipped (already correct): {skipped_count}")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print(f"{'='*60}")

    if dry_run and updated_count > 0:
        print("\n[DRY RUN] Run without --dry-run to actually assign dates")
