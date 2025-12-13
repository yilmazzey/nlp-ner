"""
Web scraper for news articles from BBC, Hurriyet, and other news sites.
Extracts clean text paragraphs for Dataset2 annotation.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from typing import List, Dict
import yaml
from newspaper import Article


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def scrape_bbc_article(url: str) -> List[str]:
    """
    Scrape a BBC news article and extract paragraphs.
    
    Args:
        url (str): URL of the article
    
    Returns:
        list: List of paragraph texts
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find article body
        article_body = soup.find('article') or soup.find('div', {'data-component': 'text-block'})
        
        if not article_body:
            # Try alternative selectors
            article_body = soup.find('div', class_='story-body')
        
        paragraphs = []
        if article_body:
            # Find all paragraph tags
            for p in article_body.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Filter out very short paragraphs
                    paragraphs.append(text)
        
        return paragraphs
    
    except Exception as e:
        print(f"Error scraping BBC article {url}: {e}")
        return []


def scrape_hurriyet_article(url: str) -> List[str]:
    """
    Scrape a Hurriyet news article and extract paragraphs.
    
    Args:
        url (str): URL of the article
    
    Returns:
        list: List of paragraph texts
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find article content
        article_content = soup.find('div', class_='news-content') or soup.find('article')
        
        paragraphs = []
        if article_content:
            for p in article_content.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    paragraphs.append(text)
        
        return paragraphs
    
    except Exception as e:
        print(f"Error scraping Hurriyet article {url}: {e}")
        return []


def scrape_with_newspaper3k(url: str) -> List[str]:
    """
    Scrape article using newspaper3k library (fallback method).
    
    Args:
        url (str): URL of the article
    
    Returns:
        list: List of paragraph texts
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Split article text into paragraphs
        paragraphs = [p.strip() for p in article.text.split('\n') if p.strip() and len(p.strip()) > 20]
        
        return paragraphs
    
    except Exception as e:
        print(f"Error scraping with newspaper3k {url}: {e}")
        return []


def get_article_urls_from_homepage(base_url: str, num_articles: int = 10) -> List[str]:
    """
    Get article URLs from a news homepage.
    
    Args:
        base_url (str): Base URL of the news site
        num_articles (int): Number of article URLs to collect
    
    Returns:
        list: List of article URLs
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find article links
        article_urls = []
        
        # Common patterns for article links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # Make absolute URL
                if href.startswith('/'):
                    href = base_url.rstrip('/') + href
                elif not href.startswith('http'):
                    continue
                
                # Filter for article URLs
                if any(keyword in href.lower() for keyword in ['/news/', '/article/', '/story/', '/haber/']):
                    if href not in article_urls:
                        article_urls.append(href)
                        if len(article_urls) >= num_articles:
                            break
        
        return article_urls[:num_articles]
    
    except Exception as e:
        print(f"Error getting article URLs from {base_url}: {e}")
        return []


def scrape_news_articles(num_paragraphs: int = 70) -> List[Dict]:
    """
    Scrape news articles and collect paragraphs.
    
    Args:
        num_paragraphs (int): Target number of paragraphs to collect
    
    Returns:
        list: List of paragraph dictionaries with 'text' and 'source' keys
    """
    config = load_config()
    scraping_config = config.get('scraping', {})
    urls = scraping_config.get('urls', [])
    
    all_paragraphs = []
    
    print(f"Scraping news articles to collect {num_paragraphs} paragraphs...")
    
    # Try to get article URLs from homepages
    article_urls = []
    for base_url in urls:
        print(f"Getting article URLs from {base_url}...")
        urls_from_homepage = get_article_urls_from_homepage(base_url, num_articles=10)
        article_urls.extend(urls_from_homepage)
        time.sleep(2)  # Be polite with requests
    
    # If we don't have enough URLs, use some default article URLs
    if len(article_urls) < 5:
        # Add some example URLs (these may need to be updated)
        if 'bbc.com' in str(urls):
            article_urls.extend([
                'https://www.bbc.com/news/world',
                'https://www.bbc.com/news/technology',
                'https://www.bbc.com/news/science-environment'
            ])
    
    # Scrape articles
    for i, url in enumerate(article_urls[:20]):  # Limit to 20 articles
        print(f"Scraping article {i+1}/{min(len(article_urls), 20)}: {url}")
        
        paragraphs = []
        
        # Try different scraping methods
        if 'bbc.com' in url:
            paragraphs = scrape_bbc_article(url)
        elif 'hurriyet.com.tr' in url:
            paragraphs = scrape_hurriyet_article(url)
        else:
            paragraphs = scrape_with_newspaper3k(url)
        
        # Add paragraphs with source
        for para in paragraphs:
            all_paragraphs.append({
                'text': para,
                'source': url
            })
        
        if len(all_paragraphs) >= num_paragraphs:
            break
        
        time.sleep(2)  # Be polite with requests
    
    # If we still don't have enough, add some example paragraphs
    if len(all_paragraphs) < num_paragraphs:
        print(f"Warning: Only collected {len(all_paragraphs)} paragraphs. Adding example paragraphs...")
        example_paragraphs = [
            "The United Nations announced a new climate initiative on Monday.",
            "Apple Inc. released its latest iPhone model in September.",
            "President Joe Biden visited London last week for diplomatic talks.",
            "Microsoft Corporation reported record profits this quarter.",
            "Scientists discovered a new species in the Amazon rainforest.",
            "The European Union approved new trade regulations.",
            "Elon Musk announced plans for a new space mission.",
            "Tokyo hosted the Olympic Games in 2021.",
            "Amazon.com expanded its operations to new markets.",
            "The World Health Organization issued new health guidelines."
        ]
        
        for para in example_paragraphs:
            if len(all_paragraphs) >= num_paragraphs:
                break
            all_paragraphs.append({
                'text': para,
                'source': 'example'
            })
    
    print(f"Collected {len(all_paragraphs)} paragraphs")
    return all_paragraphs[:num_paragraphs]


def save_paragraphs(paragraphs: List[Dict], output_path: str):
    """
    Save paragraphs to JSON file.
    
    Args:
        paragraphs (list): List of paragraph dictionaries
        output_path (str): Output file path
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(paragraphs, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(paragraphs)} paragraphs to {output_path}")


def main():
    """Main function to run the scraper"""
    config = load_config()
    scraping_config = config.get('scraping', {})
    num_paragraphs = scraping_config.get('num_paragraphs', 70)
    output_file = scraping_config.get('output_file', 'dataset2/raw_news.json')
    
    paragraphs = scrape_news_articles(num_paragraphs=num_paragraphs)
    save_paragraphs(paragraphs, output_file)
    
    print(f"\nScraping complete! Collected {len(paragraphs)} paragraphs.")


if __name__ == "__main__":
    main()


