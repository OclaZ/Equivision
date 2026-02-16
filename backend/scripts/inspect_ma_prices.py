import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
df = pd.read_csv('data/bronze/horse_prices_raw.csv')
ma_data = df[df['source'].str.contains('.ma')]
print(f"Total Moroccan Scraped: {len(ma_data)}")
print("--- Price and Title Samples ---")
for _, row in ma_data.sort_values('price_mad').tail(30).iterrows():
    print(f"Source: {row['source']} | Price: {row['price_mad']} | Title: {row['title']}")
