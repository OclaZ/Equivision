import csv
import math
from pathlib import Path

# Setup paths
DATA_DIR = Path("data")
BRONZE_PATH = DATA_DIR / "bronze" / "horse_prices_raw.csv"
SILVER_PATH = DATA_DIR / "silver" / "horse_prices_cleaned.csv"
GOLD_PATH = DATA_DIR / "gold" / "horse_features_final.csv"

# Known breeds for extraction
KNOWN_BREEDS = ["Arabe", "Barbe", "Arabe-Barbe", "Thoroughbred", "Appaloosa", "Quarter Horse", "Paint Horse", "Pony", "Friesian", "Lusitano", "Andalusian", "PRE", "Hanoverian", "Oldenburg", "Holsteiner", "Westphalian", "KWPN", "Icelandic", "Haflinger"]
GENERIC_BREEDS = ["cheval", "poney", "pony", "horse", "unknown", "other", "breed"]

def get_clean_breed(title, breed):
    b_val = str(breed).lower()
    if b_val not in GENERIC_BREEDS and len(b_val) > 3:
        return breed
    for kb in KNOWN_BREEDS:
        if kb.lower() in str(title).lower():
            return kb
    return "Unknown"

def process_medallion():
    if not BRONZE_PATH.exists():
        print(f"Error: {BRONZE_PATH} not found.")
        return

    # 1. Read Bronze
    raw_data = []
    with open(BRONZE_PATH, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_data.append(row)
    print(f"Bronze Records: {len(raw_data)}")

    # 2. Silver Processing (Cleaning)
    urls_seen = set()
    silver_data = []

    for row in raw_data:
        url = row.get('url')
        if not url or url in urls_seen: continue
        
        title = str(row.get('title', ''))
        # Filter garbage titles and equipment
        if len(title) < 5 or any(x in title.lower() for x in ["équipement", "selle", "accessoire", "vendre", "cherche"]):
            continue

        try:
            price = float(row.get('price_mad', 0))
        except: continue
        
        # Strict price filtering for horses [5,000 - 1,500,000]
        if price < 5000 or price > 1500000: continue
        
        clean_b = get_clean_breed(title, row.get('breed'))
        if clean_b == "Unknown": continue # We only want 100% specific breeds
        
        row['breed'] = clean_b
        urls_seen.add(url)
        silver_data.append(row)
            
    # Write Silver
    if silver_data:
        with open(SILVER_PATH, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=silver_data[0].keys())
            writer.writeheader()
            writer.writerows(silver_data)
    print(f"Silver Records (Cleaned): {len(silver_data)}")

    # 3. Gold Processing (Feature Engineering)
    breed_counts = {}
    for row in silver_data:
        b = row.get('breed', 'Unknown')
        breed_counts[b] = breed_counts.get(b, 0) + 1
        
    gold_data = []
    for row in silver_data:
        new_row = row.copy()
        # Log Price
        price = float(row['price_mad'])
        new_row['log_price'] = math.log10(price)
        
        # Breed simplification (Threshold 10)
        breed = row.get('breed', 'Unknown')
        if breed_counts.get(breed, 0) < 10:
            new_row['breed_simplified'] = 'Other'
        else:
            new_row['breed_simplified'] = breed
            
        # Location tag
        source = row.get('source', '')
        new_row['is_morocco'] = 1 if ('.ma' in source or row.get('location') == 'Morocco') else 0
        
        gold_data.append(new_row)
        
    # Write Gold
    if gold_data:
        fieldnames = list(gold_data[0].keys())
        with open(GOLD_PATH, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(gold_data)
    print(f"Gold Records (Final): {len(gold_data)}")

if __name__ == "__main__":
    process_medallion()
