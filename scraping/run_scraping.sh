#!/bin/bash
# Quick script to run the complete scraping pipeline

echo "============================================================"
echo "News Scraping Pipeline - COMP 451 Project #2"
echo "============================================================"
echo ""

# Activate virtual environment
source venv311/bin/activate

# Step 1: Collect URLs automatically
echo "Step 1: Collecting article URLs from category pages..."
python scraping/collect_urls.py

echo ""
echo "Step 2: Scraping articles from all sources..."
python scraping/scrape_all.py

echo ""
echo "============================================================"
echo "Scraping Complete!"
echo "============================================================"
echo "Check output files:"
echo "  - dataset2/raw_articles.json"
echo "  - dataset2/raw_paragraphs.json"
echo "============================================================"

