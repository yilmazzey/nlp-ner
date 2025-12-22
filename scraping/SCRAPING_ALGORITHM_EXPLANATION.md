# Scraping Algorithm Explanation

## Overview

The scraping system uses an object-oriented architecture with a base class (`BaseNewsScraper`) that provides common functionality, and specific scrapers (`FoxNewsScraper`, `ViceScraper`) that implement source-specific logic.

---

## Base Scraping Algorithm (`BaseNewsScraper`)

### Core Components

1. **HTTP Request Handling**
   - Uses `requests` library with browser-like headers (User-Agent, Accept, etc.)
   - Implements exponential backoff retry mechanism (3 attempts)
   - Timeout set to 10 seconds per request
   - Error handling with graceful degradation

2. **Polite Scraping**
   - Random delays between requests (3-5 seconds)
   - Additional delays between categories (2-4 seconds)
   - Prevents server overload and mimics human behavior

3. **Text Extraction Strategy**
   - Multi-selector fallback approach: tries multiple CSS selectors in order
   - Deduplication: uses a set to track seen texts
   - Filtering: minimum length (30 characters), removes whitespace-only content
   - Text cleaning: normalizes whitespace using `' '.join(text.split())`

4. **Scraping Workflow**
   ```
   For each category:
     1. Get article URLs from category page
     2. For each article URL:
        a. Fetch article page
        b. Extract title (try multiple selectors)
        c. Extract paragraphs (try multiple selectors)
        d. Combine paragraphs into full text
        e. Add polite delay (3-5s)
     3. Add delay between categories (2-4s)
   ```

---

## Fox News Scraping Algorithm

### URL Collection (`get_article_urls`)

**Target Categories:**
- Politics: `https://www.foxnews.com/politics`
- Business: `https://www.foxnews.com/business`
- World: `https://www.foxnews.com/world`

**Algorithm:**
1. **Fetch category page** using base scraper's `_make_request()`
2. **Parse HTML** with BeautifulSoup
3. **Multi-selector strategy** - tries multiple CSS selectors:
   - `a[data-module="Article"]`
   - `article a[href*="/politics/"]`
   - `article a[href*="/business/"]`
   - `.headline a[href*="/politics/"]`
   - `h2 a[href*="/politics/"]`
   - `h3 a[href*="/politics/"]`
   - (Similar patterns for business/world)

4. **URL Normalization:**
   - Converts relative URLs to absolute (`/politics/...` → `https://www.foxnews.com/politics/...`)
   - Handles double slashes: `//www.foxnews.com//` → `//www.foxnews.com/`
   - Handles protocol-relative URLs: `//...` → `https://...`

