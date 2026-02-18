import pandas as pd
import numpy as np
import re
from pathlib import Path
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CURRENT_YEAR = datetime.now().year
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- KNOWLEDGE BASES ---
BREED_MAP = {
    # Arabs
    "arabian": "Arabian", "arabe": "Arabian", "ox": "Arabian", "pur sang arabe": "Arabian",
    # Barbs
    "barb": "Barb", "barbe": "Barb", 
    "arabian-barb": "Arabian-Barb Mix", "arabe-barbe": "Arabian-Barb Mix", "arabe barbe": "Arabian-Barb Mix",
    # Thoroughbreds
    "thoroughbred": "Thoroughbred", "pur sang": "Thoroughbred", "ps": "Thoroughbred", "anglo": "Anglo-Arabian", "anglo-arabe": "Anglo-Arabian",
    # Warmbloods
    "friesian": "Friesian", "frison": "Friesian", 
    "andalusian": "Andalusian", "pre": "Andalusian", "pura raza española": "Andalusian", "espagnol": "Andalusian", "andalou": "Andalusian",
    "lusitano": "Lusitano", "lusitanien": "Lusitano", "psl": "Lusitano",
    "hanoverian": "Hanoverian", "hanovre": "Hanoverian", "hanovrien": "Hanoverian",
    "holsteiner": "Holsteiner", "holstein": "Holsteiner",
    "kwpn": "KWPN", "dutch warmblood": "KWPN", "nwp": "KWPN",
    "sf": "Selle Français", "selle francais": "Selle Français", "selle français": "Selle Français",
    "oldenburg": "Oldenburg", "oldenbourg": "Oldenburg",
    "westphalian": "Westphalian", "westphalien": "Westphalian",
    "zangersheide": "Zangersheide", "zangersheider": "Zangersheide",
    "bwp": "Belgian Warmblood", "belgian warmblood": "Belgian Warmblood", "sbs": "Belgian Sport Horse", "cheval de sport belge": "Belgian Sport Horse",
    "trakehner": "Trakehner",
    "aes": "Anglo European",
    "irish sport horse": "Irish Sport Horse", "ish": "Irish Sport Horse",
    # American
    "quarter horse": "Quarter Horse", "quarter": "Quarter Horse", "american quarter horse": "Quarter Horse", "qh": "Quarter Horse", "paint": "Paint Horse", "appaloosa": "Appaloosa",
    # Drafts
    "percheron": "Percheron", "shire": "Shire", "clydesdale": "Clydesdale", "breton": "Breton",
    "comtois": "Comtois", "boulonnais": "Boulonnais",
    "irish cob": "Irish Cob", "tinker": "Irish Cob", "gypsy": "Irish Cob",
    # Ponies
    "shetland": "Shetland", "welsh": "Welsh", "connemara": "Connemara", "haflinger": "Haflinger", 
    "fjords": "Fjord", "fjord": "Fjord", "pottok": "Pottok", "pony": "Pony", "poney": "Pony",
    "new forest": "New Forest", "pfs": "Poney Français de Selle", "poney francais de selle": "Poney Français de Selle"
}

GENDER_MAP = {
    "male": "Stallion", "mâle": "Stallion", "etalon": "Stallion", "étalon": "Stallion", "stallion": "Stallion", "entier": "Stallion",
    "female": "Mare", "femelle": "Mare", "jument": "Mare", "mare": "Mare", "poulinière": "Mare",
    "gelding": "Gelding", "hongre": "Gelding"
}

# --- HELPER FUNCTIONS ---

def clean_text(text):
    if not isinstance(text, str): return ""
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()

def extract_breed(text):
    """Smart breed extraction using the BREED_MAP."""
    text_clean = clean_text(text)
    
    # Check specific compound breeds first
    if "arabe barbe" in text_clean or "arabe-barbe" in text_clean:
        return "Arabian-Barb Mix"
    
    for key, value in BREED_MAP.items():
        # Word boundary check
        if re.search(r'\b' + re.escape(key) + r'\b', text_clean):
            return value
    return "Other"

def extract_gender(text):
    text_clean = clean_text(text)
    for key, value in GENDER_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text_clean):
            return value
    return "Unknown"

