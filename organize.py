"""Organize media files into dated folder structures."""

import os
import shutil
from collections import Counter
from datetime import datetime
from typing import List, Tuple
from enum import Enum, auto

import exifread

from constants import PHOTO_EXT, VIDEO_EXT


class FolderAction(Enum):
    """Actions that can be taken on a folder during organization."""

    ACCEPT = auto()
    RENAME = auto()
    UNGROUP = auto()
    SKIP = auto()


def get_photo_date(path: str) -> datetime:
    """Attempts to extract EXIF date, falls back to file modification time."""
    try:
        with open(path, "rb") as f:
            # We add details=False to skip complex tag parsing that often causes slice errors
            tags = exifread.process_file(
                f, stop_tag="EXIF DateTimeOriginal", details=False
            )
            date_tag = tags.get("EXIF DateTimeOriginal")

            if date_tag:
                # Wrap the string conversion in a secondary try to catch 'slice' errors
                try:
                    return datetime.strptime(str(date_tag), "%Y:%m:%d %H:%M:%S")
                except (ValueError, IndexError, TypeError) as e:
                    print(f"  [!] Metadata corruption in {os.path.basename(path)}: {e}")
    except Exception as e:
        # Catch-all for exifread internal errors like "Unexpected slice length"
        print(
            f"  [!] Could not parse EXIF for {os.path.basename(path)}. Using file date."
        )

    return datetime.fromtimestamp(os.path.getmtime(path))


def classify_folder(folder_path: str) -> Tuple[List[datetime], int, int]:
    """Scans folder for media and returns dates and counts."""
    dates: List[datetime] = []
    photo_count: int = 0
    video_count: int = 0

    for root, _, files in os.walk(folder_path):
        for name in files:
            if name.startswith("."):
                continue
            ext = os.path.splitext(name.lower())[1]
            path = os.path.join(root, name)

            if ext in PHOTO_EXT:
                photo_count += 1
                dates.append(get_photo_date(path))
            elif ext in VIDEO_EXT:
                video_count += 1
                dates.append(datetime.fromtimestamp(os.path.getmtime(path)))

    return dates, photo_count, video_count


def choose_target_date(dates: List[datetime]) -> Tuple[int, int]:
    """Finds the most frequent Year and Month in the date list."""
    counts = Counter((d.year, d.month) for d in dates)
    return counts.most_common(1)[0][0]


def prompt_user(
    name: str, year: int, month: int, count: int
) -> Tuple[FolderAction, str]:
    """Prompts user for action and returns the Action Enum and the folder name."""
    print(f"\nFolder: {name}")
    print(f"Target: {year}/{month:02d}/")
    print(f"Files: {count}")

    choice = input("[Enter]=accept | r=rename | u=ungroup | s=skip: ").strip().lower()

    if choice == "r":
        new_name = input("New folder name: ").strip()
        return FolderAction.RENAME, new_name or name
    elif choice == "u":
        return FolderAction.UNGROUP, name
    elif choice == "s":
        return FolderAction.SKIP, name
    return FolderAction.ACCEPT, name


def move_individual_files(
    src_folder: str, photo_root: str, video_root: str, dry_run: bool
) -> None:
    """Moves files out of the folder individually into YYYY/MM/ structure."""
    for root, _, files in os.walk(src_folder):
        for name in files:
            if name.startswith("."):
                continue

            path = os.path.join(root, name)
            ext = os.path.splitext(name.lower())[1]

            if ext in PHOTO_EXT:
                date = get_photo_date(path)
                dest_root = photo_root
            elif ext in VIDEO_EXT:
                date = datetime.fromtimestamp(os.path.getmtime(path))
                dest_root = video_root
            else:
                continue

            dest_dir = os.path.join(dest_root, str(date.year), f"{date.month:02d}")
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, name)

            if os.path.exists(dest_path):
                print(f"  [!] File already exists, skipping: {name}")
                continue

            if dry_run:
                print(f"  [DRY RUN] Would move file: {name} -> {dest_dir}")
            else:
                print(f"  --> Moving file: {name}")
                shutil.move(path, dest_path)

    if not dry_run:
        try:
            if not os.listdir(src_folder):
                os.rmdir(src_folder)
        except Exception as e:
            print(f"  [!] Could not delete folder {src_folder}: {e}")


def move_entire_folder(
    src: str, dest_root: str, year: int, month: int, name: str, dry_run: bool
) -> None:
    """Moves the entire directory into the Year/Month structure."""
    dest_dir = os.path.join(dest_root, str(year), f"{month:02d}")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, name)

    if os.path.exists(dest_path):
        print(f"  [!] Destination folder already exists: {dest_path}")
        return

    if dry_run:
        print(f"  [DRY RUN] Would move folder: {src} -> {dest_path}")
    else:
        print(f"  --> Moving folder: {name} into {year}/{month:02d}/")
        shutil.move(src, dest_path)


def organize(
    source: str, photo_dest: str, video_dest: str, dry_run: bool, interactive: bool
) -> None:
    """
    Organize media files from source into photo and video destinations.

    Args:
        source: Source directory to scan
        photo_dest: Destination directory for photos
        video_dest: Destination directory for videos
        dry_run: If True, only show what would be done
        interactive: If True, prompt user for actions on each folder
    """
    if not os.path.exists(source):
        print(f"Error: {source} is not accessible.")
        return

    for entry in os.scandir(source):
        if not entry.is_dir():
            continue

        # Skip already processed year folders
        if entry.name.isdigit() and len(entry.name) == 4:
            continue

        folder_path = entry.path
        folder_name = entry.name

        dates, photos, videos = classify_folder(folder_path)
        if not dates:
            continue

        year, month = choose_target_date(dates)
        target_root = photo_dest if photos >= videos else video_dest

        action = FolderAction.ACCEPT
        final_name = folder_name

        if interactive:
            action, final_name = prompt_user(folder_name, year, month, photos + videos)

        if action == FolderAction.SKIP:
            print(f"Skipping {folder_name}...")
            continue
        elif action == FolderAction.UNGROUP:
            print(f"Ungrouping {folder_name}...")
            move_individual_files(folder_path, photo_dest, video_dest, dry_run)
        else:
            # Covers ACCEPT and RENAME
            move_entire_folder(
                folder_path, target_root, year, month, final_name, dry_run
            )
