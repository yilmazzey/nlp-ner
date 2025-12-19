"""
Fox News scraper for politics and business news.
Targets: https://www.foxnews.com/politics, https://www.foxnews.com/business
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from .base_scraper import BaseNewsScraper
import logging

logger = logging.getLogger(__name__)


class FoxNewsScraper(BaseNewsScraper):
    """Scraper for Fox News articles."""
    
    def __init__(self):
        super().__init__(
            source_name="Fox News",
            base_url="https://www.foxnews.com",
            min_delay=3.0,
            max_delay=5.0
        )
        
        # Category URLs
        self.category_urls = {
            "politics": "https://www.foxnews.com/politics",
            "business": "https://www.foxnews.com/business",
            "world": "https://www.foxnews.com/world",
        }
    
    def get_article_urls(self, category: str, num_articles: int = 25) -> List[str]:
        """
        Get article URLs from Fox News category pages.
        
        Args:
            category: Category name (politics, business, world)
            num_articles: Number of article URLs to collect
        
        Returns:
            List of article URLs
        """
        category_url = self.category_urls.get(category)
        if not category_url:
            logger.warning(f"Unknown category: {category}")
            return []
        
        response = self._make_request(category_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        article_urls = []
        
        # Fox News article link patterns - target actual articles, not category pages
        selectors = [
            'a[data-module="Article"]',
            'article a[href*="/politics/"]',
            'article a[href*="/business/"]',
            'article a[href*="/world/"]',
            '.headline a[href*="/politics/"]',
            '.headline a[href*="/business/"]',
            '.headline a[href*="/world/"]',
            'h2 a[href*="/politics/"]',
            'h2 a[href*="/business/"]',
            'h3 a[href*="/politics/"]',
            'h3 a[href*="/business/"]',
        ]
        
        seen_urls = set()
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Make absolute URL
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif href.startswith('http') and 'foxnews.com' in href:
                    full_url = href
                elif href.startswith('//'):
                    full_url = 'https:' + href
                else:
                    continue
                
                # Clean up double slashes
                full_url = full_url.replace('//www.foxnews.com//', '//www.foxnews.com/')
                full_url = full_url.replace('https://www.foxnews.com//', 'https://www.foxnews.com/')
                
                # Filter for article URLs - EXCLUDE category pages, include only actual articles
                # Articles have pattern: /politics/article-slug or /business/article-slug
                # Category pages have: /category/politics/... or /politics/ (without article slug)
                if any(pattern in full_url for pattern in ['/politics/', '/business/', '/world/']) and \
                   full_url not in seen_urls and \
                   '/category/' not in full_url and \
                   not any(exclude in full_url for exclude in ['/video/', '/opinion/', '/shows/', '/person/', '/tag/', '/author/']) and \
                   len(full_url.split('/')) >= 5:
                    article_urls.append(full_url)
                    seen_urls.add(full_url)
                    
                    if len(article_urls) >= num_articles:
                        break
            
            if len(article_urls) >= num_articles:
                break
        
        return article_urls[:num_articles]
    
    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single Fox News article.
        
        Args:
            url: Article URL
        
        Returns:
            Dictionary with article data or None if failed
        """
        response = self._make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        title_selectors = [
            'h1.headline',
            'h1',
            '.headline',
            '[data-module="Article"] h1',
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = self._clean_text(title_elem.get_text())
                break
        
        # Extract article body paragraphs
        paragraph_selectors = [
            '.article-body p',  # Fox News main content selector
            '.article-text p',
            'article p',
            '.body-copy p',
        ]
        
        paragraphs = self._extract_paragraphs(soup, paragraph_selectors)
        
        if not paragraphs:
            logger.warning(f"No paragraphs found in {url}")
            return None
        
        # Combine paragraphs into full text
        full_text = '\n\n'.join(paragraphs)
        
        return {
            'title': title,
            'text': full_text,
            'url': url,
            'source': self.source_name,
        }

