import os
import requests
from fake_useragent import UserAgent
import logging
from bs4 import BeautifulSoup
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_urls(query, serpapi_key=None, retries=5, delay=3):
    """Fetch URLs from SerpAPI or DuckDuckGo with retries."""
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    
    if serpapi_key:
        base_url = "https://serpapi.com/search"
        params = {'q': query, 'api_key': serpapi_key}
        for attempt in range(retries):
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"SerpAPI raw response for '{query}': {data}")
                    urls = [result['link'] for result in data.get('organic_results', []) if 'link' in result]
                    if not urls:
                        logger.warning(f"No URLs found in SerpAPI response for '{query}'")
                    else:
                        logger.info(f"Found {len(urls)} URLs for query: {query}")
                    return urls
                logger.warning(f"SerpAPI failed for '{query}': Status {response.status_code}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"SerpAPI error for '{query}': {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
    else:
        base_url = "https://html.duckduckgo.com/html/"
        params = {'q': query}
        for attempt in range(retries):
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = soup.select('a.result__a')
                    urls = [link.get('href') for link in links if link.get('href')]
                    logger.info(f"Found {len(urls)} URLs for query: {query}")
                    return urls
                logger.warning(f"DuckDuckGo failed for '{query}': Status {response.status_code}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"DuckDuckGo error for '{query}': {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
    logger.error(f"No URLs found for query: {query} after {retries} retries")
    return []

def index_urls(index_file='indexed_urls.json'):
    """Index URLs from search results."""
    ua = UserAgent()
    queries = [
        'tender notice nepal bhutan information security audit',
        'tender notice nepal bhutan vapt 2025',
        'tender notice nepal bhutan iso 27001 2025',
        'tender notice nepal bhutan information security audit 2025',
        'eoi nepal bhutan tender tender',
        'procurement notice nepal bhutan',
        "Information security audit tender notice 2025"
    ]
    all_urls = set()
    serpapi_key = "4a1b46237a4fc281f818c074a8fd94863049a08dd855a1eb7b18e05829219a34"
    logger.info(f"Using SerpAPI key: {serpapi_key[:4]}...{serpapi_key[-4:]}")
    for query in queries:
        logger.info(f"Searching for: {query}")
        urls = search_urls(query, serpapi_key)
        all_urls.update(urls)
    
    if not all_urls:
        logger.error("No URLs found from any search queries. Indexing aborted.")
        return
    
    indexed_data = []
    for url in all_urls:
        try:
            logger.info(f"Indexing {url}")
            response = requests.get(url, headers={'User-Agent': ua.random}, timeout=5, verify=False)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else ''
                content = soup.get_text(separator=' ', strip=True)[:2000]
                indexed_data.append({'url': url, 'title': title, 'content': content})
                logger.info(f"Successfully indexed {url}")
            else:
                logger.warning(f"Failed to fetch {url}: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Error indexing {url}: {e}")
            continue
    
    if not indexed_data:
        logger.error("No URLs successfully indexed. Saving empty index file.")
    
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(indexed_data, f, indent=2)
        logger.info(f"Indexed URLs saved to {index_file}")
    except Exception as e:
        logger.error(f"Error saving indexed URLs: {e}")