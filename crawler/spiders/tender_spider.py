import scrapy
from scrapy.http import Request
from crawler.items import TenderItem
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import logging
import json
import os
import re
from datetime import datetime

class TenderSpider(scrapy.Spider):
    name = 'tender_spider'
    visited_urls = set()

    def __init__(self, country="Nepal", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country = country
        self.ua = UserAgent()
        self.start_urls = self.get_indexed_urls()

    def get_indexed_urls(self):
        index_file = 'indexed_urls.json'
        if not os.path.exists(index_file):
            self.logger.error(f"Index file {index_file} not found. Run indexer first.")
            return []

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            urls = [item['url'] for item in data if item['url'].startswith('https://')]
            self.logger.info(f"Loaded {len(urls)} HTTPS URLs from {index_file}")
            return urls
        except Exception as e:
            self.logger.error(f"Error loading index file: {e}")
            return []

    def normalize_url(self, url):
        parsed = urlparse(url)
        path = re.sub(r'/page/\d+/?$', '', parsed.path.rstrip('/'))
        query = '' if not re.search(r'page=\d+', parsed.query) else f"?{parsed.query}"
        return f"{parsed.scheme}://{parsed.netloc}{path}{query}"

    def start_requests(self):
        if not self.start_urls:
            self.logger.error("No start URLs found. Ensure index_urls.py has run successfully.")
            return
        for url in self.start_urls:
            normalized_url = self.normalize_url(url)
            self.current_domain = urlparse(normalized_url).netloc
            self.visited_urls.clear()
            self.logger.info(f"Starting crawl for URL: {normalized_url}")
            yield Request(
                url=normalized_url,
                headers={'User-Agent': self.ua.random},
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_options': {'wait_until': 'networkidle', 'timeout': 120000},
                    'playwright_page_scripts': [
                        'await new Promise(resolve => setTimeout(resolve, 5000));',
                        'await page.waitForSelector("body", { timeout: 15000 }).catch(() => null);'
                    ]
                },
                errback=self.handle_error
            )

    def handle_error(self, failure):
        self.logger.error(f"Request failed for {failure.request.url}: {failure.value}")

    def parse(self, response):
        if response.url in self.visited_urls:
            self.logger.debug(f"Skipping already visited URL: {response.url}")
            return
        if urlparse(response.url).netloc != self.current_domain:
            self.logger.debug(f"Skipping external URL: {response.url}")
            return
        if 'SessionTimedOut' in response.url:
            self.logger.warning(f"Session timed out at {response.url}. Skipping.")
            return

        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        if 'text/html' not in content_type:
            self.logger.info(f"Skipping non-HTML response at {response.url}")
            return

        self.visited_urls.add(response.url)
        self.logger.info(f"Crawling: {response.url}")

        # Broad selectors to capture any potential tender-like content
        tenders = response.css(
            'table tr, div, section, article, li, p'
        ) or response.xpath(
            '//tr | //div | //section | //article | //li | //p'
        )
        self.logger.debug(f"Found {len(tenders)} potential tender elements on {response.url}")

        for tender in tenders:
            description = tender.css('p::text, div::text, td::text, span::text, a::text, li::text').getall() or \
                          tender.xpath('.//text()').getall()
            description = ' '.join([d.strip() for d in description if d.strip()])[:1000]
            self.logger.debug(f"Tender description: {description[:200]}...")

            if not description:
                self.logger.debug(f"Skipping tender with empty description")
                continue

            item = TenderItem()
            item['title'] = tender.css(
                'h1::text, h2::text, h3::text, h4::text, td a::text, a::text, '
                'div[class*="title"]::text, span[class*="title"]::text, .title::text'
            ).get(default='').strip() or tender.xpath('.//h1/text() | .//h2/text() | .//h3/text() | .//a/text()').get(default='').strip() or 'Untitled'
            item['description'] = description
            item['pub_date'] = tender.css(
                'time::text, .date::text, span.date::text, td::text, div.date::text, '
                'div[class*="date"]::text, .published::text'
            ).get(default='').strip() or tender.xpath('.//*[contains(@class, "date") or contains(@class, "published")]/text()').get(default='').strip()
            item['submission_deadline'] = tender.css(
                '.deadline::text, td::text, div.deadline::text, div[class*="deadline"]::text, .due-date::text'
            ).get(default='').strip() or tender.xpath('.//*[contains(@class, "deadline") or contains(@class, "due-date")]/text()').get(default='').strip()
            item['eligibility'] = tender.css(
                '.eligibility::text, div.eligibility::text, div[class*="eligibility"]::text'
            ).get(default='').strip() or tender.xpath('.//*[contains(@class, "eligibility")]/text()').get(default='').strip()
            item['contact'] = tender.css(
                '.contact::text, div.contact::text, td::text, div[class*="contact"]::text, .contact-info::text'
            ).get(default='').strip() or tender.xpath('.//*[contains(@class, "contact") or contains(@class, "contact-info")]/text()').get(default='').strip()
            item['link'] = urljoin(response.url, tender.css('a::attr(href)').get(default='') or tender.xpath('.//a/@href').get(default=''))
            item['source_url'] = response.url
            item['country'] = self.country
            item['issuer'] = tender.css(
                '.issuer::text, .organization::text, .authority::text, div.header::text, '
                'h1 small::text, div[class*="issuer"]::text, div[class*="organization"]::text'
            ).get(default='').strip() or tender.xpath('.//*[contains(@class, "issuer") or contains(@class, "organization")]/text()').get(default='').strip()
            if not item['issuer']:
                item['issuer'] = response.css(
                    'meta[name="author"]::attr(content), .site-title::text, .footer .org-name::text, '
                    'div[class*="footer"]::text'
                ).get(default='').strip() or 'Unknown'
            self.logger.info(f"Scraped item: {item['title']} (Issuer: {item['issuer']})")
            yield item