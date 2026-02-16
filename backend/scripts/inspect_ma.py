import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
df = pd.read_csv('data/bronze/horse_prices_raw.csv')
print("--- animo.ma Samples ---")
print(df[df['source'] == 'animo.ma'][['title', 'breed']].head(10))
print("\n--- animalsouk.ma Samples ---")
print(df[df['source'] == 'animalsouk.ma'][['title', 'breed']].head(10))