def parse_price(price_str):
    if not isinstance(price_str, str):
        if isinstance(price_str, (int, float)): return float(price_str)
        return np.nan
    
    # Clean string
    price_str = price_str.lower().replace('.', '').replace(',', '').replace(' ', '').strip()
    
    # Check for "Price on Request"
    if any(x in price_str for x in ['request', 'nous consulter', 'offrir', ' enchère', 'poa', 'ono']):
        return np.nan
    
    # Handle ranges: "15 000 à 20 000" -> Average
    numbers = re.findall(r'\d+', price_str)
    if not numbers:
        return np.nan
    
    nums = [float(n) for n in numbers]
    
    # Filter extremely small numbers (likely unrelated digits) if context suggests huge price, 
    # but here we usually get raw prices.
    
    if len(nums) == 2:
        return sum(nums) / 2
    elif len(nums) > 0:
        return nums[0]
    
    return np.nan

def parse_height(height_str):
    """Normalizes height to cm."""
    if not isinstance(height_str, str): return np.nan
    
    text = height_str.lower().strip()
    
    # Try "165 cm", "1.65 m", "1m65"
    match_m = re.search(r'(\d)[m\.](\d{2})', text)
    if match_m:
        return int(match_m.group(1)) * 100 + int(match_m.group(2))
    
    match_cm = re.search(r'(\d{3})\s*cm?', text)
    if match_cm:
        return int(match_cm.group(1))
    
    # Hands: "16.2 hh", "14.1"
    match_hh = re.search(r'(\d{1,2})[\.,](\d)\s*(hh|h|hands)?', text)
    if match_hh and ("h" in text or "hand" in text or "hh" in text):
        hands = int(match_hh.group(1))
        inches = int(match_hh.group(2))
        total_inches = (hands * 4) + inches
        return int(total_inches * 2.54)
    
    return np.nan

def parse_age(age_str):
    """Extracts age in years."""
    if not isinstance(age_str, str): 
        if isinstance(age_str, (int, float)): return float(age_str)
        return np.nan
        
    text = age_str.lower()
    
    # "10 years", "5 ans", "10yo"
    match = re.search(r'(\d{1,2})\s*(ans|an|years|yrs|yo)', text)
    if match:
        return int(match.group(1))
    
    # Birth year "2015", "né en 2018"
    matches = re.findall(r'\b(20[0-2][0-9])\b', text)
    if matches:
        birth_year = int(max(matches))
        return CURRENT_YEAR - birth_year
        
    return np.nan

# --- PARSERS WITH IMAGE EXTRACTION ---

def parse_ehorses():
    logger.info("Parsing eHorses...")
    file_path = DATA_DIR / "ehorses.csv"
    if not file_path.exists(): return pd.DataFrame()
    df = pd.read_csv(file_path)
    clean_df = pd.DataFrame()
    clean_df['name'] = df['headline']
    clean_df['price'] = df['price'].apply(parse_price)
    clean_df['breed'] = df['headline'].apply(extract_breed)
    clean_df['gender'] = df['headline'].apply(extract_gender)
    clean_df['age'] = df['headline'].apply(parse_age)
    clean_df['height'] = df['headline'].apply(parse_height)
    # Image URL
    clean_df['image_url'] = df.get('swiper-slide src', np.nan)
    clean_df['source'] = 'ehorses'
    return clean_df

def parse_equirodi():
    logger.info("Parsing Equirodi...")
    file_path = DATA_DIR / "equirodi.csv"
    if not file_path.exists(): return pd.DataFrame()
    df = pd.read_csv(file_path)
    clean_df = pd.DataFrame()
    price_col = 'Price' if 'Price' in df.columns else 'price'
    if price_col in df.columns:
        clean_df['price'] = df[price_col].apply(parse_price)
    else:
        clean_df['price'] = np.nan
    clean_df['breed'] = df.apply(lambda x: extract_breed(str(x.get('Breed', '')) + " " + str(x.get('description', ''))), axis=1)
    clean_df['gender'] = df.apply(lambda x: extract_gender(str(x.get('Gender', '')) + " " + str(x.get('description', ''))), axis=1)
    clean_df['age'] = df.apply(lambda x: parse_age(str(x.get('Age', '')) if 'Age' in df.columns else str(x.get('description', ''))), axis=1)
    clean_df['height'] = df.apply(lambda x: parse_height(str(x.get('Height', '')) if 'Height' in df.columns else str(x.get('description', ''))), axis=1)
    clean_df['name'] = df.get('Title', 'Unknown')
    # Image URL (last column usually)
    clean_df['image_url'] = df.get('col-md-6 src', np.nan)
    clean_df['source'] = 'equirodi'
    return clean_df

