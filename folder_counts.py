import os
import argparse
from pathlib import Path
from typing import Dict, Tuple

def get_folder_stats(root_path: Path) -> Dict[Path, int]:
    """
    Recursively counts files in folders and aggregates sums for parents.
    Returns a dictionary mapping folder paths to total file counts.
    """
    stats: Dict[Path, int] = {}

    # Walk bottom-up so we process children before parents
    for root, dirs, files in os.walk(root_path, topdown=False):
        current_path = Path(root)

        # Count files in the immediate folder (ignoring hidden files)
        current_file_count = len([f for f in files if not f.startswith('.')])

        # Add the counts from immediate subdirectories already processed
        subfolder_total = sum(stats.get(current_path / d, 0) for d in dirs)

        stats[current_path] = current_file_count + subfolder_total

    return stats

def print_tree(path: Path, stats: Dict[Path, int], prefix: str = "") -> None:
    """
    Prints a visual tree structure of the folders with their aggregated file counts.
    """
    count = stats.get(path, 0)
    # Highlight the folder name and its count
    print(f"{prefix}└── {path.name}/ ({count} files)")

    # Get immediate subdirectories
    subdirs = sorted([d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')])

    for i, subdir in enumerate(subdirs):
        # Adjust indentation for the tree visual
        new_prefix = prefix + "    "
        print_tree(subdir, stats, new_prefix)

def main() -> None:
    parser = argparse.ArgumentParser(description="Count files in folders recursively.")
    parser.add_argument("root", help="The root directory to scan")
    args = parser.parse_args()

    root_path = Path(args.root).expanduser().resolve()

    if not root_path.exists() or not root_path.is_dir():
        print(f"Error: {root_path} is not a valid directory.")
        return

    print(f"\nScanning: {root_path}")
    print("-" * 40)

    folder_stats = get_folder_stats(root_path)
    print_tree(root_path, folder_stats)
    print("-" * 40)

if __name__ == "__main__":
    main()
