import os
import shutil
import argparse
from typing import Optional, Set, Dict, Tuple

# Optional: which file types to include (None = all)
EXTENSIONS: Optional[Set[str]] = None  # Example: {".jpg", ".png", ".mp4"}


def flatten_folder(source: str, target: str, dry_run: bool) -> None:
    """
    Flatten all files from the source folder (recursively) into the target folder.
    Keeps the largest file in case of duplicates (by filename).
    """
    os.makedirs(target, exist_ok=True)

    # Keep track of files we've already moved: filename -> (full_path, size)
    seen: Dict[str, Tuple[str, int]] = {}

    for root, _, files in os.walk(source):
        for file in files:
            ext: str = os.path.splitext(file)[1].lower()
            if EXTENSIONS and ext not in EXTENSIONS:
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
                    print(f"Move: {src_path} -> {dest_path}")
                    shutil.move(src_path, dest_path)
                seen[file] = (dest_path, size)

    print("Flattening complete.")


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Flatten folder structure"
    )
    parser.add_argument("source", help="Source folder to flatten")
    parser.add_argument("target", nargs="?", help="Target folder (optional)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show actions without moving files"
    )

    args: argparse.Namespace = parser.parse_args()

    source: str = os.path.abspath(args.source)
    target: str = (
        os.path.abspath(args.target)
        if args.target
        else os.path.join(source, "flattened")
    )

    flatten_folder(source, target, args.dry_run)


if __name__ == "__main__":
    main()
