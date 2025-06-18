BOT_NAME = 'tender_crawler'
SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 0.5
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0
ITEM_PIPELINES = {
    'crawler.pipelines.SqlitePipeline': 300,
    'crawler.pipelines.CsvPipeline': 400,
    'crawler.pipelines.TextPipeline': 500
}
SQLITE_FILE = 'tenders.db'
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
DEPTH_LIMIT = 3
DOWNLOADER_MIDDLEWARES = {
    'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler': 543,
}
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000