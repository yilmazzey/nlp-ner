"""
Web scraping module for news articles.
Provides scrapers for Fox News and Vice.
"""

from .base_scraper import BaseNewsScraper
from .foxnews_scraper import FoxNewsScraper
from .vice_scraper import ViceScraper

__all__ = [
    'BaseNewsScraper',
    'FoxNewsScraper',
    'ViceScraper',
]

