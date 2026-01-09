"""Flatten nested folder structures into a single directory."""

import os
import shutil
from typing import Optional, Set, Dict, Tuple


def flatten_folder(
    source: str, target: str, dry_run: bool, extensions: Optional[Set[str]] = None
) -> None:
    """
    Flatten all files from the source folder (recursively) into the target folder.
    Keeps the largest file in case of duplicates (by filename).

    Args:
        source: Source folder to flatten
        target: Target folder for flattened files
        dry_run: If True, only show what would be done
        extensions: Optional set of file extensions to include (e.g. {".jpg", ".png"})
    """
    os.makedirs(target, exist_ok=True)

    # Keep track of files we've already moved: filename -> (full_path, size)
    seen: Dict[str, Tuple[str, int]] = {}

    for root, _, files in os.walk(source):
        for file in files:
            ext: str = os.path.splitext(file)[1].lower()
            if extensions and ext not in extensions:
                continue

            src_path: str = os.path.join(root, file)
            size: int = os.path.getsize(src_path)

            # Skip files already in the target folder
            if os.path.abspath(root) == os.path.abspath(target):
                continue

            prefix = "[Dry Run] " if dry_run else ""
            if file in seen:
                existing_path, existing_size = seen[file]

                if size > existing_size:
                    print(
                        f"{prefix}Replace (keep bigger): {existing_path} -> {src_path}"
                    )
                    if not dry_run:
                        os.remove(existing_path)
                        shutil.move(src_path, os.path.join(target, file))
                        seen[file] = (os.path.join(target, file), size)
                else:
                    print(f"{prefix}Skip smaller duplicate: {src_path}")
                    if not dry_run:
                        os.remove(src_path)
            else:
                dest_path: str = os.path.join(target, file)
                print(f"{prefix}Move: {src_path} -> {dest_path}")
                if not dry_run:
                    shutil.move(src_path, dest_path)
                seen[file] = (dest_path, size)

    print("Flattening complete.")
