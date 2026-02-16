import pandas as pd
import re
import numpy as np
from pathlib import Path

# Paths
DATA_DIR = Path("data")
BRONZE_PATH = DATA_DIR / "bronze" / "horse_prices_raw.csv"
SILVER_PATH = DATA_DIR / "silver" / "horse_prices_cleaned.csv"
GOLD_PATH = DATA_DIR / "gold" / "horse_features_final.csv"

# 1. BREEDS IN MOROCCAN CLASSIFIEDS (Enhanced Regex)
BREED_KEYWORDS = [
    (r"(pure? sang arabe|pur sang arabe|arabe pure|arabe)", "Arabian"),
    (r"(arabe-barbe|arabe barbe|arabo barbe|arabo-barbe|arabo)", "Arabian-Barb Mix"),
    (r"(barbe|barb)", "Barb"),
    (r"(anglo arabe|anglo-arab|anglo)", "Anglo-Arabian"),
    (r"(pur sang anglais|thoroughbred|ps anglais)", "Thoroughbred"),
    (r"(frison|friesian|frisonne)", "Friesian"),
    (r"(poney|pony|ponette)", "Pony"),
    (r"(pre|andalou|andalusian|espagnol)", "Andalusian"),
    (r"(quarter horse|aqh)", "Quarter Horse"),
    (r"(lusitano|lusitanien)", "Lusitano"),
]

NON_HORSE = [r"âne", r"chiot", r"chien", r"selle", r"accessoire", r"équipement", r"van", r"transport", r"pomeranie"]
PEOPLE_NAMES = [r"\bمحمد\b", r"\bkaddouri\b", r"\badil\b", r"\bimrane\b", r"\bfahd\b", r"\bmohamed\b", r"\byoussef\b", r"\byounes\b", r"\bhajar\b", r"\bomar\b", r"\baziz\b"]

def extract_specific_breed(title, breed):
    title_low = str(title).lower()
    breed_low = str(breed).lower()
    full_text = f"{title_low} {breed_low}"
    
    # 1. Search semantic keywords (highest precision)
    for pattern, normalized in BREED_KEYWORDS:
        if re.search(pattern, full_text):
            return normalized
            
    # 2. Check if the breed is already specific and valid (e.g. from ehorses)
    if breed_low not in ["cheval", "poney", "pony", "horse", "unknown", "other", "breed", "nan", ""]:
        return breed # Keep valid specific breeds from international sources
        
    return "Rejected"

def is_garbage(title):
    t = str(title).lower()
    # Logic: if title doesn't contain horse keywords BUT contains person name or equipment
    if any(re.search(p, t) for p in PEOPLE_NAMES): return True
    if any(re.search(p, t) for p in NON_HORSE): return True
    if len(t.strip()) < 3: return True
    return False

def clean_data():
    if not BRONZE_PATH.exists(): return
    df = pd.read_csv(BRONZE_PATH)
    
    # Pre-clean
    df = df.dropna(subset=['price_mad', 'title'])
    df['price_mad'] = pd.to_numeric(df['price_mad'], errors='coerce')
    df = df.drop_duplicates(subset=['url'])
    
    # FILTER: Price range
    df = df[(df['price_mad'] >= 5000) & (df['price_mad'] <= 2500000)]
    
    # FILTER: Remove metadata noise (dog/names)
    df = df[~df['title'].apply(is_garbage)]
    
    # FILTER: Specific Breed ONLY (Pure Sang Arabe, Barb, etc.)
    df['breed_clean'] = df.apply(lambda x: extract_specific_breed(x['title'], x['breed']), axis=1)
    df = df[df['breed_clean'] != "Rejected"]
    
    # Final mappings
    df['breed'] = df['breed_clean']
    df['log_price'] = np.log10(df['price_mad'])
    df['is_morocco'] = df['source'].str.contains('avito|animo|animalsouk|elevageaumaroc').astype(int)
    
    df.to_csv(SILVER_PATH, index=False)
    df.to_csv(GOLD_PATH, index=False)
    print(f"Purification finished. Gold: {len(df)}")
    print(f"Sources: {df['source'].value_counts().to_dict()}")

if __name__ == "__main__":
    clean_data()
