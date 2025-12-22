"""
Script to scrape Vice articles and append to existing dataset.
Uses direct requests approach that works with Vice.
"""

import json
import os
import sys
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_vice_article_urls(category_url: str, num_articles: int = 40) -> list:
    """Get article URLs from Vice category page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(category_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        article_urls = []
        seen_urls = set()
        
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # Make absolute URL
            if href.startswith('/'):
                full_url = 'https://www.vice.com' + href
            elif href.startswith('http') and 'vice.com' in href:
                full_url = href
            else:
                continue
            
            # Filter for article URLs
            if '/en/article/' in full_url and \
               full_url not in seen_urls and \
               not any(exclude in full_url for exclude in ['/video/', '/gallery/', '/tag/', '/author/', '/contributor/', '/category/', '/section/', '/search', '/subscribe', '/page/', '/about-', '/privacy', '/terms']):
                article_urls.append(full_url)
                seen_urls.add(full_url)
                
                if len(article_urls) >= num_articles:
                    break
        
        return article_urls
    except Exception as e:
        logger.error(f"Error getting URLs from {category_url}: {e}")
        return []


def scrape_vice_article(url: str) -> dict:
    """Scrape a single Vice article."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        title_elem = soup.find('h1')
        if title_elem:
            title = ' '.join(title_elem.get_text().split())
        
        # Extract paragraphs
        paragraphs = []
        paragraph_selectors = [
            '.article__body p',
            '.article-body p',
            'article p',
            '.content p',
        ]
        
        for selector in paragraph_selectors:
            paras = soup.select(selector)
            if paras:
                for p in paras:
                    text = ' '.join(p.get_text().split())
                    if text and len(text) > 30:
                        paragraphs.append(text)
                break
        
        if not paragraphs:
            logger.warning(f"No paragraphs found in {url}")
            return None
        
        full_text = '\n\n'.join(paragraphs)
        
        return {
            'title': title,
            'text': full_text,
            'url': url,
            'source': 'Vice',
            'category': 'politics',
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None


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
    """Main function to scrape Vice and append to existing dataset."""
    # Load existing dataset if it exists
    articles_file = 'dataset2/raw_articles.json'
    paragraphs_file = 'dataset2/raw_paragraphs.json'
    
    existing_articles = []
    existing_paragraphs = []
    
    if os.path.exists(articles_file):
        with open(articles_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_articles = data.get('articles', [])
            logger.info(f"Loaded {len(existing_articles)} existing articles")
    
    if os.path.exists(paragraphs_file):
        with open(paragraphs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_paragraphs = data.get('articles', [])
            logger.info(f"Loaded {len(existing_paragraphs)} existing paragraphs")
    
    # Scrape Vice articles
    logger.info("="*60)
    logger.info("Scraping Vice Politics Articles")
    logger.info("="*60)
    
    category_url = "https://www.vice.com/en/tag/politics/"
    target_articles = 40
    
    logger.info(f"Collecting URLs from {category_url}...")
    urls = get_vice_article_urls(category_url, num_articles=target_articles)
    logger.info(f"Found {len(urls)} article URLs")
    
    if not urls:
        logger.error("No URLs found. Exiting.")
        return
    
    # Scrape articles
    new_articles = []
    for i, url in enumerate(urls):
        logger.info(f"Scraping article {i+1}/{len(urls)}: {url[:80]}...")
        article = scrape_vice_article(url)
        if article:
            new_articles.append(article)
        
        # Polite delay
        if i < len(urls) - 1:
            time.sleep(random.uniform(3, 5))
    
    logger.info(f"Successfully scraped {len(new_articles)} articles from Vice")
    
    # Combine with existing articles
    all_articles = existing_articles + new_articles
    
    # Extract paragraphs
    logger.info("Extracting paragraphs...")
    new_paragraphs = extract_paragraphs(new_articles)
    all_paragraphs = existing_paragraphs + new_paragraphs
    
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
    logger.info("Scraping Complete!")
    logger.info("="*60)
    logger.info(f"Total articles: {len(all_articles)}")
    logger.info(f"Total paragraphs: {len(all_paragraphs)}")
    logger.info(f"Source breakdown: {articles_data['metadata']['source_counts']}")
    logger.info(f"\nArticles saved to: {articles_file}")
    logger.info(f"Paragraphs saved to: {paragraphs_file}")
    logger.info("="*60)


if __name__ == "__main__":
    main()









