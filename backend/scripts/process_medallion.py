import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setting styles
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

DATA_DIR = Path("data")
BRONZE_PATH = DATA_DIR / "bronze" / "horse_prices_raw.csv"
SILVER_PATH = DATA_DIR / "silver" / "horse_prices_cleaned.csv"
GOLD_PATH = DATA_DIR / "gold" / "horse_features_final.csv"

# 1. Bronze
print("Processing Bronze Layer...")
df_bronze = pd.read_csv(BRONZE_PATH)

# 2. Silver
print("Processing Silver Layer...")
df_silver = df_bronze.copy()
df_silver['price_mad'] = pd.to_numeric(df_silver['price_mad'], errors='coerce')
df_silver = df_silver.dropna(subset=['price_mad'])
df_silver = df_silver.drop_duplicates(subset=['url'])
df_silver = df_silver[(df_silver['price_mad'] >= 3000) & (df_silver['price_mad'] <= 3000000)]
df_silver['breed'] = df_silver['breed'].fillna('Unknown')
df_silver['gender'] = df_silver['gender'].fillna('Unknown')
df_silver.to_csv(SILVER_PATH, index=False)

# 3. Gold
print("Processing Gold Layer...")
df_gold = df_silver.copy()
df_gold['log_price'] = np.log1p(df_gold['price_mad'])
df_gold['is_morocco'] = (df_gold['source'].str.contains('.ma') | (df_gold['location'] == 'Morocco')).astype(int)

# Breed simplification
breed_counts = df_gold['breed'].value_counts()
rare_breeds = breed_counts[breed_counts < 10].index
df_gold['breed_simplified'] = df_gold['breed'].replace(rare_breeds, 'Other')

df_gold.to_csv(GOLD_PATH, index=False)
print(f"EDA Pipeline Complete. Gold Records: {len(df_gold)}")

# Generate a plot to verify
plt.figure(figsize=(12, 8))
sns.boxplot(data=df_gold[df_gold['breed_simplified'] != 'Other'], x='price_mad', y='breed_simplified')
plt.xscale('log')
plt.title('Price Distribution by Breed (Gold Data)')
plt.savefig('horse_price_distribution.png')
print("Verification plot saved to horse_price_distribution.png")
