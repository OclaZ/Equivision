import pandas as pd
import re
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
DATA_DIR = Path("data")
BRONZE_PATH = DATA_DIR / "bronze" / "horse_prices_raw.csv"
SILVER_PATH = DATA_DIR / "silver" / "horse_prices_cleaned.csv"
GOLD_PATH = DATA_DIR / "gold" / "horse_features_final.csv"

# Current Year for Age Calculation
CURRENT_YEAR = datetime.now().year

# --- KNOWLEDGE BASES ---
BREED_MAP = {
    # Arabs
    "arabian": "Arabian", "arabe": "Arabian", "ox": "Arabian", "pur sang arabe": "Arabian",
    # Barbs
    "barb": "Barb", "barbe": "Barb", 
    "arabian-barb": "Arabian-Barb Mix", "arabe-barbe": "Arabian-Barb Mix", "arabe barbe": "Arabian-Barb Mix",
    # Thoroughbreds
    "thoroughbred": "Thoroughbred", "pur sang": "Thoroughbred", "ps": "Thoroughbred", "anglo": "Anglo-Arabian",
    # Warmbloods
    "friesian": "Friesian", "frison": "Friesian", 
    "andalusian": "Andalusian", "pre": "Andalusian", "pura raza española": "Andalusian", "espagnol": "Andalusian",
    "lusitano": "Lusitano", "lusitanien": "Lusitano", "psl": "Lusitano",
    "hanoverian": "Hanoverian", "hanovre": "Hanoverian",
    "holsteiner": "Holsteiner", "holstein": "Holsteiner",
    "kwpn": "KWPN", "dutch warmblood": "KWPN",
    "sf": "Selle Français", "selle francais": "Selle Français", "selle français": "Selle Français",
    "oldenburg": "Oldenburg", "westphalian": "Westphalian",
    # Drafts
    "percheron": "Percheron", "shire": "Shire", "clydesdale": "Clydesdale", "breton": "Breton",
    "comtois": "Comtois", "boulonnais": "Boulonnais",
    # Ponies
    "shetland": "Shetland", "welsh": "Welsh", "connemara": "Connemara", "haflinger": "Haflinger", 
    "fjords": "Fjord", "pottok": "Pottok", "pony": "Pony", "poney": "Pony"
}

GENDER_MAP = {
    "male": "Stallion", "mâle": "Stallion", "etalon": "Stallion", "étalon": "Stallion", "stallion": "Stallion", "entier": "Stallion",
    "female": "Mare", "femelle": "Mare", "jument": "Mare", "mare": "Mare", "poulinière": "Mare",
    "gelding": "Gelding", "hongre": "Gelding"
}

NOISE_WORDS = ["vendre", "cherche", "donne", "camion", "van", "transport", "paille", "foin", "selle", "equipement", "botte"]

def clean_text(text):
    if not isinstance(text, str): return ""
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()

def extract_breed_smart(text):
    text = clean_text(text)
    # Check specific compound breeds first (Arabe-Barbe)
    if "arabe barbe" in text or "arabe-barbe" in text:
        return "Arabian-Barb Mix"
    
    # Check single words
    for key, value in BREED_MAP.items():
        # Look for word boundary to avoid partial matches (e.g. "barbe" inside "barbecue" - unlikely but robust)
        if re.search(r'\b' + re.escape(key) + r'\b', text):
            return value
    return "Unknown"

def extract_gender(text):
    text = clean_text(text)
    for key, value in GENDER_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text):
            return value
    return "Unknown"

def extract_age_smart(text):
    text = clean_text(text)
    
    # Pattern 1: Explicit "X years/ans"
    match = re.search(r'(\d{1,2})\s*(ans|an|years|yrs)', text)
    if match:
        age = int(match.group(1))
        if 0 <= age <= 35: return age

    # Pattern 2: Birth Year "2015", "né en 2018"
    # Search for years explicitly between 1990 and Current Year
    matches = re.findall(r'\b(199[0-9]|20[0-2][0-9])\b', text)
    if matches:
        # Take the most recent year found (likely the birth year)
        birth_year = int(max(matches)) 
        return CURRENT_YEAR - birth_year

    return np.nan

def extract_height(text):
    text = clean_text(text)
    # Pattern: 1m65, 1.65m, 165cm
    match = re.search(r'(\d)[m\.](\d{2})', text)
    if match:
        return int(match.group(1)) * 100 + int(match.group(2)) # Returns cm
    
    match_cm = re.search(r'(\d{3})\s*cm', text)
    if match_cm:
        return int(match_cm.group(1))
        
    return np.nan

def clean_data_pro():
    if not BRONZE_PATH.exists():
        print(f"❌ Input file not found: {BRONZE_PATH}")
        return

    print("🚀 Starting God-Tier Data Cleaning...")
    df = pd.read_csv(BRONZE_PATH)
    print(f"   Initial Records: {len(df)}")
    
    # Combine Title + Description for better extraction
    # (Assuming description col exists, if not create empty)
    if 'description' not in df.columns:
        df['description'] = ""
    
    df['full_text'] = df['title'].fillna("") + " " + df['description'].fillna("")
    
    # 1. Price Filtering
    df['price_mad'] = pd.to_numeric(df['price_mad'], errors='coerce')
    df = df.dropna(subset=['price_mad'])
    df = df[(df['price_mad'] > 1000) & (df['price_mad'] < 2000000)] # Remove < 1000 (likely fake/accessories)
    print(f"   After Price Filter: {len(df)}")

    # 2. Garbage Removal
    mask_garbage = df['title'].apply(lambda x: any(w in str(x).lower() for w in NOISE_WORDS))
    df = df[~mask_garbage]
    print(f"   After Garbage Removal: {len(df)}")

    # 3. Feature Extraction
    print("   Extracting Features (Breed, Age, Gender, Height)...")
    df['breed_clean'] = df['full_text'].apply(extract_breed_smart)
    df['gender_clean'] = df['full_text'].apply(extract_gender)
    df['age_clean'] = df['full_text'].apply(extract_age_smart)
    df['height_cm'] = df['full_text'].apply(extract_height)

    # 4. Filter Unknown Breeds (Crucial for pricing model)
    df_silver = df[df['breed_clean'] != "Unknown"].copy()
    print(f"   After Breed Filter (Silver): {len(df_silver)}")
    
    # Save Silver
    SILVER_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_silver.to_csv(SILVER_PATH, index=False)
    
    # 5. Create Gold Dataset (Ready for ML)
    # Fill missing age with mean per breed? Or drop? 
    # For now, let's keep them but mark as unknown for the ML model to handle or impute later.
    df_gold = df_silver.copy()
    
    # Select columns
    cols = ['title', 'price_mad', 'breed_clean', 'gender_clean', 'age_clean', 'height_cm', 'url', 'location']
    final_cols = [c for c in cols if c in df_gold.columns]
    df_gold = df_gold[final_cols]
    
    # Rename for consistency
    df_gold = df_gold.rename(columns={
        'breed_clean': 'breed',
        'gender_clean': 'gender',
        'age_clean': 'age'
    })

    # Drop entries with NO detailed info? 
    # Actually, keep them if they have at least breed + price.
    
    GOLD_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_gold.to_csv(GOLD_PATH, index=False)
    print(f"✅ FINAL GOLD DATASET SAVED: {len(df_gold)} records")
    print(f"   Path: {GOLD_PATH}")

if __name__ == "__main__":
    clean_data_pro()
