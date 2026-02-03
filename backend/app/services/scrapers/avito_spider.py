
import scrapy
from typing import Generator, Dict, Any

class AvitoSpider(scrapy.Spider):
    name = "avito"
    allowed_domains = ["avito.ma"]
    start_urls = ["https://www.avito.ma/fr/maroc/animaux/chevaux"]

    def parse(self, response) -> Generator[Dict[str, Any], None, None]:
        # Iterate over listings
        # Using the selectors validated in parse_avito.py
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
        
        # Pagination
        # Need to identify the "Next" button.
        # This might require inspecting the sample html for pagination links.
        # In the absence of a visible pagination in sample, we'll assume a localized text or class.
        # I'll look for a link with rel="next" or similar generic pattern.
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
