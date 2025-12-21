"""
Base scraper class with common functionality for all news sources.
Provides headers, delays, error handling, and common utilities.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseNewsScraper(ABC):
    """
    Base class for news scrapers with common functionality.
    All specific scrapers should inherit from this class.
    """
    
    def __init__(self, source_name: str, base_url: str, min_delay: float = 3.0, max_delay: float = 5.0):
        """
        Initialize base scraper.
        
        Args:
            source_name: Name of the news source (e.g., "Reuters")
            base_url: Base URL of the news website
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
        """
        self.source_name = source_name
        self.base_url = base_url
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        # Standard headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _make_request(self, url: str, timeout: int = 10, retries: int = 3) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling and retries.
        
        Args:
            url: URL to request
            timeout: Request timeout in seconds
            retries: Number of retry attempts
        
        Returns:
            Response object or None if all retries fail
        """
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def _polite_delay(self):
        """Add a random delay between requests to be polite."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace.
        
        Args:
            text: Raw text string
        
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        return text.strip()
    
    def _extract_paragraphs(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """
        Extract paragraphs using multiple CSS selectors (fallback strategy).
        
        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try
        
        Returns:
            List of paragraph texts
        """
        paragraphs = []
        seen_texts = set()  # Avoid duplicates
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = self._clean_text(elem.get_text())
                    # Filter: minimum length, not duplicate, not just whitespace
                    if text and len(text) > 30 and text not in seen_texts:
                        paragraphs.append(text)
                        seen_texts.add(text)
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return paragraphs
    
    @abstractmethod
    def get_article_urls(self, category: str, num_articles: int = 25) -> List[str]:
        """
        Get article URLs from a category/section page.
        Must be implemented by each specific scraper.
        
        Args:
            category: Category name (e.g., "business", "politics")
            num_articles: Number of article URLs to collect
        
        Returns:
            List of article URLs
        """
        pass
    
    @abstractmethod
    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single article and extract content.
        Must be implemented by each specific scraper.
        
        Args:
            url: Article URL
        
        Returns:
            Dictionary with 'title', 'text', 'url', 'source' keys, or None if failed
        """
        pass
    
    def scrape_articles(self, categories: List[str], articles_per_category: int = 25) -> List[Dict[str, str]]:
        """
        Scrape multiple articles from multiple categories.
        
        Args:
            categories: List of category names to scrape
            articles_per_category: Number of articles to scrape per category
        
        Returns:
            List of article dictionaries
        """
        all_articles = []
        
        for category in categories:
            logger.info(f"[{self.source_name}] Scraping {category} category...")
            
            # Get article URLs
            article_urls = self.get_article_urls(category, num_articles=articles_per_category)
            logger.info(f"[{self.source_name}] Found {len(article_urls)} article URLs in {category}")
            
            # Scrape each article
            for i, url in enumerate(article_urls):
                logger.info(f"[{self.source_name}] Scraping article {i+1}/{len(article_urls)}: {url[:80]}...")
                
                article = self.scrape_article(url)
                if article:
                    article['category'] = category
                    all_articles.append(article)
                else:
                    logger.warning(f"[{self.source_name}] Failed to scrape: {url}")
                
                # Polite delay between articles
                if i < len(article_urls) - 1:
                    self._polite_delay()
            
            # Extra delay between categories
            if category != categories[-1]:
                time.sleep(random.uniform(2, 4))
        
        logger.info(f"[{self.source_name}] Successfully scraped {len(all_articles)} articles")
        return all_articles