5. **URL Filtering:**
   - **Include:** URLs containing `/politics/`, `/business/`, or `/world/`
   - **Exclude:**
     - Category pages: `/category/`
     - Videos: `/video/`
     - Opinion pieces: `/opinion/`
     - Shows: `/shows/`
     - Person pages: `/person/`
     - Tags: `/tag/`
     - Author pages: `/author/`
   - **Validation:** URL must have at least 5 path segments (ensures it's an article, not a listing page)
   - **Deduplication:** Uses a set to track seen URLs

6. **Return:** First `num_articles` unique article URLs

### Article Extraction (`scrape_article`)

**Algorithm:**
1. **Fetch article page** using base scraper's `_make_request()`
2. **Extract title** (fallback selectors):
   - `h1.headline`
   - `h1`
   - `.headline`
   - `[data-module="Article"] h1`

3. **Extract paragraphs** (fallback selectors):
   - `.article-body p` (primary)
   - `.article-text p`
   - `article p`
   - `.body-copy p`

4. **Text processing:**
   - Uses base scraper's `_extract_paragraphs()` with multi-selector fallback
   - Filters: minimum 30 characters, deduplication
   - Combines paragraphs with `\n\n` separator

5. **Return:** Dictionary with `{title, text, url, source}` or `None` if extraction fails

---

## Vice Scraping Algorithm

### URL Collection (`get_article_urls`)

**Target Categories:**
- Politics: `https://www.vice.com/en/tag/politics`
- Business: `https://www.vice.com/en/tag/business`

**Algorithm:**
1. **Fetch category page** using base scraper's `_make_request()`
2. **Parse HTML** with BeautifulSoup
3. **Link discovery:**
   - Finds all `<a>` tags with `href` attributes
   - Uses `soup.find_all('a', href=True)`

4. **URL Normalization:**
   - Converts relative URLs: `/en/article/...` → `https://www.vice.com/en/article/...`
   - Handles absolute URLs that contain `vice.com`

5. **URL Filtering:**
   - **Include:** URLs containing `/en/article/` (Vice article pattern)
   - **Exclude:**
     - Videos: `/video/`
     - Galleries: `/gallery/`
     - Tags: `/tag/`
     - Author pages: `/author/`, `/contributor/`
     - Category pages: `/category/`
     - Sections: `/section/`
     - Search: `/search`
     - Subscribe: `/subscribe`
     - Pagination: `/page/`
     - About/Privacy/Terms: `/about-`, `/privacy`, `/terms`
   - **Deduplication:** Uses a set to track seen URLs

6. **Return:** First `num_articles` unique article URLs

### Article Extraction (`scrape_article`)

**Algorithm:**
1. **Fetch article page** using base scraper's `_make_request()`
2. **Extract title** (fallback selectors):
   - `h1`
   - `.article-header h1`
   - `[data-testid="article-title"]`
   - `.headline`

3. **Extract paragraphs** (fallback selectors):
   - `.article__body p` (primary)
   - `.article-body p`
   - `article p`
   - `.content p`
   - `[data-testid="article-body"] p`

4. **Text processing:**
   - Uses base scraper's `_extract_paragraphs()` with multi-selector fallback
   - Filters: minimum 30 characters, deduplication
   - Combines paragraphs with `\n\n` separator

5. **Return:** Dictionary with `{title, text, url, source}` or `None` if extraction fails

---

## Final Dataset Processing (`scrape_all.py`)

### Orchestration Algorithm

1. **Initialize scrapers:**
   - `FoxNewsScraper()`
   - `ViceScraper()`

2. **For each scraper:**
   - Call `scrape_articles(categories, articles_per_category)`
   - Categories: `["business", "politics", "world"]`
   - Target: 40 articles per source (distributed across categories)

3. **Save full articles:**
   - Create metadata: `{total_articles, scraped_date, sources, source_counts}`
   - Save to `dataset2/raw_articles.json` with structure:
     ```json
     {
       "metadata": {...},
       "articles": [
         {
           "title": "...",
           "text": "...",
           "url": "...",
           "source": "...",
           "category": "..."
         }
       ]
     }
     ```

4. **Extract paragraphs:**
   - For each article:
     - Split text by `\n\n` (paragraph separator)
     - Filter: minimum 50 characters per paragraph
     - Create paragraph objects with metadata:
       ```json
       {
         "text": "...",
         "source": "...",
         "url": "...",
         "title": "...",
         "category": "..."
       }
       ```

5. **Save paragraphs:**
   - Save to `dataset2/raw_paragraphs.json` with same structure as articles

---

## Dataset Analysis Algorithm (`dataset2_analysis.ipynb`)

### Analysis Pipeline

1. **Data Loading:**
   - Load `raw_articles.json` → extract `articles` list
   - Load `raw_paragraphs.json` → extract `articles` list (paragraphs stored as "articles" in JSON structure)

2. **Basic Statistics:**
   - **Articles:**
     - Total count, source distribution
     - Character length: total, mean, median, min, max
     - Word count: total, mean, median, min, max
   
   - **Paragraphs:**
     - Total count, source distribution
     - Character length: mean, median, min, max
     - Word count: mean, median, min, max

3. **Source Distribution Analysis:**
   - Count articles by source (Fox News vs Vice)
   - Count paragraphs by source
   - Visualize with bar charts

4. **Text Length Distributions:**
   - Histogram of article character lengths
   - Histogram of paragraph character lengths
   - Overlay mean and median lines

5. **Source Comparison:**
   - Group articles by source
   - Calculate statistics (mean, median, min, max) for:
     - Character count
     - Word count
   - Box plots comparing sources

6. **Paragraph Analysis:**
   - Similar grouping and statistics for paragraphs
   - Visualizations comparing sources

### Key Findings (from analysis output):

- **Articles:** 30 total (15 Fox News, 15 Vice)
- **Paragraphs:** 551 total (393 Fox News, 158 Vice)
- **Article lengths:**
  - Average: 4,131 characters / 662 words
  - Median: 3,625 characters / 581 words
- **Paragraph lengths:**
  - Average: 213 characters / 34 words
  - Median: 185 characters / 30 words
- **Source differences:**
  - Fox News articles: longer on average (5,037 chars, 787 words)
  - Vice articles: more variable (3,225 chars avg, but max 15,135 chars)

---

## Key Design Decisions

1. **Multi-selector fallback:** Handles website structure changes gracefully
2. **Polite delays:** Prevents IP blocking and respects server resources
3. **Deduplication:** Ensures unique content in final dataset
4. **Error handling:** Continues scraping even if individual articles fail
5. **Paragraph extraction:** Splits articles into annotatable units (>50 chars)
6. **Metadata preservation:** Maintains source, URL, title, category for traceability









