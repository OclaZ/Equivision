import scrapy


class AvitoSpider(scrapy.Spider):
    name = "avito"
    allowed_domains = ["avito.ma"]
    start_urls = ["https://avito.ma"]

    def parse(self, response):
        pass
