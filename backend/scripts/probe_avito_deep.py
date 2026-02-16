import requests
from bs4 import BeautifulSoup
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

url = "https://www.avito.ma/fr/maroc/animaux-à_vendre?q=cheval"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        data = json.loads(next_data.string)
        props = data.get('props', {}).get('pageProps', {})
        
        # Check componentProps
        comp = props.get('componentProps', {})
        logger.info(f"ComponentProps keys: {list(comp.keys())}")
        if 'analysis' in comp:
             logger.info(f"Analysis keys: {list(comp['analysis'].keys())}")
        
        # Check Apollo State (GraphQL Cache)
        apollo = props.get('apolloState', {})
        # Find keys that look like Listing: or Item:
        listing_keys = [k for k in apollo.keys() if 'Listing' in k or 'Item' in k][:10]
        logger.info(f"Sample Apollo keys: {listing_keys}")

        # Search for any large list in redux
        state = props.get('initialReduxState', {})
        for key, val in state.items():
             if isinstance(val, dict):
                 for subkey, subval in val.items():
                      if isinstance(subval, list) and len(subval) > 0:
                           logger.info(f"Found list in Redux: {key}.{subkey} (len={len(subval)})")
                      elif isinstance(subval, dict) and 'list' in subval:
                           logger.info(f"Found list structure in Redux: {key}.{subkey}.list")

    else:
        logger.warning("No __NEXT_DATA__ found")

except Exception as e:
    logger.error(f"Error: {e}")
