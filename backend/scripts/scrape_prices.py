import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HorseScraper:
    def __init__(self, output_file="horse_prices_final.csv"):
        self.output_file = Path(output_file)
        self.data = []
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def save(self):
        if not self.data: return
        mode = 'a' if self.output_file.exists() else 'w'
        header = not self.output_file.exists()
        fieldnames = ['source', 'title', 'price', 'location', 'url']
        with open(self.output_file, mode=mode, newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if header: writer.writeheader()
            writer.writerows(self.data)
        self.data = []

    def scrape_avito(self, pages=50):
        url_base = "https://www.avito.ma/fr/maroc/chevaux--%C3%A0_vendre"
        for p in range(1, pages + 1):
            url = f"{url_base}?o={p}"
            try:
                res = requests.get(url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(res.text, 'html.parser')
                links = soup.find_all('a', href=re.compile(r'/vi/|/fr/'))
                count = 0
                for a in links:
                    href = a.get('href', '')
                    if any(x in href.lower() for x in ['voitures', 'motos', 'camions', 'bateaux', 'remorques', 'appartements', 'maisons']):
                        continue
                    try:
                        title_el = a.find(['p', 'h2'])
                        title = title_el.text.strip() if title_el else ""
                        if any(x in title.lower() for x in ['selle', 'sacoche', 'pompe', 'tableau', 'guitare', 'jacket', 'bronze']):
                            continue
                        price_el = a.find('span', class_=re.compile(r'PuYkS'))
                        price = int(re.sub(r'[^\d]', '', price_el.text)) if price_el else 0
                        if 1000 < price < 500000:
                            self.data.append({
                                'source': 'avito.ma', 'title': title, 'price': price,
                                'location': '', 'url': f"https://www.avito.ma{href}" if not href.startswith('http') else href
                            })
                            count += 1
                    except: continue
                logger.info(f"Avito Page {p}: found {count} horses")
                self.save()
                time.sleep(random.uniform(0.5, 1.5))
            except: continue

    def scrape_animalsouk(self, pages=10):
        for p in range(1, pages + 1):
            try:
                res = requests.get(f"https://www.animalsouk.ma/Chevaux?page={p}", headers=self.headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                ads = soup.select('a.card')
                count = 0
                for ad in ads:
                    try:
                        title = ad.select_one('h2.card-title').text.strip()
                        if 'rottweiler' in title.lower() or 'sac' in title.lower(): continue
                        price = int(re.sub(r'[^\d]', '', ad.select_one('span.price').text))
                        if price > 1000:
                            self.data.append({'source': 'animalsouk.ma', 'title': title, 'price': price, 'location': '', 'url': ''})
                            count += 1
                    except: continue
                logger.info(f"AnimalSouk Page {p}: found {count} horses")
                self.save()
            except: break

    def scrape_animo(self, pages=10):
        for p in range(1, pages + 1):
            try:
                res = requests.get(f"https://animo.ma/annonces/Chevaux?page={p}", headers=self.headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                ads = soup.select('article.item-spot')
                count = 0
                for ad in ads:
                    try:
                        title = ad.select_one('h4 a').text.strip()
                        price = int(re.sub(r'[^\d]', '', ad.select_one('.price-tag').text))
                        if price > 1000:
                            self.data.append({'source': 'animo.ma', 'title': title, 'price': price, 'location': '', 'url': ''})
                            count += 1
                    except: continue
                logger.info(f"Animo Page {p}: found {count} horses")
                self.save()
            except: break

    def scrape_elevage(self, pages=10):
        url_base = "https://www.elevageaumaroc.com/fr/annonces/chevaux-poneys,4"
        for p in range(1, pages + 1):
            url = f"{url_base}?start={(p-1)*20}"
            try:
                res = requests.get(url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(res.text, 'html.parser')
                ads = soup.select('.item_row, .item_outer, .item_box')
                count = 0
                for ad in ads:
                    try:
                        title_el = ad.select_one('a.title')
                        if not title_el: continue
                        title = title_el.text.strip()
                        price_el = ad.select_one('.price_unit, .item_price, .price')
                        if price_el:
                            price = int(re.sub(r'[^\d]', '', price_el.text))
                        else:
                            m = re.search(r'([\d\s\.,]+)\s*DH', ad.get_text(), re.I)
                            price = int(re.sub(r'[^\d]', '', m.group(1))) if m else 0
                        
                        if price > 1000:
                            self.data.append({'source': 'elevageaumaroc.com', 'title': title, 'price': price, 'location': '', 'url': ''})
                            count += 1
                    except: continue
                logger.info(f"Elevage Page {p}: found {count} horses")
                self.save()
            except: continue

    def scrape_ehorses(self, pages=5):
        url_base = "https://www.ehorses.fr/cheval-a-vendre"
        for p in range(1, pages + 1):
            url = f"{url_base}/seite-{p}.html" if p > 1 else url_base
            try:
                res = requests.get(url, headers=self.headers, timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                scripts = soup.find_all('script', type='application/ld+json')
                count = 0
                for s in scripts:
                    try:
                        d = json.loads(s.string.strip())
                        # Check graph or ItemList
                        items = []
                        if d.get('@type') == 'ItemList': items = d.get('itemListElement', [])
                        elif '@graph' in d: items = [x for x in d['@graph'] if x.get('@type') == 'Product']
                        
                        for it in items:
                            o = it.get('item', it)
                            if not o.get('name'): continue
                            offers = o.get('offers', {})
                            p_val = offers.get('price') if isinstance(offers, dict) else (offers[0].get('price') if isinstance(offers, list) else 0)
                            if p_val:
                                price_mad = int(float(p_val) * 10.6)
                                self.data.append({'source': 'ehorses.fr', 'title': o.get('name'), 'price': price_mad, 'location': 'Europe', 'url': o.get('url', '')})
                                count += 1
                    except: continue
                logger.info(f"Ehorses Page {p}: found {count} horses")
                self.save()
                time.sleep(random.uniform(2, 4))
            except: continue

if __name__ == "__main__":
    # Clean previous final file to avoid duplicates if re-running
    if Path("horse_prices_final.csv").exists(): Path("horse_prices_final.csv").unlink()
    
    scraper = HorseScraper()
    scraper.scrape_avito(50)
    scraper.scrape_animalsouk(10)
    scraper.scrape_animo(10)
    scraper.scrape_elevage(10)
    scraper.scrape_ehorses(5)
