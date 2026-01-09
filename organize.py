"""Organize media files into dated folder structures."""

import os
import shutil
import subprocess
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


def open_folder_in_finder(folder_path: str) -> None:
    """Open a folder in Finder (macOS)."""
    try:
        subprocess.run(["open", folder_path], check=False)
    except Exception as e:
        print(f"  [!] Could not open folder: {e}")


def prompt_user(
    folder_path: str, folder_name: str, year: int, month: int, count: int
) -> Tuple[FolderAction, str]:
    """Prompts user for action and returns the Action Enum and the folder name."""
    print(f"\nFolder: {folder_path}")
    print(f"Target: {year}/{month:02d}/")
    print(f"Files: {count}")

    while True:
        choice = input(
            "[Enter]=ungroup | r=rename (or enter a NEW NAME) | a=accept | v=view | s=skip: "
        ).strip()
        
        if len(choice) == 0:
            return FolderAction.UNGROUP, folder_name
        elif choice in ["a", "A"]:
            return FolderAction.ACCEPT, folder_name
        elif choice in ["s", "S"]:
            return FolderAction.SKIP, folder_name
        elif choice in ["v", "V"]:
            print("Opening folder...")
            open_folder_in_finder(folder_path)
            # Continue loop to prompt again after viewing
            continue
        elif choice in ["r", "R"]:
            new_name = input("New folder name: ").strip()
            return FolderAction.RENAME, new_name or folder_name
        else:
            # Treat as a new folder name
            new_name = choice.strip()
            return FolderAction.RENAME, new_name or folder_name


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
                print(f"[!] File already exists, skipping: {name}")
                continue

            if dry_run:
                print(f"[DRY RUN] Move file: {name} -> {dest_dir}")
            else:
                print(f"Moving file: {name} -> {dest_path}")
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

    print(f"\nScanning {source} for media files and folders...\n")

    # Track folders that have been processed
    processed_paths = set()

    # First pass: collect all directories
    directories_to_process = []
    loose_files_in_root = []

    # Walk bottom-up so children are processed before parents
    for dirpath, dirnames, filenames in os.walk(source, topdown=False):
        # Skip already processed year folders
        dirnames[:] = [d for d in dirnames if not (d.isdigit() and len(d) == 4)]

        # Get relative path for display
        rel_path = os.path.relpath(dirpath, source)
        if rel_path == ".":
            rel_path = "<root>"

        # Count media files in current directory (not in subdirs)
        media_files = [f for f in filenames
                      if not f.startswith(".")
                      and os.path.splitext(f.lower())[1] in PHOTO_EXT.union(VIDEO_EXT)]

        print(f"Checking {len(media_files)} media file(s) in {rel_path}")

        # If we're in the source root directory, handle loose files separately
        if dirpath == source:
            if media_files:
                loose_files_in_root = [(os.path.join(dirpath, f), f) for f in media_files]
            # Don't process source as a folder, just its subdirectories
            continue

        # For subdirectories, add to processing queue if they have media
        if media_files or dirnames:  # Process if has media or subdirectories
            directories_to_process.append(dirpath)

    # Process loose files in root directory
    if loose_files_in_root:
        print(f"\nProcessing {len(loose_files_in_root)} loose file(s) in source root...")
        for file_path, filename in loose_files_in_root:
            ext = os.path.splitext(filename.lower())[1]

            if ext in PHOTO_EXT:
                date = get_photo_date(file_path)
                dest_root = photo_dest
            elif ext in VIDEO_EXT:
                date = datetime.fromtimestamp(os.path.getmtime(file_path))
                dest_root = video_dest
            else:
                continue

            dest_dir = os.path.join(dest_root, str(date.year), f"{date.month:02d}")
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)

            if os.path.exists(dest_path):
                print(f"  [!] File already exists, skipping: {filename}")
                continue

            if dry_run:
                print(f"  [DRY RUN] Would move: {filename} -> {dest_dir}")
            else:
                print(f"  --> Moving: {filename}")
                shutil.move(file_path, dest_path)

    # Process subdirectories
    print(f"\nProcessing {len(directories_to_process)} folder(s)...\n")
    for folder_path in directories_to_process:
        if folder_path in processed_paths:
            continue

        folder_name = os.path.basename(folder_path)

        # Classify the folder
        dates, photos, videos = classify_folder(folder_path)
        if not dates:
            continue

        year, month = choose_target_date(dates)
        target_root = photo_dest if photos >= videos else video_dest

        action = FolderAction.ACCEPT
        final_name = folder_name

        if interactive:
            action, final_name = prompt_user(
                folder_path, folder_name, year, month, photos + videos
            )

        if action == FolderAction.SKIP:
            print(f"  Skipping {folder_name}...")
            processed_paths.add(folder_path)
            continue
        elif action == FolderAction.UNGROUP:
            print(f"  Ungrouping {folder_name}...")
            move_individual_files(folder_path, photo_dest, video_dest, dry_run)
            processed_paths.add(folder_path)
        else:
            # Covers ACCEPT and RENAME
            move_entire_folder(
                folder_path, target_root, year, month, final_name, dry_run
            )
            processed_paths.add(folder_path)

    print(f"\nOrganization complete!")
    
    # Clean up empty folders
    if not dry_run:
        print(f"\nCleaning up empty folders in {source}...")
        remove_empty_folders(source)


def remove_empty_folders(root: str) -> None:
    """Remove all empty folders from the directory tree."""
    deleted_count = 0
    
    # Walk bottom-up so we can delete child folders before checking parents
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        # Skip the root directory itself
        if dirpath == root:
            continue
        
        # Skip year folders (4-digit names)
        folder_name = os.path.basename(dirpath)
        if folder_name.isdigit() and len(folder_name) == 4:
            continue
        
        # Check if directory is empty (no files and no subdirectories)
        try:
            if not os.listdir(dirpath):
                print(f"  Removing empty folder: {dirpath}")
                os.rmdir(dirpath)
                deleted_count += 1
        except Exception as e:
            print(f"  [!] Could not remove {dirpath}: {e}")
    
    if deleted_count > 0:
        print(f"\nRemoved {deleted_count} empty folder(s)")
    else:
        print("  No empty folders found")
