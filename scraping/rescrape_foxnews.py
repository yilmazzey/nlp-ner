"""
Re-scrape Fox News with fixed scraper to get proper full articles.
Replaces old category page data with actual article content.
"""

import json
import os
import sys
import time
import random
from datetime import datetime
import logging

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scraping.foxnews_scraper import FoxNewsScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_paragraphs(articles: list) -> list:
    """Extract individual paragraphs from articles."""
    paragraphs = []
    for article in articles:
        article_paragraphs = [
            para.strip() for para in article['text'].split('\n\n')
            if para.strip() and len(para.strip()) > 50
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
    """Re-scrape Fox News with fixed scraper."""
    # Load existing dataset
    articles_file = 'dataset2/raw_articles.json'
    paragraphs_file = 'dataset2/raw_paragraphs.json'
    
    existing_articles = []
    existing_paragraphs = []
    
    if os.path.exists(articles_file):
        with open(articles_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Keep only Vice articles, remove Fox News
            existing_articles = [a for a in data.get('articles', []) if a['source'] != 'Fox News']
            logger.info(f"Keeping {len(existing_articles)} existing articles (Vice)")
    
    if os.path.exists(paragraphs_file):
        with open(paragraphs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Keep only Vice paragraphs, remove Fox News
            existing_paragraphs = [p for p in data.get('articles', []) if p['source'] != 'Fox News']
            logger.info(f"Keeping {len(existing_paragraphs)} existing paragraphs (Vice)")
    
    # Scrape Fox News with fixed scraper
    logger.info("="*60)
    logger.info("Re-scraping Fox News with Fixed Scraper")
    logger.info("="*60)
    
    scraper = FoxNewsScraper()
    categories = ["politics", "business"]
    target_per_category = 15  # Get 15 articles per category = 30 total
    
    new_fox_articles = []
    for category in categories:
        logger.info(f"\nScraping {category} category...")
        article_urls = scraper.get_article_urls(category, num_articles=target_per_category)
        logger.info(f"Found {len(article_urls)} article URLs")
        
        for i, url in enumerate(article_urls):
            logger.info(f"  Scraping article {i+1}/{len(article_urls)}: {url[:80]}...")
            article = scraper.scrape_article(url)
            if article:
                article['category'] = category
                new_fox_articles.append(article)
                logger.info(f"    ✓ Got {len(article['text'])} chars, {len(article['text'].split())} words")
            else:
                logger.warning(f"    ✗ Failed to scrape")
            
            # Polite delay
            if i < len(article_urls) - 1:
                time.sleep(random.uniform(3, 5))
        
        # Extra delay between categories
        if category != categories[-1]:
            time.sleep(random.uniform(2, 4))
    
    logger.info(f"\n✓ Successfully scraped {len(new_fox_articles)} Fox News articles")
    
    # Combine with existing articles
    all_articles = existing_articles + new_fox_articles
    
    # Extract paragraphs
    logger.info("\nExtracting paragraphs...")
    new_fox_paragraphs = extract_paragraphs(new_fox_articles)
    all_paragraphs = existing_paragraphs + new_fox_paragraphs
    
    # Save combined dataset
    os.makedirs('dataset2', exist_ok=True)
    
    # Save articles
    articles_data = {
        'metadata': {
            'total_articles': len(all_articles),
            'scraped_date': datetime.now().isoformat(),
            'sources': list(set(a['source'] for a in all_articles)),
            'source_counts': {
                source: sum(1 for a in all_articles if a['source'] == source)
                for source in set(a['source'] for a in all_articles)
            }
        },
        'articles': all_articles
    }
    
    with open(articles_file, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, indent=2, ensure_ascii=False)
    
    # Save paragraphs
    paragraphs_data = {
        'metadata': {
            'total_articles': len(all_paragraphs),
            'scraped_date': datetime.now().isoformat(),
            'sources': list(set(p['source'] for p in all_paragraphs)),
            'source_counts': {
                source: sum(1 for p in all_paragraphs if p['source'] == source)
                for source in set(p['source'] for p in all_paragraphs)
            }
        },
        'articles': all_paragraphs
    }
    
    with open(paragraphs_file, 'w', encoding='utf-8') as f:
        json.dump(paragraphs_data, f, indent=2, ensure_ascii=False)
    
    logger.info("="*60)
    logger.info("Re-scraping Complete!")
    logger.info("="*60)
    logger.info(f"Total articles: {len(all_articles)}")
    logger.info(f"Total paragraphs: {len(all_paragraphs)}")
    logger.info(f"Source breakdown: {articles_data['metadata']['source_counts']}")
    logger.info(f"\nArticles saved to: {articles_file}")
    logger.info(f"Paragraphs saved to: {paragraphs_file}")
    logger.info("="*60)


if __name__ == "__main__":
    main()







