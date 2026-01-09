"""Shared constants, types, and utilities for media management."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Set

# File extension sets
PHOTO_EXT: Set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".tif",
    ".tiff",
    ".nef",
    ".cr2",
    ".arw",
}

VIDEO_EXT: Set[str] = {".mp4", ".mov", ".avi", ".mkv", ".mts"}


class FolderAction(Enum):
    """Actions that can be taken on a folder during organization."""

    ACCEPT = auto()
    RENAME = auto()
    UNGROUP = auto()
    SKIP = auto()


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
