"""
Annotate Dataset2 (scraped news paragraphs) using the best model+prompt combination.
"""

import json
import os
import yaml
from tqdm import tqdm
from .comparison import get_best_model_prompt
from .predictor import predict
from .data_loader import get_few_shot_examples, load_conll2003


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def annotate_dataset2(input_path="dataset2/raw_news.json", 
                     output_path="dataset2/final_annotated.json",
                     comparison_table_path="results/comparison_table.csv"):
    """
    Annotate Dataset2 using the best model+prompt combination.
    
    Args:
        input_path (str): Path to raw news paragraphs JSON
        output_path (str): Path to save annotated dataset
        comparison_table_path (str): Path to comparison table CSV
    """
    config = load_config()
    
    # Get best model and prompt
    try:
        best_model, best_prompt_type, best_f1 = get_best_model_prompt(comparison_table_path)
        print(f"Using best model+prompt combination:")
        print(f"  Model: {best_model}")
        print(f"  Prompt Type: {best_prompt_type}")
        print(f"  F1 Score: {best_f1:.4f}\n")
    except Exception as e:
        print(f"Warning: Could not load comparison table: {e}")
        print("Using default: gpt-4o with zero_shot")
        best_model = "gpt-4o"
        best_prompt_type = "zero_shot"
    
    # Load raw news paragraphs
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. Please run the scraper first.")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_paragraphs = json.load(f)
    
    print(f"Annotating {len(raw_paragraphs)} paragraphs...")
    
    # Get few-shot examples if needed
    few_shot_examples = None
    if best_prompt_type == 'few_shot':
        # Load examples from conll2003
        num_few_shot = config.get('prompts', {}).get('few_shot_examples', 3)
        conll_data = load_conll2003(num_sentences=num_few_shot)
        few_shot_examples = get_few_shot_examples(conll_data, num_examples=num_few_shot)
    
    # Annotate each paragraph
    annotated_data = []
    
    for para_data in tqdm(raw_paragraphs, desc="Annotating"):
        text = para_data['text']
        source = para_data.get('source', 'unknown')
        
        # Tokenize (simple whitespace tokenization)
        tokens = text.split()
        
        try:
            # Get predictions
            predictions = predict(text, best_model, best_prompt_type, few_shot_examples)
            
            # Ensure predictions match token count
            if len(predictions) != len(tokens):
                # Adjust predictions
                if len(predictions) < len(tokens):
                    predictions.extend(['O'] * (len(tokens) - len(predictions)))
                else:
                    predictions = predictions[:len(tokens)]
            
            annotated_data.append({
                'text': text,
                'tokens': tokens,
                'labels': predictions,
                'source': source,
                'model': best_model,
                'prompt_type': best_prompt_type
            })
        
        except Exception as e:
            print(f"Error annotating paragraph: {e}")
            # Fallback: use all 'O' labels
            annotated_data.append({
                'text': text,
                'tokens': tokens,
                'labels': ['O'] * len(tokens),
                'source': source,
                'model': best_model,
                'prompt_type': best_prompt_type,
                'error': str(e)
            })
    
    # Save annotated dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(annotated_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnnotated dataset saved to {output_path}")
    print(f"Total paragraphs annotated: {len(annotated_data)}")
    
    return annotated_data


if __name__ == "__main__":
    # Run annotation
    annotate_dataset2()

