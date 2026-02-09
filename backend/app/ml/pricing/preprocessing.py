
import json
import re
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

class PricingPreprocessor:
    BREEDS = ['arabe', 'barbe', 'anglo', 'espagnol', 'frison', 'poney', 'shetland', 'cheval']
    GENDERS = {'jument': 'female', 'poulinière': 'female', 'hongre': 'gelding', 'étalon': 'male', 'poulain': 'male', 'male': 'male'}

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else None
        self.df = None

    def load_data(self) -> pd.DataFrame:
        if not self.data_path or not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found at {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        self.df = pd.DataFrame(raw_data)
        return self.df

    @staticmethod
    def clean_price(price_str: str) -> Optional[float]:
        try:
            if not price_str or not isinstance(price_str, str):
                return None
            clean_str = re.sub(r'[^0-9]', '', price_str)
            if not clean_str:
                return None
            return float(clean_str)
        except Exception:
            return None

    @classmethod
    def extract_features(cls, text: str) -> Dict[str, str]:
        text = str(text).lower()
        
        # Breed
        breed = 'unknown'
        for b in cls.BREEDS:
            if b in text:
                breed = b
                break
        
        # Gender
        gender = 'unknown'
        for k, v in cls.GENDERS.items():
            if k in text:
                gender = v
                break
                
        return {'breed': breed, 'gender': gender}

    def process(self) -> pd.DataFrame:
        if self.df is None:
            self.load_data()
            
        # 1. Clean Price
        self.df['price_numeric'] = self.df['price'].apply(self.clean_price)
        
        # 2. Extract Features
        features = self.df['title'].apply(self.extract_features).apply(pd.Series)
        self.df = pd.concat([self.df, features], axis=1)
        
        # 3. Filter Valid Data
        # We need a price to train
        df_clean = self.df.dropna(subset=['price_numeric'])
        
        # 4. One-Hot Encode (for simplicity in v1)
        # Note: In production, we should save the encoder or use pipelines
        # For this MVP, we will return the processed dataframe ready for training
        return df_clean

if __name__ == "__main__":
    # Test
    pp = PricingPreprocessor("d:/EquiVision/backend/data/raw/avito_horses.json")
    df = pp.process()
    print(f"Processed {len(df)} listings. Columns: {df.columns.tolist()}")
