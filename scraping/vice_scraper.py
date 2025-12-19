"""
Vice News scraper for politics and business news.
Targets: https://www.vice.com/en/tag/politics/
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from .base_scraper import BaseNewsScraper
import logging

logger = logging.getLogger(__name__)


class ViceScraper(BaseNewsScraper):
    """Scraper for Vice News articles."""
    
    def __init__(self):
        super().__init__(
            source_name="Vice",
            base_url="https://www.vice.com",
            min_delay=3.0,
            max_delay=5.0
        )
        
        # Category URLs
        self.category_urls = {
            "politics": "https://www.vice.com/en/tag/politics",
            "business": "https://www.vice.com/en/tag/business",
        }
    
    def get_article_urls(self, category: str, num_articles: int = 25) -> List[str]:
        """
        Get article URLs from Vice category pages.
        
        Args:
            category: Category name (politics, business)
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
        
        # Vice article link patterns - find all links and filter
        # Vice uses /en/article/[slug]/ format
        all_links = soup.find_all('a', href=True)
        
        seen_urls = set()
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Make absolute URL
            if href.startswith('/'):
                full_url = self.base_url + href
            elif href.startswith('http') and 'vice.com' in href:
                full_url = href
            else:
                continue
            
            # Filter for article URLs - Vice uses /en/article/[slug]/ format
            # Exclude video, gallery, tag pages, author pages, category pages, etc.
            if '/en/article/' in full_url and \
               full_url not in seen_urls and \
               not any(exclude in full_url for exclude in ['/video/', '/gallery/', '/tag/', '/author/', '/contributor/', '/category/', '/section/', '/search', '/subscribe', '/page/', '/about-', '/privacy', '/terms']):
                article_urls.append(full_url)
                seen_urls.add(full_url)
                
                if len(article_urls) >= num_articles:
                    break
        
        return article_urls[:num_articles]
    
    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single Vice article.
        
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
            'h1',
            '.article-header h1',
            '[data-testid="article-title"]',
            '.headline',
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = self._clean_text(title_elem.get_text())
                break
        
        # Extract article body paragraphs
        paragraph_selectors = [
            '.article__body p',  # Vice main content selector
            '.article-body p',
            'article p',
            '.content p',
            '[data-testid="article-body"] p',
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

