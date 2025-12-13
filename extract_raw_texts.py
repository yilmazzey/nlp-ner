#!/usr/bin/env python3
"""
Extract raw texts from the conll2003 dataset JSON file.
This creates raw_texts.json with just the text fields for LLM annotation.
"""

import json
import os


def extract_raw_texts(input_file='data/conll2003_validation_140.json', 
                      output_file='data/raw_texts.json'):
    """
    Extract raw text fields from the dataset JSON.
    
    Args:
        input_file (str): Path to input dataset JSON
        output_file (str): Path to output raw texts JSON
    """
    print(f"Loading dataset from {input_file}...")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} sentences")
    
    # Extract just the text fields
    raw_texts = [item['text'] for item in data]
    
    # Ensure we have exactly 140 samples
    if len(raw_texts) != 140:
        print(f"Warning: Expected 140 samples, got {len(raw_texts)}. Truncating/padding...")
        if len(raw_texts) > 140:
            raw_texts = raw_texts[:140]
        else:
            print(f"Error: Only {len(raw_texts)} samples available, need 140")
    
    # Save raw texts
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(raw_texts, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Extracted {len(raw_texts)} raw texts to {output_file}")
    print(f"\nSample texts:")
    for i in [0, len(raw_texts)//2, len(raw_texts)-1]:
        print(f"  [{i+1}] {raw_texts[i][:60]}...")
    
    return raw_texts


if __name__ == "__main__":
    extract_raw_texts()


