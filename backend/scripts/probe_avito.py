import requests
from bs4 import BeautifulSoup
import json

url = "https://www.avito.ma/fr/maroc/animaux-à_vendre?q=cheval"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        print("FOUND __NEXT_DATA__!")
        data = json.loads(next_data.string)
        # Verify structure
        print("Keys:", data.keys())
        if 'props' in data:
            print("Props keys:", data['props'].keys())
    else:
        print("NO __NEXT_DATA__ found.")
        # Print some classes to guess structure
        print("Div classes:", [div.get('class') for div in soup.find_all('div', limit=20) if div.get('class')])

except Exception as e:
    print(f"Error: {e}")
