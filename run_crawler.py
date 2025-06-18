import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_crawler():
    logger.info("Starting crawler process...")
    os.environ['SCRAPY_SETTINGS_MODULE'] = 'crawler.settings'
    settings = get_project_settings()
    settings.set('REQUEST_FINGERPRINTER_IMPLEMENTATION', '2.7')
    settings.set('CONCURRENT_REQUESTS', 64)
    settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', 16)
    settings.set('DOWNLOAD_DELAY', 0.3)
    settings.set('AUTOTHROTTLE_ENABLED', True)
    settings.set('AUTOTHROTTLE_TARGET_CONCURRENCY', 12.0)
    process = CrawlerProcess(settings)
    
    from crawler.spiders.indexer_spider import IndexerSpider
    from crawler.spiders.tender_spider import TenderSpider
    
    logger.info("Running IndexerSpider...")
    process.crawl(IndexerSpider)
    logger.info("Running TenderSpider...")
    process.crawl(TenderSpider)
    
    process.start()
    logger.info("Crawler process completed.")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_crawler()