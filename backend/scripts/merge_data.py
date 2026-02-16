import csv
from pathlib import Path

def merge_datasets():
    morocco_file = Path("horse_prices_final.csv")
    world_file = Path("world_horse_prices.csv")
    final_file = Path("horse_prices_master.csv")
    
    master_data = []
    
    # 1. Load Morocco Data
    if morocco_file.exists():
        with open(morocco_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map columns
                master_data.append({
                    'source': row.get('source', 'morocco'),
                    'title': row.get('title', ''),
                    'breed': row.get('type', 'Cheval'),
                    'gender': row.get('gender', ''),
                    'age': row.get('age', ''),
                    'price_mad': row.get('price', 0),
                    'location': row.get('location', 'Morocco'),
                    'url': row.get('url', '')
                })
    
    # 2. Load World Data
    if world_file.exists():
        with open(world_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                master_data.append({
                    'source': row.get('source', 'world'),
                    'title': row.get('name', ''),
                    'breed': row.get('breed', ''),
                    'gender': row.get('gender', ''),
                    'age': row.get('age', ''),
                    'price_mad': row.get('price_mad', 0),
                    'location': row.get('location', 'Global'),
                    'url': row.get('url', '')
                })
                
    # 3. Save Master Data
    fieldnames = ['source', 'title', 'breed', 'gender', 'age', 'price_mad', 'location', 'url']
    with open(final_file, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(master_data)
        
    print(f"Merge Complete! Total records in {final_file}: {len(master_data)}")

if __name__ == "__main__":
    merge_datasets()
