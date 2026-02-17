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
DATA_DIR = Path("data/raw/horse-breeds")
CLEAN_DIR = Path("data/clean/horse-breeds")
MIN_SIZE = (128, 128)  # Minimum resolution
MIN_KB = 15            # Minimum file size

def clean_vision_data():
    if not DATA_DIR.exists():
        print(f"Directory {DATA_DIR} not found.")
        return

    # Prepare YOLO
    yolo_model = None
    if YOLO_AVAILABLE:
        print("Loading YOLOv8 for smart cropping...")
        yolo_model = YOLO('yolov8n.pt') 

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

    counts = {"total": 0, "kept": 0, "removed_size": 0, "removed_corrupt": 0, "removed_dim": 0, "removed_dup": 0, "no_horse": 0}
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

                # 5. Determine Breed Folder
                breed_id = img_path.name.split('_')[0]
                breed_name = label_map.get(breed_id, "Unknown").replace(" ", "_")
                breed_dir = CLEAN_DIR / breed_name
                breed_dir.mkdir(exist_ok=True)

                # 6. Save the (possibly cropped) image
                if crop_img.mode in ("RGBA", "P"):
                    crop_img = crop_img.convert("RGB")
                    
                target_path = breed_dir / img_path.name
                # Ensure extension is .jpg
                target_path = target_path.with_suffix(".jpg")
                crop_img.save(target_path, "JPEG", quality=95)
                counts["kept"] += 1

        except Exception as e:
            print(f"Corrupt image {img_path.name}: {e}")
            counts["removed_corrupt"] += 1

    print("\n" + "="*40)
    print("   VISION DATA CLEANING REPORT (YOLO EDITION)")
    print("="*40)
    print(f"Total Images Scanned:  {counts['total']}")
    print(f"Images Kept (Unique):  {counts['kept']}")
    print(f"Removed (No Horse):    {counts.get('no_horse', 0)}")
    print(f"Removed (Duplicate):   {counts['removed_dup']}")
    print(f"Removed (Small size):  {counts['removed_size']}")
    print(f"Removed (Small dims):  {counts['removed_dim']}")
    print(f"Removed (Corrupt):     {counts['removed_corrupt']}")
    print("="*40)
    print(f"Clean data saved to: {CLEAN_DIR}")

if __name__ == "__main__":
    clean_vision_data()
