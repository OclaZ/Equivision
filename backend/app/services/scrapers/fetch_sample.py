import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
r = requests.get('https://www.avito.ma/fr/maroc/chevaux-a_vendre', headers=headers)
with open('avito_sample.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
