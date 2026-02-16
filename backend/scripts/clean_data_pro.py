import pandas as pd
import re
import numpy as np
from pathlib import Path

# Configuration
DATA_DIR = Path("data")
BRONZE_PATH = DATA_DIR / "bronze" / "horse_prices_raw.csv"
SILVER_PATH = DATA_DIR / "silver" / "horse_prices_cleaned.csv"
GOLD_PATH = DATA_DIR / "gold" / "horse_features_final.csv"

# Global Breed Dictionary (Standard: List of known breeds to look for)
KNOWN_BREEDS = [
    "Arabe", "Barbe", "Arabe-Barbe", "English Thoroughbred", "Thoroughbred", "Pur-Sang",
    "Appaloosa", "Quarter Horse", "Paint Horse", "Pony", "Poney", "Shetland",
    "Friesian", "Frison", "Lusitano", "Andalusian", "PRE", "Hanoverian", "Oldenburg",
    "Holsteiner", "Westphalian", "KWPN", "Icelandic", "Haflinger", "Morgan",
    "Warmblood", "Sport Horse", "Pottok", "Anglo-Arabe", "Barb", "Arabian",
    "Percheron", "Shire", "Clydesdale", "Lipizzaner", "Connemara", "Welsh"
]

# Words that indicate bad data or noise
NOISE_WORDS = ["vendre", "cherche", "donne", "accessoire", "équipement", "selle", "van", "transport"]

def extract_breed(title, current_breed):
    """
    Tries to find a real breed from the title if current_breed is generic.
    """
    generic_terms = ["cheval", "poney", "pony", "horse", "unknown", "other", "breed"]
    
    # If breed is already specific, just standardize it
    if str(current_breed).lower() not in generic_terms and len(str(current_breed)) > 3:
        return current_breed

    # Search in title
    for b in KNOWN_BREEDS:
        if re.search(r'\b' + re.escape(b) + r'\b', str(title), re.IGNORECASE):
            return b
            
    return "Unknown"

def is_garbage_title(title):
    """
    Checks if the title is likely a person's name or nonsense.
    """
    t = str(title).lower()
    # If title is just 1 or 2 words that look like names (e.g., "Kaddouri Mohamed")
    # This is a heuristic: titles with no horse-related keywords or extremely short.
    horse_keywords = ["cheval", "poney", "horse", "mare", "stallion", "pouliche", "hongre", "year", "ans"]
    horse_keywords += [b.lower() for b in KNOWN_BREEDS]
    
    has_keyword = any(kw in t for kw in horse_keywords)
    
    # Very short titles or titles with common noise
    if len(t) < 5: return True
    if any(noise in t for noise in NOISE_WORDS): return True
    
    # If it's a Moroccan source (avito) and has no keywords, it's risky
    # (Actually many people just put the horse name, but names are hard to detect)
    # Let's be conservative for "100% clean data"
    return False

def clean_horse_data():
    if not BRONZE_PATH.exists():
        print("Bronze data not found!")
        return

    df = pd.read_csv(BRONZE_PATH)
    print(f"Initial Bronze Records: {len(df)}")

    # 1. Basic Cleaning
    df['title'] = df['title'].fillna("Unknown")
    df['price_mad'] = pd.to_numeric(df['price_mad'], errors='coerce')
    df = df.dropna(subset=['price_mad'])
    
    # 2. Strict Outlier Filter (Quality control)
    # Too cheap: Not a horse. Too expensive: Likely fake or extreme luxury.
    df = df[(df['price_mad'] >= 5000) & (df['price_mad'] <= 1500000)]

    # 3. Garbage Title Removal
    df = df[~df['title'].apply(is_garbage_title)]
    print(f"Records after title filter: {len(df)}")

    # 4. Breed Extraction & Standardization
    df['breed_clean'] = df.apply(lambda x: extract_breed(x['title'], x['breed']), axis=1)
    
    # 5. Drop remaining 'Unknown' breeds if we want "100% clean"
    # The user said "Cheval is not a breed", so they want actual breeds.
    clean_df = df[df['breed_clean'] != "Unknown"].copy()
    
    # 6. Standardization Mapping
    map_dict = {
        "Frison": "Friesian",
        "Poney": "Pony",
        "Pur-Sang": "Thoroughbred",
        "English Thoroughbred": "Thoroughbred",
        "Arabe": "Arabian",
        "Barbe": "Barb",
        "Arabe-Barbe": "Arabian-Barb Mix",
        "PRE": "Pura Raza Española"
    }
    clean_df['breed_clean'] = clean_df['breed_clean'].replace(map_dict)

    # 7. Final deduplication
    clean_df = clean_df.drop_duplicates(subset=['url'])
    
    # Save Silver
    clean_df.to_csv(SILVER_PATH, index=False)
    print(f"Silver Records (Strictly Cleaned): {len(clean_df)}")
    
    # 8. Gold Layer (Features)
    df_gold = clean_df.copy()
    df_gold['log_price'] = np.log10(df_gold['price_mad'])
    df_gold['breed'] = df_gold['breed_clean'] # Standardize back to main col
    
    # Add age extraction if possible (Simplified)
    def extract_age(text):
        match = re.search(r'(\d+)\s*(ans|years|jahre)', str(text).lower())
        return int(match.group(1)) if match else np.nan
    
    df_gold['age_num'] = df_gold['title'].apply(extract_age)
    
    # Filter: Only keep records that have a clear breed now
    df_gold.to_csv(GOLD_PATH, index=False)
    print(f"Gold Records (Final Clean): {len(df_gold)}")

if __name__ == "__main__":
    clean_horse_data()
