import pandas as pd
import numpy as np
import random
import re
import sys
from pathlib import Path

# Setup encoding for broad character support
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
DATA_DIR = Path("data")
BRONZE_PATH = DATA_DIR / "bronze" / "horse_prices_raw.csv"
SILVER_PATH = DATA_DIR / "silver" / "horse_prices_cleaned.csv"
GOLD_PATH = DATA_DIR / "gold" / "horse_features_final.csv"

# --- CONFIGURATION ---
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

MOROCCAN_CITIES = ["Casablanca", "Rabat", "Marrakech", "Agadir", "Fes", "Tangier", "El Jadida", "Meknes", "Beni Mellal", "Settat"]

# --- CORE FUNCTIONS ---

def extract_breed(title, breed):
    title_low = str(title).lower()
    breed_low = str(breed).lower()
    full_text = f"{title_low} {breed_low}"
    for pattern, normalized in BREED_KEYWORDS:
        if re.search(pattern, full_text):
            return normalized
    if breed_low not in ["cheval", "poney", "pony", "horse", "unknown", "other", "breed", "nan", ""]:
        return breed
    return "Rejected"

def extract_age(title):
    match = re.search(r'(\d+)\s*(ans|years|jahre|mois)', str(title).lower())
    if match:
        val = int(match.group(1))
        if "mois" in match.group(0):
            return round(val / 12, 1)
        return float(val)
    return np.nan

def generate_synthetic_moroccan(breed, n=150):
    data = []
    base_prices = {
        "Arabian": (15000, 450000, 95000), 
        "Barb": (12000, 200000, 55000),
        "Arabian-Barb Mix": (9000, 150000, 40000)
    }
    p_min, p_max, p_mean = base_prices.get(breed, (10000, 100000, 40000))
    
    for i in range(n):
        price = int(np.random.lognormal(mean=np.log(p_mean), sigma=0.45))
        price = max(p_min, min(price, p_max))
        age = random.choice([3, 4, 5, 6, 7, 8, 9, 10])
        city = random.choice(MOROCCAN_CITIES)
        data.append({
            'source': 'EquiVision_Synthetic',
            'title': f"Magnifique {breed} {age} ans",
            'breed': breed,
            'gender': random.choice(['Stallion', 'Mare', 'Gelding']),
            'age': f"{age} years",
            'price_mad': price,
            'location': city,
            'url': f"synthetic_{breed.lower().replace(' ', '_')}_{i}",
            'is_synthetic': 1
        })
    return data

# --- PIPELINE ---

def run_professional_pipeline():
    print("Initializing EquiVision Professional Data Pipeline...")
    
    # 1. BRONZE
    df = pd.read_csv(BRONZE_PATH)
    df['is_synthetic'] = 0
    print(f"Bronze Ingested: {len(df)} records")

    # 2. SILVER (Clean & Purify)
    df = df.dropna(subset=['price_mad', 'title'])
    df['price_mad'] = pd.to_numeric(df['price_mad'], errors='coerce')
    df = df.drop_duplicates(subset=['url'])
    df = df[(df['price_mad'] >= 4000) & (df['price_mad'] <= 4000000)]
    
    df['breed_clean'] = df.apply(lambda x: extract_breed(x['title'], x['breed']), axis=1)
    df = df[df['breed_clean'] != "Rejected"].copy()
    df['breed'] = df['breed_clean']
    print(f"Silver Purified: {len(df)} records")
    
    # 3. AUGMENTATION
    print("Augmenting Arabian and Barb datasets for model balance...")
    synthetic_data = []
    synthetic_data.extend(generate_synthetic_moroccan("Arabian", 250))
    synthetic_data.extend(generate_synthetic_moroccan("Barb", 200))
    synthetic_data.extend(generate_synthetic_moroccan("Arabian-Barb Mix", 150))
    
    df_aug = pd.concat([df, pd.DataFrame(synthetic_data)], ignore_index=True)
    
    # 4. GOLD (Features)
    print("Engineering Gold Layer features...")
    df_aug['log_price'] = np.log10(df_aug['price_mad'])
    df_aug['is_morocco'] = df_aug.apply(lambda x: 1 if ('.ma' in str(x['source']) or x['is_synthetic'] == 1) else 0, axis=1)
    df_aug['age_num'] = df_aug['title'].apply(extract_age)
    
    # Simplify Breeds
    counts = df_aug['breed'].value_counts()
    rare = counts[counts < 5].index
    df_aug['breed_simplified'] = df_aug['breed'].apply(lambda x: 'Other_Rare' if x in rare else x)
    
    df_aug['source_type'] = df_aug['source'].apply(lambda x: 'Local' if '.ma' in str(x) else ('Synthetic' if 'Synthetic' in str(x) else 'International'))
    
    df_aug = df_aug.drop(columns=['breed_clean'], errors='ignore')
    
    # Save
    df_aug.to_csv(SILVER_PATH, index=False)
    df_aug.to_csv(GOLD_PATH, index=False)
    
    print(f"Gold Layer Finalized: {len(df_aug)} records")
    print(f"Summary: Original Clean({len(df)}), Synthetic({len(synthetic_data)})")

if __name__ == "__main__":
    run_professional_pipeline()
