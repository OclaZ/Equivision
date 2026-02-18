import pandas as pd
import requests
import logging
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data/processed/unified_horse_data.csv"
OUTPUT_DIR = BASE_DIR / "data/raw/horse-breeds-scraped"
MAX_WORKERS = 5
TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def setup_dirs():
    if OUTPUT_DIR.exists():
        # Optional: Clean up or just append? 
        # For now, let's keep existing to avoid re-downloading if run multiple times
        pass
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_image(row):
    url = row.get('image_url')
    breed = row.get('breed')
    
    if pd.isna(url) or pd.isna(breed) or breed in ["Other", "Unknown"]:
        return None

    try:
        # Create breed directory
        breed_dir = OUTPUT_DIR / breed.replace(" ", "_")
        breed_dir.mkdir(exist_ok=True)
        
        # Hash URL for unique filename
        img_hash = hashlib.md5(url.encode()).hexdigest()
        file_path = breed_dir / f"{img_hash}.jpg"
        
        if file_path.exists():
            return "skipped"

        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            return "downloaded"
        else:
            return "failed"
            
    except Exception as e:
        with open("download_failures.log", "a") as log:
            log.write(f"{url}: {str(e)}\n")
        return "failed"

def main():
    if not DATA_FILE.exists():
        logger.error(f"Data file {DATA_FILE} not found!")
        return

    logger.info(f"Reading {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    
    # Filter valid rows
    valid_rows = df.dropna(subset=['image_url', 'breed'])
    valid_rows = valid_rows[~valid_rows['breed'].isin(["Other", "Unknown"])]
    
    logger.info(f"Found {len(valid_rows)} images to process for {len(valid_rows['breed'].unique())} breeds.")
    
    records = valid_rows.to_dict('records')
    
    success = 0
    skipped = 0
    failed = 0
    
    logger.info("Starting download...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_image, row): row for row in records}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result == "downloaded":
                success += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
                
            if i % 100 == 0:
                print(f"Progress: {i}/{len(records)} | Success: {success} | Skipped: {skipped} | Failed: {failed}", end='\r')

    print(f"\nDownload Complete!")
    print(f"Success: {success}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    # Verify breed counts
    print("\nBreed Counts (Downloaded):")
    for breed_dir in OUTPUT_DIR.iterdir():
        if breed_dir.is_dir():
            count = len(list(breed_dir.glob("*.jpg")))
            print(f"{breed_dir.name}: {count}")

if __name__ == "__main__":
    setup_dirs()
    main()
