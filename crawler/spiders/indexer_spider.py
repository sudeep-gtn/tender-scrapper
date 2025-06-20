import scrapy
from scrapy import Request
from urllib.parse import urlencode, urlparse
import logging
import json
import os
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class IndexerSpider(scrapy.Spider):
    def __init__(self, country="Nepal", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queries = [
            f'tender notice {country} information security audit',
            f'tender notice {country} vapt 2025',
            f'tender notice {country} iso 27001 2025',
            f'eoi {country} tender',
            f'procurement notice {country}'
        ]
    name = 'indexer_spider'
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    def __init__(self, *args, **kwargs):
        super(IndexerSpider, self).__init__(*args, **kwargs)
        self.ua = UserAgent()
        self.serpapi_key = "11005b544662f18b992432eb381116cc6d0c7c5020013e4b4f46dfd227132f96"
        self.queries = [
            'tender notice nepal bhutan information security audit 2025',
            'tender notice nepal bhutan vapt 2025',
            'tender notice nepal bhutan iso 27001 2025',
            'tender notice nepal bhutan information security audit 2025',
            'eoi nepal bhutan tender tender 2025',
            'procurement notice nepal bhutan 2025',
            "Information security audit tender notice 2025"
        ]
        self.indexed_data = []
        self.output_file = 'indexed_urls.json'

    def start_requests(self):
        for query in self.queries:
            yield self.build_serpapi_request(query)

    def build_serpapi_request(self, query):
        params = {
            'q': query,
            'api_key': self.serpapi_key,
            'engine': 'google',
        }
        url = f"https://serpapi.com/search?{urlencode(params)}"
        return Request(
            url=url,
            callback=self.parse_serpapi_results,
            headers={'User-Agent': self.ua.random},
            meta={'query': query}
        )

    def parse_serpapi_results(self, response):
        try:
            data = json.loads(response.text)
            organic_results = data.get('organic_results', [])
            logger.info(f"Found {len(organic_results)} results for query: {response.meta['query']}")
            for result in organic_results:
                link = result.get('link')
                if link:
                    yield Request(url=link, callback=self.parse_page_content, meta={'source_query': response.meta['query']})
        except Exception as e:
            logger.error(f"Error parsing SerpAPI response: {e}")

    def parse_page_content(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else ''
            body_text = soup.get_text(separator=' ', strip=True)[:2000]
            self.indexed_data.append({
                'url': response.url,
                'title': title,
                'content': body_text
            })
            logger.info(f"Indexed page: {response.url}")
        except Exception as e:
            logger.error(f"Error extracting content from {response.url}: {e}")

    def closed(self, reason):
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.indexed_data, f, indent=2)
            logger.info(f"Saved {len(self.indexed_data)} indexed URLs to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving indexed URLs: {e}")