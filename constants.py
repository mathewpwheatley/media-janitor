"""Shared constants for media management."""

import sys
from typing import Dict, Set
from dataclasses import dataclass
from typing import TypeAlias

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

Year: TypeAlias = int


@dataclass(frozen=True)
class ThresholdConfig:
    """Configuration for file size and resolution thresholds."""

    label: str
    min_bytes: int
    min_width: int
    min_height: int


# Photo quality thresholds by era
PHOTO_THRESHOLDS: Dict[Year, ThresholdConfig] = {
    1995: ThresholdConfig("Legacy/Thumbnail (Pre-1995)", 2048, 160, 120),
    2000: ThresholdConfig("Legacy Photo (Pre-2000)", 5120, 320, 240),
    2006: ThresholdConfig("Early Digital (Pre-2006)", 51200, 640, 480),
    2012: ThresholdConfig("Point & Shoot (Pre-2012)", 204800, 1024, 768),
    2018: ThresholdConfig("Modern Mobile (Pre-2018)", 512000, 1920, 1080),
    sys.maxsize: ThresholdConfig("High Res/4K (2018+)", 1048576, 3840, 2160),
}

# Video quality thresholds by era
VIDEO_THRESHOLDS: Dict[Year, ThresholdConfig] = {
    1995: ThresholdConfig("Cinepak/Old web (Pre-1995)", 25600, 160, 120),
    2000: ThresholdConfig("Legacy Video (Pre-2000)", 102400, 320, 240),
    2007: ThresholdConfig("DVD/Standard Def (Pre-2007)", 5242880, 720, 480),
    2012: ThresholdConfig("Early HD (Pre-2012)", 20971520, 1280, 720),
    2017: ThresholdConfig("Full HD Standard (Pre-2017)", 52428800, 1920, 1080),
    sys.maxsize: ThresholdConfig("4K Standard (2017+)", 209715200, 3840, 2160),
}
