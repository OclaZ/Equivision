
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
# Add parent dir to path to import spider
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from avito_spider import AvitoSpider

def run_spider():
    output_file = 'avito_horses.json'
    if os.path.exists(output_file):
        os.remove(output_file)
        
    process = CrawlerProcess(settings={
        "FEEDS": {
            output_file: {"format": "json"},
        },
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })

    process.crawl(AvitoSpider)
    process.start()
    print(f"Spider finished. Check {output_file}")

if __name__ == "__main__":
    run_spider()
