"""Health check for media libraries - detect corrupted and problematic files."""

import sys
import os
import subprocess
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from PIL import Image
import exifread

from constants import (
    PHOTO_EXT,
    PHOTO_THRESHOLDS,
    VIDEO_EXT,
    VIDEO_THRESHOLDS,
    ThresholdConfig,
    Year,
)


def format_threshold(thresholds: Dict[Year, ThresholdConfig]) -> str:
    message = ""
    header = f"{'Label':<30} | {'Min Size':<12} | {'Resolution'}\n"
    message += header
    message += "-" * len(header) + "\n"

    # Sort by year to ensure the table flows chronologically
    for year in sorted(thresholds.keys()):
        config = thresholds[year]

        # Convert bytes to KB/MB for readability
        size_str = f"{config.min_bytes / 1024:,.0f} KB"
        res_str = f"{config.min_width}x{config.min_height} pixels"

        message += f"{config.label:<30} | {size_str:<12} | {res_str}\n"
    return message


def print_thresholds() -> None:
    print("Photo Thresholds:")
    print(format_threshold(PHOTO_THRESHOLDS))
    print("Video Thresholds:")
    print(format_threshold(VIDEO_THRESHOLDS))


def get_file_date(file_path: str) -> Optional[datetime]:
    """Get the original date of a media file from EXIF or file modification time."""
    ext = os.path.splitext(file_path.lower())[1]

    # Try EXIF for photos
    if ext in PHOTO_EXT:
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

    # Fall back to file modification time
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception:
        return None


def get_size_threshold(file_date: Optional[datetime], ext: str) -> ThresholdConfig:
    """
    Get size and resolution thresholds based on file date.

    Returns:
        Tuple of (min_file_size_bytes, min_resolution_pixels)
    """
    legacy = 1990
    year = file_date.year if file_date else legacy
    active_map: Dict[int, ThresholdConfig] = (
        PHOTO_THRESHOLDS if ext.lower() in PHOTO_EXT else VIDEO_THRESHOLDS
    )

    for boundary in sorted(active_map.keys()):
        if year <= boundary:
            return active_map[boundary]

    return active_map[legacy]


def check_file_health(file_path: str) -> Tuple[bool, str]:
    """
    Check if a file is healthy.

    Returns:
        Tuple of (is_healthy, issue_description)
    """
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename.lower())[1]

    # Check if file exists and is accessible
    try:
        file_size = os.path.getsize(file_path)
    except OSError as e:
        return False, f"Cannot access file: {e}"

    # Check for zero-byte files (always bad)
    if file_size == 0:
        return False, "Zero-byte file (ghost file)"

    # Get file date and era-appropriate thresholds
    file_date = get_file_date(file_path)
    thresholds = get_size_threshold(file_date, ext)

    # Check Photo/Video size
    if ext in PHOTO_EXT.union(VIDEO_EXT):
        if file_size < thresholds.min_bytes:
            return (
                False,
                f"Suspiciously small file ({file_size} bytes , {thresholds.label} threshold: {thresholds.min_bytes} bytes)",
            )

    # Check only photo resolution
    if ext in PHOTO_EXT:
        try:
            with Image.open(file_path) as img:
                # Verify by loading the image data
                img.verify()

                # Check for low resolution based on era
                with Image.open(file_path) as img_check:
                    width, height = img_check.size
                    if width < thresholds.min_width or height < thresholds.min_height:
                        return (
                            False,
                            f"Suspiciously low resolution ({width}x{height} pixels, {thresholds.label} threshold: {thresholds.min_width}x{thresholds.min_height} pixels)",
                        )

        except Exception as e:
            return False, f"Corrupted image: {e}"

    return True, "OK"


def open_file_preview(file_path: str) -> None:
    """Open a file in the default viewer (macOS)."""
    try:
        subprocess.run(["open", file_path], check=False)
    except Exception as e:
        print(f"  [!] Could not open file: {e}")


