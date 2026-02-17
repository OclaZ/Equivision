import os
import json
from pathlib import Path
from PIL import Image
import shutil

# --- CONFIGURATION ---
DATA_DIR = Path("data/raw/horse-breeds")
CLEAN_DIR = Path("data/clean/horse-breeds")
MIN_SIZE = (128, 128)  # Minimum resolution
MIN_KB = 15            # Minimum file size

def clean_vision_data():
    if not DATA_DIR.exists():
        print(f"Directory {DATA_DIR} not found.")
        return

    # Prepare clean directory
    if CLEAN_DIR.exists():
        shutil.rmtree(CLEAN_DIR)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    # Load labels
    labels_path = DATA_DIR / "labels.json"
    label_map = {}
    if labels_path.exists():
        shutil.copy(labels_path, CLEAN_DIR / "labels.json")
        with open(labels_path, 'r') as f:
            label_map = json.load(f)

    counts = {"total": 0, "kept": 0, "removed_size": 0, "removed_corrupt": 0, "removed_dim": 0, "removed_dup": 0}
    hashes = set()

    for img_path in sorted(DATA_DIR.glob("*.*")): # Sort for consistency
        if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
            continue
        
        counts["total"] += 1
        
        # 1. Check file size
        if img_path.stat().st_size < MIN_KB * 1024:
            counts["removed_size"] += 1
            continue

        # 2. Check image integrity and dimensions
        try:
            with Image.open(img_path) as img:
                img.verify() # Verify integrity
            
            with Image.open(img_path) as img:
                w, h = img.size
                if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
                    counts["removed_dim"] += 1
                    continue
                
                # Check aspect ratio
                ratio = max(w, h) / min(w, h)
                if ratio > 3.0:
                    counts["removed_dim"] += 1
                    continue

                # 3. Duplicate Detection
                thumb = img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
                pixel_data = list(thumb.getdata())
                avg = sum(pixel_data) / 64
                img_hash = "".join(["1" if p > avg else "0" for p in pixel_data])
                
                if img_hash in hashes:
                    counts["removed_dup"] += 1
                    continue
                hashes.add(img_hash)

                # 4. Determine Breed Folder
                breed_id = img_path.name.split('_')[0]
                breed_name = label_map.get(breed_id, "Unknown").replace(" ", "_")
                breed_dir = CLEAN_DIR / breed_name
                breed_dir.mkdir(exist_ok=True)

                # 5. Passed all checks! Copy to clean folder
                target_path = breed_dir / img_path.name
                shutil.copy(img_path, target_path)
                counts["kept"] += 1

        except Exception as e:
            print(f"Corrupt image {img_path.name}: {e}")
            counts["removed_corrupt"] += 1

    print("\n" + "="*40)
    print("   VISION DATA CLEANING REPORT")
    print("="*40)
    print(f"Total Images Scanned:  {counts['total']}")
    print(f"Images Kept (Unique):  {counts['kept']}")
    print(f"Removed (Duplicate):   {counts['removed_dup']}")
    print(f"Removed (Small size):  {counts['removed_size']}")
    print(f"Removed (Small dims):  {counts['removed_dim']}")
    print(f"Removed (Corrupt):     {counts['removed_corrupt']}")
    print("="*40)
    print(f"Clean data saved to: {CLEAN_DIR}")

if __name__ == "__main__":
    clean_vision_data()
