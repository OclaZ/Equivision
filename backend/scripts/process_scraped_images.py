import os
import json
from pathlib import Path
from PIL import Image
import shutil
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data/raw/horse-breeds-scraped"
CLEAN_DIR = BASE_DIR / "data/clean/horse-breeds-processed"
MIN_SIZE = (128, 128)  # Minimum resolution
MIN_KB = 10            # Minimum file size

def process_scraped_images():
    if not DATA_DIR.exists():
        print(f"Directory {DATA_DIR} not found. Run download_dataset_images.py first.")
        return

    # Prepare YOLO
    yolo_model = None
    if YOLO_AVAILABLE:
        print("Loading YOLOv8 for smart cropping...")
        yolo_model = YOLO('yolov8n.pt') 
    else:
        print("YOLO not available. Skipping smart cropping.")

    # Prepare clean directory
    if CLEAN_DIR.exists():
        shutil.rmtree(CLEAN_DIR)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    counts = {"total": 0, "kept": 0, "removed_size": 0, "removed_corrupt": 0, "removed_dim": 0, "removed_dup": 0, "no_horse": 0}
    hashes = set()

    # Iterate through breed folders
    for breed_dir in sorted(DATA_DIR.iterdir()):
        if not breed_dir.is_dir():
            continue
            
        breed_name = breed_dir.name
        print(f"Processing {breed_name}...")
        
        target_breed_dir = CLEAN_DIR / breed_name
        target_breed_dir.mkdir(exist_ok=True)

        # Recurse all images
        image_files = list(breed_dir.glob("*.jpg")) + list(breed_dir.glob("*.jpeg")) + list(breed_dir.glob("*.png")) + list(breed_dir.glob("*.webp"))
        
        for img_path in sorted(image_files):
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
                    # Convert to RGB to avoid mode issues
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                        
                    w, h = img.size
                    if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
                        counts["removed_dim"] += 1
                        continue
                    
                    # Check aspect ratio
                    ratio = max(w, h) / min(w, h)
                    if ratio > 3.0:
                        counts["removed_dim"] += 1
                        continue

                    # 3. Smart Crop with YOLO
                    crop_img = img
                    if yolo_model:
                        results = yolo_model(img, verbose=False)
                        best_crop = None
                        max_area = 0
                        
                        for r in results:
                            for box in r.boxes:
                                if int(box.cls) == 17: # 17 is Horse in COCO dataset
                                    coords = box.xyxy[0].tolist()
                                    area = (coords[2] - coords[0]) * (coords[3] - coords[1])
                                    if area > max_area:
                                        max_area = area
                                        best_crop = coords
                        
                        if best_crop:
                            # Add a small margin (10%) to the crop
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
                            # If strict YOLO is required, uncomment next lines
                            # counts["no_horse"] += 1
                            # continue
                            # For scraped data, we might want to be lenient if YOLO misses but trust the source?
                            # User said "apply yolo filter", implying filtering out bad ones.
                            # So if no horse detected, we skip.
                            counts["no_horse"] += 1
                            continue

                    # 4. Duplicate Detection (on the crop!)
                    thumb = crop_img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
                    pixel_data = list(thumb.getdata())
                    avg = sum(pixel_data) / 64
                    img_hash = "".join(["1" if p > avg else "0" for p in pixel_data])
                    
                    if img_hash in hashes:
                        counts["removed_dup"] += 1
                        continue
                    hashes.add(img_hash)

                    # 5. Save
                    target_path = target_breed_dir / img_path.name
                    target_path = target_path.with_suffix(".jpg")
                    crop_img.save(target_path, "JPEG", quality=95)
                    counts["kept"] += 1

            except Exception as e:
                # print(f"Corrupt image {img_path.name}: {e}")
                counts["removed_corrupt"] += 1

    # Summary
    print("\n" + "="*50)
    print("SCRAPED DATA PROCESSING REPORT")
    print("="*50)
    print(f"Total Images Scanned: {counts['total']}")
    print(f"Kept (Cleaned):     {counts['kept']}")
    print(f"Removed (Small):    {counts['removed_size'] + counts['removed_dim'] + counts['removed_corrupt']}")
    print(f"Removed (No Horse): {counts['no_horse']}")
    print(f"Removed (Duplicate):{counts['removed_dup']}")
    print(f"Clean data saved to: {CLEAN_DIR}")

    # Prune small classes to prevent training errors
    print("\nChecking for insufficient data classes...")
    MIN_IMAGES_FOR_TRAINING = 10
    pruned_count = 0
    for breed_dir in CLEAN_DIR.iterdir():
        if breed_dir.is_dir():
            num_imgs = len(list(breed_dir.glob("*")))
            if num_imgs < MIN_IMAGES_FOR_TRAINING:
                print(f"⚠️  Pruning {breed_dir.name} ({num_imgs} images) - Not enough for training.")
                import shutil
                shutil.rmtree(breed_dir)
                pruned_count += 1
    
    if pruned_count > 0:
        print(f"Removed {pruned_count} breeds with insufficient data (<{MIN_IMAGES_FOR_TRAINING} images).")
    else:
        print("All breeds have sufficient data!")

if __name__ == "__main__":
    process_scraped_images()
```
