
import json
from parsel import Selector

def parse_avito_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    sel = Selector(text=html_content)
    
    # Based on the view_file output in Step 520
    # Listings seem to be in a list.
    # The container class for listings needs to be identified.
    # Looking at the file content: <div class="sc-1jge648-0 jZXrfL"> seems to be the anchor tag for a listing? 
    # Or <a class="sc-1jge648-0 jZXrfL">?
    # Let's try to find the listing chunks.
    
    listings = []
    
    # Generic selector for the listings container - often a mapping of classes.
    # In the sample: <a target="_blank" href="..." class="sc-1jge648-0 jZXrfL"> wraps the listing.
    
    listing_nodes = sel.css('a.sc-1jge648-0.jZXrfL')
    
    for node in listing_nodes:
        item = {}
        item['url'] = node.css('::attr(href)').get()
        item['title'] = node.css('p[title]::attr(title)').get()
        
        # Price: 
        # <span class="sc-3286ebc5-2 PuYkS">305 000</span> <span class="sc-3286ebc5-5 eHXozK">DH</span>
        price_val = node.css('span.sc-3286ebc5-2.PuYkS::text').get()
        price_currency = node.css('span.sc-3286ebc5-5.eHXozK::text').get()
        if price_val:
            item['price'] = f"{price_val} {price_currency or ''}".strip()
        else:
            item['price'] = "N/A"
            
        # Location:
        # <div class="sc-b57yxx-10 fHMeoC"><p class="sc-1x0vz2r-0 layWaX">Voitures d'occasion dans Casablanca, Anfa</p></div>
        # Or <p class="sc-1x0vz2r-0 layWaX" style="line-height:1">Voitures d'occasion dans Casablanca, Anfa</p>
        # The text seems to be "Category dans City, Area"
        # Let's extract the raw location text.
        location_text = node.css('div.sc-b57yxx-10.fHMeoC p::text').get()
        item['location_raw'] = location_text
        
        # Image:
        # <img src="..." alt="..." class="sc-1lb3x1r-3 jXTiJI"/>
        # or <img src="..." class="sc-5rosa-5 esYTOr"/> for avatar?
        # The main image seems to be inside sc-1lb3x1r-8 ftXIwi -> img
        image_url = node.css('div.sc-1lb3x1r-8.ftXIwi img::attr(src)').get()
        item['image_url'] = image_url
        
        # Time:
        # <p class="sc-1x0vz2r-0 layWaX" style="letter-spacing:0">il y a 16 heures</p>
        item['time_ago'] = node.css('div.sc-5rosa-2.jDipnj p::text').get()
        
        listings.append(item)
        
    with open('d:/EquiVision/backend/app/services/scrapers/parsed_avito.json', 'w', encoding='utf-8') as f:
        json.dump(listings, f, indent=2, ensure_ascii=False)
    
    print(f"Parsed {len(listings)} listings. Saved to parsed_avito.json")

if __name__ == "__main__":
    parse_avito_file('d:/EquiVision/backend/app/services/scrapers/avito_sample.html')
