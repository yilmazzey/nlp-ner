"""
Script to automatically collect article URLs from category pages.
This avoids needing to manually collect URLs.
Run this first to get URLs, then use scrape_all.py to scrape them.
"""

import json
import os
import sys
from typing import List

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scraping.foxnews_scraper import FoxNewsScraper
from scraping.vice_scraper import ViceScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_urls_from_all_sources(target_per_source: int = 40) -> dict:
    """
    Collect article URLs from Fox News and Vice automatically.
    
    Args:
        target_per_source: Number of URLs to collect per source
    
    Returns:
        Dictionary mapping source names to lists of URLs
    """
    all_urls = {}
    
    scrapers = [
        ("Fox News", FoxNewsScraper(), ["politics", "business"]),
        ("Vice", ViceScraper(), ["politics"]),
    ]
    
    for source_name, scraper, categories in scrapers:
        logger.info(f"\n{'='*60}")
        logger.info(f"Collecting URLs from {source_name}")
        logger.info(f"{'='*60}\n")
        
        urls = []
        per_category = target_per_source // len(categories) + 1
        
        for category in categories:
            try:
                category_urls = scraper.get_article_urls(category, num_articles=per_category)
                urls.extend(category_urls)
                logger.info(f"  {category}: {len(category_urls)} URLs")
            except Exception as e:
                logger.error(f"  Error in {category}: {e}")
        
        # Deduplicate and limit
        urls = list(dict.fromkeys(urls))[:target_per_source]  # Preserve order, remove dupes
        all_urls[source_name] = urls
        logger.info(f"\n✓ {source_name}: Collected {len(urls)} unique URLs\n")
    
    return all_urls


def save_urls(urls_dict: dict, output_file: str = "scraping/collected_urls.json"):
    """Save collected URLs to JSON file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(urls_dict, f, indent=2, ensure_ascii=False)
    
    total = sum(len(urls) for urls in urls_dict.values())
    logger.info(f"✓ Saved {total} URLs to {output_file}")
    logger.info(f"  Breakdown: {', '.join(f'{k}: {len(v)}' for k, v in urls_dict.items())}")


def main():
    """Main function to collect URLs."""
    logger.info("="*60)
    logger.info("Article URL Collection - COMP 451 Project #2")
    logger.info("="*60)
    logger.info("Collecting 40 URLs from each of 2 sources...")
    logger.info("Sources: Fox News, Vice")
    logger.info("="*60 + "\n")
    
    urls = collect_urls_from_all_sources(target_per_source=40)
    
    save_urls(urls, "scraping/collected_urls.json")
    
    logger.info("\n" + "="*60)
    logger.info("URL Collection Complete!")
    logger.info("="*60)
    logger.info("Next step: Run 'python scraping/scrape_all.py' to scrape these URLs")
    logger.info("="*60)


if __name__ == "__main__":
    main()

