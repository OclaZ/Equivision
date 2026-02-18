import os
import json
import hashlib
from pathlib import Path
from PIL import Image
import shutil

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: 'ultralytics' not installed. YOLO smart cropping will be disabled.")

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data/raw/horse-breeds-scraped"
LEGACY_DIR = BASE_DIR / "data/raw/horse-breeds"
CLEAN_DIR = BASE_DIR / "data/clean/horse-breeds-processed"
MIN_SIZE = (128, 128)  # Minimum resolution
MIN_KB = 10            # Minimum file size

def process_single_image(img_path, target_dir, counts, yolo_model):
    counts["total"] += 1
    
    # 1. Check file size
    if img_path.stat().st_size < MIN_KB * 1024:
        counts["removed_size"] += 1
        return

    try:
        with Image.open(img_path) as img:
            # 2. Check dimensions & Integrity
            img.verify() 
        
        with Image.open(img_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            w, h = img.size
            if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
                counts["removed_dim"] += 1
                return
            
            # Aspect ratio check
            ratio = max(w, h) / min(w, h)
            if ratio > 3.0:
                counts["removed_dim"] += 1
                return

            # 3. Smart Crop with YOLO
            crop_img = img
            if yolo_model:
                results = yolo_model(img, verbose=False)
                best_crop = None
                max_area = 0
                
                for r in results:
                    for box in r.boxes:
                        if int(box.cls) == 17: # 17 is Horse
                            coords = box.xyxy[0].tolist()
                            area = (coords[2] - coords[0]) * (coords[3] - coords[1])
                            if area > max_area:
                                max_area = area
                                best_crop = coords
                
                if best_crop:
                    # Margin 10%
                    x1, y1, x2, y2 = best_crop
                    mw = (x2 - x1) * 0.1
                    mh = (y2 - y1) * 0.1
                    crop_img = img.crop((
                        max(0, x1 - mw), 
                        max(0, y1 - mh), 
                        min(img.width, x2 + mw), 
                        min(img.height, y2 + mh)
                    ))
                else:
                    counts["no_horse"] += 1
                    return # Skip if no horse detected

            # 4. Duplicate Detection (MD5 of content)
            img_hash = hashlib.md5(crop_img.tobytes()).hexdigest()
            save_path = target_dir / f"{img_hash}.jpg"
            
            if save_path.exists():
                counts["removed_dup"] += 1
                return

            # Save
            crop_img.save(save_path, "JPEG", quality=95)
            counts["kept"] += 1
            
    except Exception as e:
        # print(f"Corrupt image {img_path.name}: {e}")
        counts["removed_corrupt"] += 1

def process_scraped_images():
    # Prepare clean directory
    if CLEAN_DIR.exists():
        shutil.rmtree(CLEAN_DIR)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    # Load YOLO
    yolo_model = None
    if YOLO_AVAILABLE:
        print("Loading YOLOv8 for smart cropping...")
        try:
            yolo_model = YOLO("yolov8n.pt")
        except Exception as e:
            print(f"Failed to load YOLO: {e}")

    counts = {"total": 0, "kept": 0, "removed_size": 0, "removed_corrupt": 0, 
              "removed_dim": 0, "removed_dup": 0, "no_horse": 0}

    # --- PHASE 1: Process Scraped Data ---
    print("\n--- Processing Scraped Data ---")
    if DATA_DIR.exists():
        for breed_dir in sorted(DATA_DIR.iterdir()):
            if not breed_dir.is_dir(): continue
            
            breed_name = breed_dir.name
            print(f"Processing {breed_name}...")
            
            target_breed_dir = CLEAN_DIR / breed_name
            target_breed_dir.mkdir(exist_ok=True)
    
            # Recurse all images
            image_files = list(breed_dir.glob("*.jpg")) + list(breed_dir.glob("*.jpeg")) + \
                          list(breed_dir.glob("*.png")) + list(breed_dir.glob("*.webp"))
            
            for img_path in sorted(image_files):
                process_single_image(img_path, target_breed_dir, counts, yolo_model)
    else:
        print(f"Scraped data directory not found at {DATA_DIR}")

    # --- PHASE 2: Process Legacy Data ---
    print("\n--- Processing Legacy Data ---")
    if LEGACY_DIR.exists():
        labels_file = LEGACY_DIR / "labels.json"
        if labels_file.exists():
            with open(labels_file, 'r') as f:
                legacy_map = json.load(f)
            
            print(f"Found legacy dataset map: {legacy_map}")
            legacy_found = 0
            
            legacy_files = list(LEGACY_DIR.glob("*.jpg")) + list(LEGACY_DIR.glob("*.jpeg")) + list(LEGACY_DIR.glob("*.png"))
            
            for img_path in sorted(legacy_files):
                # Parse filename: "11_065.jpg" -> "11" -> "Lusitano"
                parts = img_path.stem.split('_')
                if len(parts) >= 2:
                    breed_id = parts[0]
                    if breed_id in legacy_map:
                        breed_name = legacy_map[breed_id].replace(" ", "_") # Normalize
                        target_breed_dir = CLEAN_DIR / breed_name
                        target_breed_dir.mkdir(exist_ok=True)
                        process_single_image(img_path, target_breed_dir, counts, yolo_model)
                        legacy_found += 1
            print(f"Processed {legacy_found} legacy images.")
        else:
            print("Legacy labels.json not found.")
    else:
        print("Legacy data directory not found.")

    # Summary
    print("\n" + "="*50)
    print("SCRAPED & LEGACY DATA REPORT")
    print("="*50)
    print(f"Total Images Scanned: {counts['total']}")
    print(f"Kept (Cleaned):     {counts['kept']}")
    print(f"Removed (Small):    {counts['removed_size'] + counts['removed_dim']}")
    print(f"Removed (Corrupt):  {counts['removed_corrupt']}")
    print(f"Removed (No Horse): {counts['no_horse']}")
    print(f"Removed (Duplicate):{counts['removed_dup']}")
    print(f"Clean data saved to: {CLEAN_DIR}")

    # Prune small classes
    print("\nChecking for insufficient data classes...")
    MIN_IMAGES_FOR_TRAINING = 10
    pruned_count = 0
    for breed_dir in CLEAN_DIR.iterdir():
        if breed_dir.is_dir():
            num_imgs = len(list(breed_dir.glob("*.jpg")))
            if num_imgs < MIN_IMAGES_FOR_TRAINING:
                print(f"⚠️  Pruning {breed_dir.name} ({num_imgs} images) - Not enough.")
                shutil.rmtree(breed_dir)
                pruned_count += 1
    
    if pruned_count > 0:
        print(f"Removed {pruned_count} breeds with insufficient data.")
    else:
        print("All breeds have sufficient data!")

if __name__ == "__main__":
    process_scraped_images()
