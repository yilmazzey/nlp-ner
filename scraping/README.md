# News Scraping Module

This module provides web scrapers for collecting news articles from Fox News and Vice for COMP 451 Project #2 (NER with Prompt Engineering).

## Architecture Diagram

See [SCRAPING_ARCHITECTURE.md](SCRAPING_ARCHITECTURE.md) for detailed Mermaid diagrams showing:
- Scraping workflow
- Class hierarchy
- Data flow
- Error handling
- Source-specific implementations

## Sources

1. **Fox News** - Politics, Business
2. **Vice** - Politics

## Architecture

### Base Scraper (`base_scraper.py`)
- Common functionality: HTTP requests, error handling, polite delays
- Abstract base class that all specific scrapers inherit from
- Features:
  - User-Agent headers to mimic real browsers
  - Random delays (3-5 seconds) between requests
  - Retry logic with exponential backoff
  - Text cleaning utilities

### Source-Specific Scrapers
Each scraper implements:
- `get_article_urls(category, num_articles)`: Collects article URLs from category pages
- `scrape_article(url)`: Extracts title and text from a single article
- `scrape_articles(categories, articles_per_category)`: Orchestrates scraping multiple articles

## Usage

### Quick Start

Run the main orchestrator script to scrape from all sources:

```bash
cd /Users/zeynep_yilmaz/Desktop/ner_nlp
source venv311/bin/activate
python scraping/scrape_all.py
```

This will:
1. Scrape ~40 articles from each source (80 total)
2. Focus on "business" and "politics" categories
3. Save full articles to `dataset2/raw_articles.json`
4. Extract paragraphs to `dataset2/raw_paragraphs.json`

### Programmatic Usage

```python
from scraping import FoxNewsScraper, ViceScraper

# Scrape from a single source
fox = FoxNewsScraper()
articles = fox.scrape_articles(
    categories=["business", "politics"],
    articles_per_category=20
)

# Each article is a dict with:
# {
#     'title': str,
#     'text': str,
#     'url': str,
#     'source': str,
#     'category': str
# }
```

## Output Format

### Articles JSON (`raw_articles.json`)
```json
{
  "metadata": {
    "total_articles": 80,
    "scraped_date": "2025-01-XX...",
    "sources": ["Fox News", "Vice"],
    "source_counts": {
      "Fox News": 40,
      "Vice": 40
    }
  },
  "articles": [
    {
      "title": "Article Title",
      "text": "Full article text...",
      "url": "https://...",
      "source": "Fox News",
      "category": "business"
    }
  ]
}
```

### Paragraphs JSON (`raw_paragraphs.json`)
```json
{
  "metadata": {...},
  "articles": [
    {
      "text": "Single paragraph text...",
      "source": "Fox News",
      "url": "https://...",
      "title": "Article Title",
      "category": "business"
    }
  ]
}
```

## Ethical Scraping

- **Polite Delays**: 3-5 second random delays between requests
- **User-Agent**: Realistic browser headers
- **Error Handling**: Graceful failures, retries with backoff
- **Respectful**: Only scrapes public article pages, no paywall bypassing

## Requirements

All dependencies are in `requirements.txt`:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast HTML parser

## Notes

- Some websites may have anti-scraping measures
- Article selectors may need updates if websites change their HTML structure
- The scrapers use multiple fallback selectors to handle different page layouts
- Failed articles are logged but don't stop the scraping process

