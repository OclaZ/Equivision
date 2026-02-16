import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorldHorseScraper:
    def __init__(self, output_file="world_horse_prices.csv"):
        self.output_file = Path(output_file)
        self.data = []
        # Robust headers to avoid blocking
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # Approximate conversion rates to MAD (DH)
        self.rates = {
            '€': 10.7,
            '£': 12.8,
            '$': 10.1,
            'CHF': 11.4
        }

    def parse_price(self, price_text):
        """Extract numeric value and convert to MAD."""
        if not price_text: return 0
        
        # Determine currency
        rate = 10.7 # Default EUR
        for symbol, r in self.rates.items():
            if symbol in price_text:
                rate = r
                break
        
        # Handle ranges like "€10,000 to €15,000"
        prices = re.findall(r'[\d\.,]+', price_text)
        if not prices: return 0
        
        vals = []
        for p in prices:
            # Clean number: remove dots/commas
            clean_p = re.sub(r'[^\d]', '', p)
            if clean_p: vals.append(int(clean_p))
        
        if not vals: return 0
        
        # Return average if range, else the single value, then convert to MAD
        avg_price = sum(vals) / len(vals)
        return int(avg_price * rate)

    def save(self):
        if not self.data: return
        mode = 'a' if self.output_file.exists() else 'w'
        header = not self.output_file.exists()
        fieldnames = ['source', 'name', 'breed', 'gender', 'age', 'price_mad', 'location', 'url']
        with open(self.output_file, mode=mode, newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if header: writer.writeheader()
            writer.writerows(self.data)
        logger.info(f"Saved {len(self.data)} records to {self.output_file}")
        self.data = []

    def scrape_ehorses(self, max_pages=100):
        """Scrape ehorses.com - The world's largest marketplace."""
        # Verified search URL
        base_url = "https://www.ehorses.com/search?viewtype=1&currency=EUR"
        
        logger.info(f"Starting ehorses.com global scrape (Target: {max_pages} pages)")
        
        for page in range(1, max_pages + 1):
            # Pagination parameter verified: seite=X
            url = f"{base_url}&seite={page}"
            
            try:
                # Use a small delay to be polite
                time.sleep(random.uniform(1.0, 2.5))
                
                response = requests.get(url, headers=self.headers, timeout=20)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch page {page}: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                # Main listing containers are 'horseBlock'
                cards = soup.select('div.horseBlock')
                
                if not cards:
                    logger.warning(f"No cards found on page {page}. Inspecting HTML...")
                    # Save error page for debug if it persists
                    break
                
                for card in cards:
                    try:
                        # 1. Headline contains Breed, Gender, Age
                        headline_el = card.select_one('a.headline')
                        if not headline_el: continue
                        
                        headline = headline_el.text.strip()
                        url_ad = headline_el['href']
                        if not url_ad.startswith('http'):
                            url_ad = f"https://www.ehorses.com{url_ad}"
                            
                        # Split headline: "Haflinger, Mare, 12 years, 146 cm, Chestnut"
                        parts = [p.strip() for p in headline.split(',')]
                        breed = parts[0] if len(parts) > 0 else "Unknown"
                        gender = parts[1] if len(parts) > 1 else ""
                        age = parts[2] if len(parts) > 2 else ""
                        
                        # 2. Price
                        # Price is in div.price, often with a sub-div sizeS grey
                        price_el = card.select_one('div.price')
                        if not price_el: continue
                        
                        # Prefer the EUR value if present in sizeS grey
                        eur_el = price_el.select_one('.sizeS.grey')
                        price_text = eur_el.text.strip() if eur_el else price_el.text.strip()
                        
                        if "Price on request" in price_text or "bid on auction" in price_text:
                            continue
                            
                        price_mad = self.parse_price(price_text)
                        
                        if price_mad < 1000: continue # Likely bad parse
                        
                        # 3. Location
                        # Country code in .zip p, city in .city
                        country_el = card.select_one('.zip p')
                        city_el = card.select_one('.city')
                        country = country_el.text.strip() if country_el else ""
                        city = city_el.text.strip() if city_el else ""
                        location = f"{city}, {country}".strip(', ')
                        if not location: location = "Global"
                        
                        self.data.append({
                            'source': 'ehorses.com',
                            'name': headline,
                            'breed': breed,
                            'gender': gender,
                            'age': age,
                            'price_mad': price_mad,
                            'location': location,
                            'url': url_ad
                        })
                    except Exception as e:
                        continue
                
                logger.info(f"Page {page}: Scraped {len(self.data)} horses (Total cumulative).")
                self.save() # Saves and clears self.data
                
            except Exception as e:
                logger.error(f"Global Error on page {page}: {e}")
                break

if __name__ == "__main__":
    scraper = WorldHorseScraper()
    # High capacity scrape: 50 pages = ~1000 horses
    scraper.scrape_ehorses(max_pages=50)
