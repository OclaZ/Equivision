
import scrapy
from typing import Generator, Dict, Any

class AvitoSpider(scrapy.Spider):
    name = "avito"
    allowed_domains = ["avito.ma"]
    start_urls = ["https://www.avito.ma/fr/maroc/animaux/chevaux"]
    
    # Configuration
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Be respectful to the server
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, max_pages=5, *args, **kwargs):
        super(AvitoSpider, self).__init__(*args, **kwargs)
        self.max_pages = int(max_pages)
        self.pages_crawled = 0

    def parse(self, response) -> Generator[Dict[str, Any], None, None]:
        self.pages_crawled += 1
        self.logger.info(f"Parsing page {self.pages_crawled}/{self.max_pages}")
        
        # Iterate over listings
        for node in response.css('a.sc-1jge648-0.jZXrfL'):
            item = {}
            item['url'] = node.css('::attr(href)').get()
            item['title'] = node.css('p[title]::attr(title)').get()
            
            price_val = node.css('span.sc-3286ebc5-2.PuYkS::text').get()
            price_currency = node.css('span.sc-3286ebc5-5.eHXozK::text').get()
            if price_val:
                item['price'] = f"{price_val} {price_currency or ''}".strip()
            else:
                item['price'] = "N/A"
            
            item['location'] = node.css('div.sc-b57yxx-10.fHMeoC p::text').get()
            item['image_url'] = node.css('div.sc-1lb3x1r-8.ftXIwi img::attr(src)').get()
            item['time_ago'] = node.css('div.sc-5rosa-2.jDipnj p::text').get()
            
            if item['url']:
                yield item
        
        # Pagination with limit
        if self.pages_crawled < self.max_pages:
            next_page = response.css('a[rel="next"]::attr(href)').get()
            if next_page:
                yield response.follow(next_page, self.parse)
            else:
                self.logger.info("No more pages found")
        else:
            self.logger.info(f"Reached max pages limit: {self.max_pages}")
