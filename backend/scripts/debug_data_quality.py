import pandas as pd
import re

def analyze_raw_data():
    df = pd.read_csv('data/gold/horse_features_final.csv')
    
    print(f"Total records in Gold: {len(df)}")
    
    breeds = df['breed'].value_counts()
    print("\n--- Distribution of 'Breed' column values ---")
    print(breeds.head(30))
    
    print("\n--- Samples of 'Cheval' or 'Unknown' needing extraction ---")
    problematic = df[df['breed'].isin(['Cheval', 'Unknown', 'Poney', 'Pony', 'Other'])]
    for _, row in problematic.head(20).iterrows():
        print(f"Source: {row['source']} | Breed: {row['breed']} | Title: {row['title']}")

if __name__ == "__main__":
    analyze_raw_data()
