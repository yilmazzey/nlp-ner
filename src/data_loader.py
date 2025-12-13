"""
Data loader for conll2003 dataset from HuggingFace.
Extracts sentences and BIO labels for NER evaluation.
"""

import yaml
import os
from typing import List, Dict
from huggingface_hub import login, hf_hub_download
import datasets


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_conll2003(num_sentences=140, split='validation', use_cache=True):
    """
    Load conll2003 dataset and extract sentences with BIO labels.
    
    Args:
        num_sentences (int): Number of sentences to extract (default: 140)
        split (str): Dataset split to use (default: 'validation')
        hf_token (str, optional): HuggingFace API token
    
    Returns:
        list: List of dictionaries with 'tokens', 'labels', and 'text' keys
    """
    print(f"Loading conll2003 dataset ({split} split)...")
    
    # Check for cached dataset
    if use_cache:
        cache_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        cache_file = os.path.join(cache_dir, f'conll2003_{split}_{num_sentences}.json')
        if os.path.exists(cache_file):
            try:
                import json
                print(f"Loading from cache: {cache_file}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    sentences = json.load(f)
                print(f"Loaded {len(sentences)} sentences from cache")
                return sentences
            except Exception as e:
                print(f"Warning: Could not load from cache: {e}")
    
    # Get token from config
    try:
        config = load_config()
        hf_token = config.get('huggingface', {}).get('token')
    except:
        hf_token = None
    
    # Login to HuggingFace if token provided
    if hf_token:
        try:
            login(token=hf_token)
            print("Authenticated with HuggingFace")
        except Exception as e:
            print(f"Warning: Could not authenticate with HuggingFace: {e}")
    
    try:
        # Try using datasets library with authentication
        from datasets import load_dataset
        
        # Map split names
        split_map = {
            'validation': 'validation',
            'train': 'train',
            'test': 'test'
        }
        dataset_split = split_map.get(split, 'validation')
        
        # Load dataset - try different methods
        try:
            # Method 1: Try loading directly (may work with auth)
            dataset = load_dataset("conll2003", split=dataset_split, token=hf_token)
        except:
            # Method 2: Try loading from parquet format
            try:
                dataset = load_dataset("tner/conll2003", split=dataset_split, token=hf_token)
            except:
                # Method 3: Use nltk as fallback
                import nltk
                try:
                    nltk.download('conll2002', quiet=True)
                    from nltk.corpus import conll2002
                    # This won't work for conll2003, but shows the pattern
                    raise ImportError("Need alternative method")
                except:
                    raise RuntimeError("Could not load conll2003 dataset")
        
        # Extract sentences and labels
        sentences = []
        label_map = {0: 'O', 1: 'B-PER', 2: 'I-PER', 3: 'B-ORG', 4: 'I-ORG',
                     5: 'B-LOC', 6: 'I-LOC', 7: 'B-MISC', 8: 'I-MISC'}
        
        for example in dataset:
            tokens = example['tokens']
            ner_tags = example['ner_tags']
            
            # Convert tag IDs to BIO labels
            labels = [label_map.get(tag, 'O') for tag in ner_tags]
            
            # Create sentence text
            text = ' '.join(tokens)
            
            sentences.append({
                'tokens': tokens,
                'labels': labels,
                'text': text
            })
            
            if len(sentences) >= num_sentences:
                break
        
        print(f"Loaded {len(sentences)} sentences from conll2003 {split} split")
        return sentences
    
    except Exception as e:
        # Fallback: Download and parse manually
        print(f"Warning: Standard load failed ({e}), trying manual download...")
        import requests
        
        split_files = {
            'train': 'eng.train',
            'validation': 'eng.testa',
            'test': 'eng.testb'
        }
        
        filename = split_files.get(split, 'eng.testa')
        url = f"https://raw.githubusercontent.com/synalp/NER/master/corpus/CoNLL-2003/{filename}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse manually
            sentences = []
            current_tokens = []
            current_labels = []
            
            for line in response.text.split('\n'):
                line = line.strip()
                if not line:
                    if current_tokens:
                        sentences.append({
                            'tokens': current_tokens,
                            'labels': current_labels,
                            'text': ' '.join(current_tokens)
                        })
                        current_tokens = []
                        current_labels = []
                        if len(sentences) >= num_sentences:
                            break
                elif not line.startswith('-DOCSTART-'):
                    parts = line.split()
                    if len(parts) >= 4:
                        token = parts[0]
                        # NER tag is the 4th column (index 3)
                        ner_tag_str = parts[3]
                        # Convert string tag to label (already in BIO format)
                        current_tokens.append(token)
                        current_labels.append(ner_tag_str)
            
            if current_tokens and len(sentences) < num_sentences:
                sentences.append({
                    'tokens': current_tokens,
                    'labels': current_labels,
                    'text': ' '.join(current_tokens)
                })
            
            sentences = sentences[:num_sentences]
            print(f"Loaded {len(sentences)} sentences from conll2003 {split} split (manual download)")
            
            # Optionally save to disk for future use
            cache_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f'conll2003_{split}_{num_sentences}.json')
            
            try:
                import json
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(sentences, f, indent=2, ensure_ascii=False)
                print(f"Dataset cached to: {cache_file}")
            except Exception as cache_error:
                print(f"Warning: Could not cache dataset: {cache_error}")
            
            return sentences
            
        except Exception as e2:
            raise RuntimeError(f"Failed to load conll2003 dataset: {e2}")


def get_few_shot_examples(data, num_examples=3):
    """
    Get few-shot examples from the dataset.
    
    Args:
        data (list): List of sentence dictionaries
        num_examples (int): Number of examples to return
    
    Returns:
        list: List of example dictionaries
    """
    return data[:num_examples]


if __name__ == "__main__":
    # Test the data loader
    config = load_config()
    num_sentences = config['dataset']['num_sentences']
    
    data = load_conll2003(num_sentences=num_sentences)
    
    print(f"\nFirst sentence example:")
    print(f"Text: {data[0]['text']}")
    print(f"Tokens: {data[0]['tokens'][:10]}...")
    print(f"Labels: {data[0]['labels'][:10]}...")

