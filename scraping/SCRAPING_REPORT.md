# News Scraping Report - COMP 451 Project #2

**Date:** December 19, 2025  
**Project:** Named Entity Recognition with Prompt Engineering

## Summary

Successfully scraped news articles from multiple sources to create Dataset2 for NER annotation. Collected **424 paragraphs** from **2 sources**, exceeding the project requirement of 50-100 samples.

## Sources Used

### 1. Fox News
- **Status:** ✅ Working
- **Articles Collected:** 12
- **Paragraphs Extracted:** 252
- **Categories:** Politics, Business
- **URL:** https://www.foxnews.com

### 2. Vice
- **Status:** ✅ Working
- **Articles Collected:** 18
- **Paragraphs Extracted:** 172
- **Categories:** Politics
- **URL:** https://www.vice.com/en/tag/politics/

### 3. Reuters
- **Status:** ❌ Blocked (401 Forbidden)
- **Reason:** Anti-scraping measures detected
- **Attempted:** Business, Finance, World categories

### 4. AP News
- **Status:** ⚠️ Selector Issues
- **Reason:** CSS selectors need updating for current page structure
- **Attempted:** Business, Politics categories

### 5. ABC News
- **Status:** ✅ Ready (URLs collected but not fully tested)
- **URLs Collected:** 40
- **Note:** Available for future scraping runs

## Final Dataset Statistics

### Articles
- **Total Articles:** 30
- **Fox News:** 12 articles
- **Vice:** 18 articles

### Paragraphs
- **Total Paragraphs:** 424
- **Fox News:** 252 paragraphs
- **Vice:** 172 paragraphs

### Quality Metrics
- ✅ Meets requirement: 424 paragraphs (requirement: 50-100)
- ✅ Multiple sources: 2 different sources
- ✅ Entity-rich content: Politics, business, international affairs
- ✅ Proper format: JSON with metadata

## Output Files

- `dataset2/raw_articles.json` - Full articles with metadata
- `dataset2/raw_paragraphs.json` - Individual paragraphs for annotation

## Technical Details

### Scraping Method
- **Tool:** BeautifulSoup4 + Python requests
- **Approach:** Ethical scraping with:
  - Polite delays (3-5 seconds between requests)
  - Proper User-Agent headers
  - Error handling and retries
  - Respect for robots.txt guidelines

### Scripts Used
- `scrape_vice.py` - Vice-specific scraper (successful)
- `scrape_all.py` - Main orchestrator for all sources
- `base_scraper.py` - Base class with common functionality
- Source-specific scrapers: `foxnews_scraper.py`, `vice_scraper.py`, etc.

## Challenges Encountered

1. **Reuters Blocking:** 401 Forbidden errors due to anti-scraping measures
   - **Solution:** Skipped Reuters, used alternative sources

2. **AP News Selectors:** CSS selectors didn't match current page structure
   - **Solution:** Updated selectors, but needs further refinement

3. **Vice JavaScript:** Initial scraper had issues with JavaScript-rendered content
   - **Solution:** Created direct requests approach in `scrape_vice.py`

## Recommendations

1. **For Production:** Consider using news APIs (NewsAPI, Guardian API) for more reliable access
2. **For Reuters:** Try RSS feeds or API access if available
3. **For AP News:** Inspect live page HTML and update selectors
4. **Future Sources:** CNN, BBC, or other scraper-friendly news sites

## Next Steps

1. ✅ Dataset2 collection complete (424 paragraphs)
2. ⏭️ Annotate paragraphs using best LLM+prompt combination
3. ⏭️ Format as `dataset2/final_annotated.json` for submission

## Files Structure

```
scraping/
├── base_scraper.py          # Base scraper class
├── foxnews_scraper.py       # Fox News scraper
├── vice_scraper.py          # Vice scraper
├── reuters_scraper.py       # Reuters scraper (blocked)
├── apnews_scraper.py        # AP News scraper (needs fixes)
├── abcnews_scraper.py       # ABC News scraper
├── scrape_all.py            # Main orchestrator
├── scrape_vice.py           # Vice-specific script (successful)
├── collect_urls.py          # URL collection utility
├── run_scraping.sh          # Shell script for easy execution
├── README.md                # Main documentation
└── SCRAPING_INSTRUCTIONS.md # Detailed instructions
```

## Conclusion

Successfully collected 424 paragraphs from 2 reliable sources (Fox News and Vice), exceeding the project requirement. The dataset is ready for annotation using the best-performing LLM and prompt combination from the evaluation phase.

