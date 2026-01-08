import os
import shutil
from collections import Counter
from datetime import datetime
import exifread

ROOT = "/Volumes/Family/Photos"
PHOTO_ROOT = "/Volumes/Family/Photos"
VIDEO_ROOT = "/Volumes/Family/Videos"

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".nef", ".cr2", ".arw"}
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".mts"}

DRY_RUN = True
INTERACTIVE = True

def get_photo_date(path):
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
            date_tag = tags.get("EXIF DateTimeOriginal")
            if date_tag:
                return datetime.strptime(str(date_tag), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return datetime.fromtimestamp(os.path.getmtime(path))

def classify_folder(folder_path):
    dates = []
    photo_count = 0
    video_count = 0
    for root, _, files in os.walk(folder_path):
        for name in files:
            ext = os.path.splitext(name.lower())[1]
            path = os.path.join(root, name)
            if ext in PHOTO_EXT:
                photo_count += 1
                dates.append(get_photo_date(path))
            elif ext in VIDEO_EXT:
                video_count += 1
                dates.append(datetime.fromtimestamp(os.path.getmtime(path)))
    return dates, photo_count, video_count

def choose_target_date(dates):
    counts = Counter((d.year, d.month) for d in dates)
    return counts.most_common(1)[0][0]

def prompt_folder_name(name, year, month, count):
    print(f"\nFolder: {name}")
    print(f"Target: {year}/{month:02d}/")
    print(f"Files: {count}")

    choice = input("[Enter]=accept | r=rename | u=ungroup (move files individually) | s=skip folder: ").strip().lower()

    if choice == "r":
        new_name = input("New folder name: ").strip()
        return new_name or name
    elif choice == "u":
        return "UNGROUP"
    elif choice == "s":
        return "SKIP"
    return name

def move_individual_files(src_folder, photo_root, video_root):
    """Moves files out of the folder individually into YYYY/MM/ structure."""
    for root, _, files in os.walk(src_folder):
        for name in files:
            if name.startswith('.'): continue # Ignore hidden files like .DS_Store

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
                print(f"  [!] Already Exists: {name}")
                continue

            if DRY_RUN:
                print(f"  [DRY RUN] Individual file: {name} -> {dest_dir}")
            else:
                print(f"  Moving file: {name}...")
                shutil.move(path, dest_path)

    # Cleanup empty folders
    if not DRY_RUN:
        try:
            # Only remove if the original folder is now empty
            if not os.listdir(src_folder):
                os.rmdir(src_folder)
        except Exception:
            pass

def move_folder(src, dest_root, year, month, name):
    dest_dir = os.path.join(dest_root, str(year), f"{month:02d}")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, name)

    if os.path.exists(dest_path):
        print(f"  [!] Folder already exists: {dest_path}")
        return

    if DRY_RUN:
        print(f"  [DRY RUN] Entire folder: {src} -> {dest_path}")
    else:
        print(f"  Moving folder: {name} -> {year}/{month:02d}/")
        shutil.move(src, dest_path)

# --- Main Execution ---

for entry in os.scandir(ROOT):
    if not entry.is_dir():
        continue

    # Skip already organized year folders (optional check to prevent infinite loops)
    if entry.name.isdigit() and len(entry.name) == 4:
        continue

    folder = entry.path
    folder_name = entry.name

    dates, photos, videos = classify_folder(folder)
    if not dates:
        continue

    year, month = choose_target_date(dates)
    target_root = PHOTO_ROOT if photos >= videos else VIDEO_ROOT

    final_name = folder_name
    if INTERACTIVE:
        final_name = prompt_folder_name(folder_name, year, month, photos + videos)

    if final_name == "SKIP":
        print(f"Skipping {folder_name}...")
        continue
    elif final_name == "UNGROUP":
        print(f"Ungrouping {folder_name}...")
        move_individual_files(folder, PHOTO_ROOT, VIDEO_ROOT)
    else:
        move_folder(folder, target_root, year, month, final_name)
