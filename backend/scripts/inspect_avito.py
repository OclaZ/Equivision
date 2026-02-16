import pandas as pd
import sys

# Set output encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/bronze/horse_prices_raw.csv')
avito = df[df['source'] == 'avito.ma']
print(f"Total Avito: {len(avito)}")
print("--- Titles and Breeds (Raw) ---")
for _, row in avito.head(30).iterrows():
    print(f"Title: {row['title']} | Breed: {row['breed']}")

known_breed_words = ["arabe", "barbe", "pura", "sang", "anglo", "poney", "cheval", "horse"]
hits = 0
for _, row in avito.iterrows():
    t = str(row['title']).lower()
    if any(w in t for w in known_breed_words):
        hits += 1
print(f"\nPotential Breed Hits in Titles: {hits}")