def prompt_delete_file(file_path: str, issue: str) -> bool:
    """Prompt user whether to delete a file. Returns True if should delete."""
    print(f"\nFile: {file_path}")
    print(f"Issue: {issue}")
    print(f"Size: {os.path.getsize(file_path)} bytes")

    choice = input("[d]=delete | [v]=view | [Enter/s]=skip: ").strip().lower()

    if choice == "v":
        print("Opening file...")
        open_file_preview(file_path)
        # Ask again after viewing
        choice = input("[d]=delete | [Enter/s]=skip: ").strip().lower()

    return choice == "d"


def health_check(
    root: str,
    dry_run: bool = True,
    interactive: bool = False,
    display_thresholds: bool = False,
) -> None:
    """
    Scan media library for health issues and optionally delete problematic files.

    Args:
        root: Root directory to scan
        dry_run: If True, only show what would be done
        interactive: If True, prompt for each file before deletion
        display_thresholds: If True, only print the date-based thresholds for reference
    """
    if display_thresholds:
        print_thresholds()
        return

    if not os.path.exists(root):
        print(f"Error: {root} is not accessible.")
        return

    print(f"Scanning {root} for health issues...\n")

    issues: List[Tuple[str, str]] = []
    healthy_count = 0
    total_count = 0

    for dirpath, _, filenames in os.walk(root):
        print(f"Checking {len(filenames)} files in {dirpath}")
        for filename in filenames:
            if filename.startswith("."):
                continue

            file_path = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename.lower())[1]

            # Only check media files
            if ext not in PHOTO_EXT and ext not in VIDEO_EXT:
                continue

            total_count += 1
            is_healthy, issue = check_file_health(file_path)

            if not is_healthy:
                issues.append((file_path, issue))
            else:
                healthy_count += 1

    # Display results
    if not issues:
        print("✓ No issues found! All media files appear healthy.\n")
        print(f"\nHealth Check Summary:")
        print(f"  Total media files scanned: {total_count}")
        print(f"  Healthy files: {healthy_count}")
        print(f"  Files with issues: 0")
        return

    print(f"Found {len(issues)} file(s) with issues:\n")
    print(f"{'='*80}")

    # Group issues by type
    issue_groups = {}
    for file_path, issue in issues:
        issue_type = issue.split(":")[0] if ":" in issue else issue
        if issue_type not in issue_groups:
            issue_groups[issue_type] = []
        issue_groups[issue_type].append((file_path, issue))

    # Display grouped issues
    for issue_type, group in issue_groups.items():
        print(f"\n{issue_type} ({len(group)} file(s)):")
        for file_path, issue in group:
            print(f"  - {file_path}")
            print(f"    Issue: {issue}")

    print(f"\n{'='*80}")

    # Summary
    print(f"\nHealth Check Summary:")
    print(f"  Total media files scanned: {total_count}")
    print(f"  Healthy files: {healthy_count}")
    print(f"  Files with issues: {len(issues)}")

    # Handle deletion
    if dry_run:
        print(f"\n[DRY RUN] Run with --execute to delete problematic files")
        if not interactive:
            print(f"[TIP] Use --interactive to review each file before deletion")
    else:
        print(f"\n{'='*80}")
        print("Processing files for deletion...")
        print(f"{'='*80}\n")

        deleted_count = 0
        skipped_count = 0

        for file_path, issue in issues:
            should_delete = True

            if interactive:
                should_delete = prompt_delete_file(file_path, issue)

            if should_delete:
                try:
                    os.remove(file_path)
                    print(f"  ✓ Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  [!] Could not delete {file_path}: {e}")
            else:
                print(f"  Skipped: {file_path}")
                skipped_count += 1

        print(f"\n{'='*80}")
        print(f"Deleted: {deleted_count} file(s)")
        if interactive:
            print(f"Skipped: {skipped_count} file(s)")