def parse_germanhorsecenter():
    logger.info("Parsing GermanHorseCenter...")
    file_path = DATA_DIR / "germanhorsecenter.csv"
    if not file_path.exists(): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path)
    except:
        return pd.DataFrame()

    clean_df = pd.DataFrame()
    df['full_text'] = df.apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
    clean_df['price'] = df['full_text'].apply(parse_price)
    clean_df['breed'] = df['full_text'].apply(extract_breed)
    clean_df['gender'] = df['full_text'].apply(extract_gender)
    clean_df['age'] = df['full_text'].apply(parse_age)
    clean_df['height'] = df['full_text'].apply(parse_height)
    clean_df['name'] = df.get('header', 'Unknown')
    # Image URL
    clean_df['image_url'] = df.get('teaser__img-container src', np.nan)
    clean_df['source'] = 'germanhorsecenter'
    return clean_df

def parse_horsequest():
    logger.info("Parsing HorseQuest...")
    file_path = DATA_DIR / "horsequest.csv"
    if not file_path.exists(): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except Exception as e:
        logger.error(f"Failed to read horsequest: {e}")
        return pd.DataFrame()

    target_col = df.columns[8] if len(df.columns) > 8 else None
    
    clean_df = pd.DataFrame()
    clean_df['source'] = 'horsequest'
    clean_df['name'] = df.iloc[:, 3] if len(df.columns) > 3 else "Unknown"
    # Image URL (col 1 usually)
    # Check if col 1 is sensible
    clean_df['image_url'] = df.iloc[:, 1] if len(df.columns) > 1 else np.nan

    def process_hq_row(row):
        hl_item = str(row[target_col]) if target_col else ""
        parts = hl_item.split('|')
        
        height = np.nan
        age = np.nan
        breed = "Other"
        gender = "Unknown"
        
        for part in parts:
            part = part.strip()
            if parse_height(part) is not np.nan and "yo" not in part.lower():
                height = parse_height(part)
            elif parse_age(part) is not np.nan and ("yo" in part.lower() or "year" in part.lower()):
                age = parse_age(part)
            else:
                b = extract_breed(part)
                if b != "Other": breed = b
                g = extract_gender(part)
                if g != "Unknown": gender = g
        
        full_text = " ".join([str(x) for x in row.values])
        price = parse_price(full_text)
        
        return pd.Series([height, age, breed, gender, price])

    extracted = df.apply(process_hq_row, axis=1)
    extracted.columns = ['height', 'age', 'breed', 'gender', 'price']
    clean_df = pd.concat([clean_df, extracted], axis=1)
    
    return clean_df

def parse_paardplaats():
    logger.info("Parsing Paardplaats...")
    file_path = DATA_DIR / "paardplaats.csv"
    if not file_path.exists(): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except:
        return pd.DataFrame()
        
    clean_df = pd.DataFrame()
    clean_df['name'] = df.iloc[:, 5]
    clean_df['breed'] = df.iloc[:, 7].apply(extract_breed)
    clean_df['age'] = df.iloc[:, 8].apply(parse_age)
    clean_df['height'] = df.iloc[:, 9].apply(parse_height)
    clean_df['gender'] = df.iloc[:, 11].apply(extract_gender)
    clean_df['price'] = df.iloc[:, 14].apply(parse_price)
    
    # Image URL (col 1: object-contain src)
    clean_df['image_url'] = df.iloc[:, 1] if len(df.columns) > 1 else np.nan
    clean_df['source'] = 'paardplaats'
    
    return clean_df

