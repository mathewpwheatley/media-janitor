"""Find and remove duplicate files based on content hash."""

import hashlib
import os
from collections import defaultdict
from typing import Dict, List, Tuple


def compute_hash(file_path: str) -> str:
    """Compute MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"  [!] Could not hash {os.path.basename(file_path)}: {e}")
        return ""


def find_duplicates(root: str) -> Dict[str, List[str]]:
    """
    Scan directory for duplicate files based on content hash.

    Returns:
        Dictionary mapping hash -> list of file paths with that hash
    """
    hash_map: Dict[str, List[str]] = defaultdict(list)

    print(f"Scanning {root} for duplicates...\n")
    for dirpath, _, filenames in os.walk(root):
        print(f"Checking {len(filenames)} files in {dirpath}")
        for filename in filenames:

            if filename.startswith("."):
                continue

            file_path = os.path.join(dirpath, filename)

            # Skip non-files (symlinks, etc.)
            if not os.path.isfile(file_path):
                continue

            file_hash = compute_hash(file_path)
            if file_hash:
                hash_map[file_hash].append(file_path)

    # Filter to only duplicates (hash appears more than once)
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    return duplicates


def calculate_space_savings(duplicates: Dict[str, List[str]]) -> Tuple[int, int]:
    """
    Calculate potential space savings from removing duplicates.

    Returns:
        Tuple of (duplicate_count, bytes_saved)
    """
    duplicate_count = 0
    bytes_saved = 0

    for paths in duplicates.values():
        # Keep one copy, remove the rest
        duplicate_count += len(paths) - 1

        # All files have same size, so get size from first file
        try:
            file_size = os.path.getsize(paths[0])
            bytes_saved += file_size * (len(paths) - 1)
        except OSError:
            pass

    return duplicate_count, bytes_saved


def format_size(bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def dedupe(root: str, dry_run: bool = True) -> None:
    """
    Find and optionally remove duplicate files.

    Args:
        root: Root directory to scan
        dry_run: If True, only show what would be done
    """
    if not os.path.exists(root):
        print(f"Error: {root} is not accessible.")
        return

    duplicates = find_duplicates(root)

    if not duplicates:
        print("\nNo duplicates found!")
        return

    duplicate_count, bytes_saved = calculate_space_savings(duplicates)

    print(f"\n{'='*60}")
    print(f"Found {len(duplicates)} sets of duplicate files")
    print(f"Total duplicates: {duplicate_count} files")
    print(f"Space that could be saved: {format_size(bytes_saved)}")
    print(f"{'='*60}\n")

    # Display duplicate sets
    for idx, (file_hash, paths) in enumerate(duplicates.items(), 1):
        file_size = os.path.getsize(paths[0])
        print(
            f"\nDuplicate Set #{idx} (Hash: {file_hash[:8]}..., Size: {format_size(file_size)})"
        )

        # Sort by path length (keep shortest, typically the "original")
        paths_sorted = sorted(paths, key=lambda p: len(p))

        for i, path in enumerate(paths_sorted):
            if i == 0:
                print(f"  [KEEP] {path}")
            else:
                print(f"  [DELETE] {path}")

    # Delete duplicates if not dry run
    if not dry_run:
        print(f"\n{'='*60}")
        print("Deleting duplicates...")
        print(f"{'='*60}\n")

        deleted_count = 0
        for paths in duplicates.values():
            # Keep shortest path, delete rest
            paths_sorted = sorted(paths, key=lambda p: len(p))

            for path in paths_sorted[1:]:
                try:
                    os.remove(path)
                    print(f"  Deleted: {path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  [!] Could not delete {path}: {e}")

        print(f"\nDeleted {deleted_count} duplicate files")
        print(f"Freed {format_size(bytes_saved)}")
    else:
        print(f"\n[DRY RUN] Run without --dry-run to actually delete duplicates")
