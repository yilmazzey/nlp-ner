"""
Main script to run the complete NER prompt engineering pipeline.
"""

import argparse
import sys
import os

# Add project root to path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from src.comparison import run_comparison
from src.annotator import annotate_dataset2
from scraping.news_scraper import main as scrape_news


def main():
    parser = argparse.ArgumentParser(description='NER Prompt Engineering Pipeline')
    parser.add_argument('--step', choices=['scrape', 'compare', 'annotate', 'all'], 
                       default='all', help='Which step to run')
    parser.add_argument('--skip-scrape', action='store_true', 
                       help='Skip scraping step (use existing raw_news.json)')
    
    args = parser.parse_args()
    
    if args.step == 'scrape' or (args.step == 'all' and not args.skip_scrape):
        print("=" * 60)
        print("Step 1: Web Scraping")
        print("=" * 60)
        scrape_news()
        print()
    
    if args.step == 'compare' or args.step == 'all':
        print("=" * 60)
        print("Step 2: Running Comparison (12 combinations)")
        print("=" * 60)
        df, best = run_comparison()
        print()
    
    if args.step == 'annotate' or args.step == 'all':
        print("=" * 60)
        print("Step 3: Annotating Dataset2")
        print("=" * 60)
        annotate_dataset2()
        print()
    
    print("=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print("\nOutput files:")
    print("  - results/comparison_table.csv")
    print("  - dataset2/final_annotated.json")


if __name__ == "__main__":
    main()

