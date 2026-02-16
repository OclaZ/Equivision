import requests
from bs4 import BeautifulSoup
import json

url = "https://www.ehorses.fr/chevaux-a-vendre.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for structured data (schema.org)
    scripts = soup.find_all('script', type='application/ld+json')
    if scripts:
        print("FOUND JSON-LD!")
        for s in scripts:
            print(s.string[:100] + "...")
            
    # Check for specific listing structure
    listings = soup.select('.ed-horse-card')
    print(f"Found {len(listings)} listings via .ed-horse-card selector")
    
    listings_alt = soup.select('.ed-item')
    print(f"Found {len(listings_alt)} listings via .ed-item selector")
    
    # Check raw text if structure fails
    if not listings and not listings_alt:
        print("Classes found:", [div.get('class') for div in soup.find_all('div', limit=20) if div.get('class')])

except Exception as e:
    print(f"Error: {e}")