def parse_shf():
    logger.info("Parsing SHF Market...")
    file_path = DATA_DIR / "shf-market.csv"
    if not file_path.exists(): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except:
        return pd.DataFrame()
        
    clean_df = pd.DataFrame()
    name_col = df.columns[3]
    details_col = df.columns[4]
    price_col = df.columns[-1]
    
    clean_df['name'] = df[name_col]
    clean_df['price'] = df[price_col].apply(parse_price)
    
    # Image URL (card-img-top src - col 2)
    clean_df['image_url'] = df.iloc[:, 2] if len(df.columns) > 2 else np.nan

    def process_shf_details(text):
        if not isinstance(text, str): return pd.Series([np.nan, np.nan, "Other", "Unknown"])
        lines = text.split('\n')
        breed = "Other"
        age = np.nan
        height = np.nan
        gender = "Unknown"
        if len(lines) > 0:
            breed = extract_breed(lines[0])
        if len(lines) > 1:
            line2_parts = lines[1].split('-')
            for part in line2_parts:
                p = part.strip()
                if "ans" in p.lower() or "year" in p.lower():
                    age = parse_age(p)
                elif "cm" in p.lower() or "m" in p.lower():
                    height = parse_height(p)
                elif extract_gender(p) != "Unknown":
                    gender = extract_gender(p)
        return pd.Series([age, height, breed, gender])

    extracted = df[details_col].apply(process_shf_details)
    extracted.columns = ['age', 'height', 'breed', 'gender']
    clean_df = pd.concat([clean_df, extracted], axis=1)
    clean_df['source'] = 'shf'
    
    return clean_df

def parse_caballo():
    logger.info("Parsing Caballo Horsemarket...")
    file_path = DATA_DIR / "caballo-horsemarket.csv"
    if not file_path.exists(): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except:
        return pd.DataFrame()
        
    clean_df = pd.DataFrame()
    clean_df['source'] = 'caballo'
    
    df['full_text'] = df.apply(lambda x: ' '.join(x.dropna().astype(str)), axis=1)
    
    clean_df['price'] = df['full_text'].apply(parse_price)
    clean_df['breed'] = df['full_text'].apply(extract_breed)
    clean_df['age'] = df['full_text'].apply(parse_age)
    clean_df['height'] = df['full_text'].apply(parse_height)
    clean_df['gender'] = df['full_text'].apply(extract_gender)
    clean_df['name'] = "Unknown"
    
    # Image URL (index 1: nomargin src)
    clean_df['image_url'] = df.iloc[:, 1] if len(df.columns) > 1 else np.nan
    
    return clean_df

def main():
    logger.info("Starting Data Unification (With Images)...")
    
    parsers = [
        parse_ehorses,
        parse_equirodi,
        parse_germanhorsecenter,
        parse_horsequest,
        parse_paardplaats,
        parse_shf,
        parse_caballo
    ]
    
    all_data = []
    
    for parser in parsers:
        try:
            df = parser()
            if not df.empty:
                logger.info(f"Loaded {len(df)} records from {parser.__name__}")
                all_data.append(df)
        except Exception as e:
            logger.error(f"CRITICAL ERROR in {parser.__name__}: {e}")
            
    if not all_data:
        logger.error("No data parsed!")
        return

    final_df = pd.concat(all_data, ignore_index=True)
    
    # Final Cleaning
    # Keep rows with Price OR (Breed AND Image) -> Ideally for Vision we need Breed+Image
    # For Pricing we need Price+Breed+Features
    
    # We will save EVERYTHING that has valid breed/price to the unified file, 
    # but also ensure image_url is preserved.
    
    final_df = final_df.dropna(subset=['price'])
    final_df = final_df[(final_df['price'] > 500) & (final_df['price'] < 5000000)]
    final_df = final_df[(final_df['age'] >= 0) & (final_df['age'] <= 30)]
    
    final_df['breed'] = final_df['breed'].fillna('Other')
    final_df['gender'] = final_df['gender'].fillna('Unknown')
    final_df['image_url'] = final_df['image_url'].replace({np.nan: None})
    
    logger.info(f"Final Combined Data Count: {len(final_df)}")
    
    # Count valid images
    valid_imgs = final_df['image_url'].notna().sum()
    logger.info(f"Records with Images: {valid_imgs}")
    
    output_path = PROCESSED_DIR / "unified_horse_data.csv"
    final_df.to_csv(output_path, index=False)
    logger.info(f"✅ Unified data saved to {output_path}")

if __name__ == "__main__":
    main()
