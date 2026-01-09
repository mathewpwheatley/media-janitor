"""Command-line interface for Media Manager."""

import argparse
import os
import sys

from __init__ import __version__
from organize import organize
from flatten import flatten_folder
from count import display_count
from dedupe import dedupe
from fix_dates import fix_dates
from health_check import health_check


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="media-janitor",
        description="A CLI tool for organizing photo and video libraries",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Organize command
    organize_parser = subparsers.add_parser(
        "organize",
        help="Organize media files into dated folder structures",
        description="Sort folders from source directory into dated year/month structure",
    )
    organize_parser.add_argument(
        "source",
        help="Source directory to scan for media folders",
    )
    organize_parser.add_argument(
        "photo_dest",
        metavar="photo-dest",
        help="Destination directory for photo folders",
    )
    organize_parser.add_argument(
        "video_dest",
        metavar="video-dest",
        help="Destination directory for video folders",
    )
    organize_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes (default: True)",
    )
    organize_parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Run in batch mode without prompting for actions",
    )

    # Flatten command
    flatten_parser = subparsers.add_parser(
        "flatten",
        help="Flatten nested folder structures",
        description="Flatten all files from nested folders into a single directory",
    )
    flatten_parser.add_argument(
        "source",
        help="Source folder to flatten",
    )
    flatten_parser.add_argument(
        "target",
        nargs="?",
        help="Target folder for flattened files (default: <source>/flattened)",
    )
    flatten_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Count command
    count_parser = subparsers.add_parser(
        "count",
        help="Display folder statistics",
        description="Analyze and display folder statistics in a tree view",
    )
    count_parser.add_argument(
        "root",
        help="Root directory to scan",
    )

    # Dedupe command
    dedupe_parser = subparsers.add_parser(
        "dedupe",
        help="Find and remove duplicate files",
        description="Scan for duplicate files using content hash and optionally remove them",
    )
    dedupe_parser.add_argument(
        "root",
        help="Root directory to scan for duplicates",
    )
    dedupe_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Fix-dates command
    fix_dates_parser = subparsers.add_parser(
        "fix-dates",
        help="Fix file dates using EXIF or filename patterns",
        description="Correct file modification dates using EXIF metadata or filename patterns",
    )
    fix_dates_parser.add_argument(
        "root",
        help="Root directory to scan",
    )
    fix_dates_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    # Health-check command
    health_check_parser = subparsers.add_parser(
        "health-check",
        help="Check media library health",
        description=f"Scan for corrupted files, ghost files, and thumbnails with date-based thresholds",
    )
    group = health_check_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "root",
        nargs="?",
        help="Root directory to scan",
    )
    group.add_argument(
        "--thresholds",
        action="store_true",
        help="Prints date-based thresholds for reference",
    )
    health_check_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes ",
    )
    health_check_parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Run in batch mode without prompting for actions",
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "organize":
            print(f"DEBUG: {args}")
            organize(
                source=args.source,
                photo_dest=args.photo_dest,
                video_dest=args.video_dest,
                dry_run=args.dry_run,
                interactive=(not args.no_interactive),
            )

        elif args.command == "flatten":
            target = (
                args.target if args.target else os.path.join(args.source, "flattened")
            )
            flatten_folder(
                source=args.source,
                target=target,
                dry_run=args.dry_run,
            )

        elif args.command == "count":
            display_count(root=args.root)

        elif args.command == "dedupe":
            dedupe(
                root=args.root,
                dry_run=args.dry_run,
            )

        elif args.command == "fix-dates":
            fix_dates(
                root=args.root,
                dry_run=args.dry_run,
            )

        elif args.command == "health-check":
            health_check(
                root=args.root,
                dry_run=args.dry_run,
                interactive=not args.no_interactive,
                display_thresholds=args.thresholds,
            )

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
