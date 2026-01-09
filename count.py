"""Analyze and display folder statistics in a tree view."""

import os
from pathlib import Path
from typing import Dict
from dataclasses import dataclass

from constants import PHOTO_EXT, VIDEO_EXT


@dataclass
class Stats:
    """Statistics for photo, video, and other file counts."""

    Photo: int = 0
    Video: int = 0
    Other: int = 0

    def __iadd__(self, other: "Stats") -> "Stats":
        self.Photo += other.Photo
        self.Video += other.Video
        self.Other += other.Other
        return self


def get_folder_stats(root_path: Path) -> Dict[Path, Stats]:
    """
    Recursively counts photo, video, and other files in folders and
    aggregates totals for parent folders.
    Returns a dictionary mapping folder paths to Stats.
    """
    stats: Dict[Path, Stats] = {}

    # Walk bottom-up so children are processed before parents
    for root, dirs, files in os.walk(root_path, topdown=False):
        current_path: Path = Path(root)
        current_stats: Stats = Stats()

        # Count files in the immediate folder
        for filename in files:
            if filename.startswith("."):
                continue

            ext: str = Path(filename).suffix.lower()

            if ext in PHOTO_EXT:
                current_stats.Photo += 1
            elif ext in VIDEO_EXT:
                current_stats.Video += 1
            else:
                current_stats.Other += 1

        # Add stats from subdirectories
        for d in dirs:
            child_path: Path = current_path / d
            if child_path in stats:
                current_stats += stats[child_path]

        stats[current_path] = current_stats

    return stats


def print_tree(path: Path, stats: Dict[Path, Stats], prefix: str = "") -> None:
    """
    Prints a visual tree structure of the folders with their aggregated file counts.
    """
    counts = stats.get(path, Stats())
    # Highlight the folder name and its count
    print(
        f"{prefix}└── {path.name}/ (Photos: {counts.Photo}, Videos: {counts.Video}, Other: {counts.Other})"
    )

    # Get immediate subdirectories
    subdirs = sorted(
        [d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )

    for i, subdir in enumerate(subdirs):
        # Adjust indentation for the tree visual
        new_prefix = prefix + "    "
        print_tree(subdir, stats, new_prefix)


def display_count(root: str) -> None:
    """
    Display folder statistics for the given root directory.

    Args:
        root: The root directory to scan
    """
    root_path = Path(root).expanduser().resolve()

    if not root_path.exists() or not root_path.is_dir():
        print(f"Error: {root_path} is not a valid directory.")
        return

    print(f"\nScanning: {root_path}")
    print("-" * 40)

    folder_stats = get_folder_stats(root_path)
    print_tree(root_path, folder_stats)
    print("-" * 40)
