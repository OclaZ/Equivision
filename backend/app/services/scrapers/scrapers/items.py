import scrapy

class HorseListingItem(scrapy.Item):
    source = scrapy.Field()
    external_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    # Attributes
    breed = scrapy.Field()
    age = scrapy.Field()
    gender = scrapy.Field()
    discipline = scrapy.Field()
    image_urls = scrapy.Field()
    published_at = scrapy.Field()
    scraped_at = scrapy.Field()
