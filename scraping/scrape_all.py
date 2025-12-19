"""
Main orchestrator script to scrape news articles from Fox News and Vice.
Collects 40 articles from each source (80 total).
Focuses on business, politics, regulations, and international affairs.
"""

import json
import os
import sys
from typing import List, Dict
from datetime import datetime
import logging

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scraping.foxnews_scraper import FoxNewsScraper
from scraping.vice_scraper import ViceScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scrape_all_sources(
    articles_per_source: int = 40,
    categories_per_source: List[str] = None
) -> List[Dict[str, str]]:
    """
    Scrape articles from Fox News and Vice.
    
    Args:
        articles_per_source: Number of articles to scrape per source (default: 40)
        categories_per_source: Categories to scrape per source (default: business, politics)
    
    Returns:
        List of article dictionaries
    """
    if categories_per_source is None:
        categories_per_source = ["business", "politics"]
    
    all_articles = []
    
    # Initialize scrapers
    scrapers = [
        FoxNewsScraper(),
        ViceScraper(),
    ]
    
    # Scrape from each source
    for scraper in scrapers:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting to scrape from {scraper.source_name}")
            logger.info(f"{'='*60}\n")
            
            articles = scraper.scrape_articles(
                categories=categories_per_source,
                articles_per_category=articles_per_source // len(categories_per_source)
            )
            
            all_articles.extend(articles)
            logger.info(f"✓ Collected {len(articles)} articles from {scraper.source_name}\n")
            
        except Exception as e:
            logger.error(f"Error scraping from {scraper.source_name}: {e}")
            continue
    
    return all_articles


def save_articles(articles: List[Dict[str, str]], output_path: str):
    """
    Save scraped articles to JSON file.
    
    Args:
        articles: List of article dictionaries
        output_path: Output file path
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Add metadata
    output_data = {
        'metadata': {
            'total_articles': len(articles),
            'scraped_date': datetime.now().isoformat(),
            'sources': list(set(article['source'] for article in articles)),
            'source_counts': {
                source: sum(1 for a in articles if a['source'] == source)
                for source in set(article['source'] for article in articles)
            }
        },
        'articles': articles
    }
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Saved {len(articles)} articles to {output_path}")
    logger.info(f"  Sources: {output_data['metadata']['source_counts']}")


def extract_paragraphs(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Extract individual paragraphs from articles for annotation.
    Each paragraph will be annotated separately.
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        List of paragraph dictionaries with 'text', 'source', 'url', 'title'
    """
    paragraphs = []
    
    for article in articles:
        # Split article text into paragraphs
        article_paragraphs = [
            para.strip() for para in article['text'].split('\n\n')
            if para.strip() and len(para.strip()) > 50  # Minimum paragraph length
        ]
        
        for para in article_paragraphs:
            paragraphs.append({
                'text': para,
                'source': article['source'],
                'url': article['url'],
                'title': article.get('title', ''),
                'category': article.get('category', ''),
            })
    
    return paragraphs


def main():
    """Main function to run the scraping pipeline."""
    # Configuration
    ARTICLES_PER_SOURCE = 40  # Target: 40 articles per source = 160 total
    CATEGORIES = ["business", "politics", "world"]  # Focus on business, politics, and world news
    
    # Output paths
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset2')
    ARTICLES_FILE = os.path.join(OUTPUT_DIR, 'raw_articles.json')
    PARAGRAPHS_FILE = os.path.join(OUTPUT_DIR, 'raw_paragraphs.json')
    
    logger.info("="*60)
    logger.info("News Scraping Pipeline - COMP 451 Project #2")
    logger.info("="*60)
    logger.info(f"Target: {ARTICLES_PER_SOURCE} articles per source")
    logger.info(f"Categories: {', '.join(CATEGORIES)}")
    logger.info(f"Sources: Fox News, Vice")
    logger.info("="*60 + "\n")
    
    # Scrape all sources
    articles = scrape_all_sources(
        articles_per_source=ARTICLES_PER_SOURCE,
        categories_per_source=CATEGORIES
    )
    
    if not articles:
        logger.error("No articles were scraped. Exiting.")
        return
    
    # Save full articles
    save_articles(articles, ARTICLES_FILE)
    
    # Extract paragraphs for annotation
    logger.info("\nExtracting paragraphs from articles...")
    paragraphs = extract_paragraphs(articles)
    logger.info(f"Extracted {len(paragraphs)} paragraphs")
    
    # Save paragraphs
    save_articles(paragraphs, PARAGRAPHS_FILE)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Scraping Summary")
    logger.info("="*60)
    logger.info(f"Total articles scraped: {len(articles)}")
    logger.info(f"Total paragraphs extracted: {len(paragraphs)}")
    logger.info(f"\nArticles saved to: {ARTICLES_FILE}")
    logger.info(f"Paragraphs saved to: {PARAGRAPHS_FILE}")
    logger.info("="*60)


if __name__ == "__main__":
    main()

