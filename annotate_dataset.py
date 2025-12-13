#!/usr/bin/env python3
"""
Annotate raw texts using all 4 LLMs and 3 prompt styles.
This script processes the raw texts and generates predictions for evaluation.
"""

import json
import os
import sys
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_loader import load_conll2003, get_few_shot_examples
from src.predictor import predict
from src.evaluator import calculate_metrics


def load_raw_texts(input_file='data/raw_texts.json'):
    """Load raw texts from JSON file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_gold_labels(input_file='data/conll2003_validation_140.json'):
    """Load gold labels from dataset JSON."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def annotate_with_llm(texts, model_name, prompt_type, few_shot_examples=None, progress=True):
    """
    Annotate texts using a specific LLM and prompt type.
    
    Args:
        texts (list): List of raw text strings
        model_name (str): Model name
        prompt_type (str): Prompt type ('zero_shot', 'few_shot', 'chain_of_thought')
        few_shot_examples (list, optional): Examples for few-shot prompting
        progress (bool): Show progress bar
    
    Returns:
        list: List of predicted label lists
    """
    predictions = []
    iterator = tqdm(texts, desc=f"{model_name} - {prompt_type}") if progress else texts
    
    for text in iterator:
        try:
            pred = predict(text, model_name, prompt_type, few_shot_examples)
            predictions.append(pred)
        except Exception as e:
            print(f"\nError predicting with {model_name} - {prompt_type}: {e}")
            # Fallback: use all 'O' labels
            tokens = text.split()
            predictions.append(['O'] * len(tokens))
    
    return predictions


def run_annotation_pipeline():
    """
    Run the full annotation pipeline for all combinations.
    """
    print("=" * 60)
    print("NER Annotation Pipeline")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading data...")
    raw_texts = load_raw_texts('data/raw_texts.json')
    gold_data = load_gold_labels('data/conll2003_validation_140.json')
    
    print(f"   ✓ Loaded {len(raw_texts)} raw texts")
    print(f"   ✓ Loaded {len(gold_data)} gold label examples")
    
    # Prepare gold labels and tokens
    gold_labels = [item['labels'] for item in gold_data]
    gold_tokens = [item['tokens'] for item in gold_data]
    
    # Get few-shot examples
    print("\n2. Preparing few-shot examples...")
    few_shot_examples = get_few_shot_examples(gold_data, num_examples=3)
    print(f"   ✓ Prepared {len(few_shot_examples)} few-shot examples")
    
    # Define all combinations (4 LLMs as specified)
    # Load from config to ensure consistency
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    models = []
    # Add one OpenAI model (prefer gpt-4o, fallback to gpt-4o-mini)
    openai_models = config.get('openai', {}).get('models', ['gpt-4o', 'gpt-4o-mini'])
    models.append(openai_models[0])  # Use first OpenAI model
    
    # Add Gemini model
    gemini_models = config.get('google_ai', {}).get('models', ['gemini-1.5-flash'])
    models.extend(gemini_models)
    
    # Add Ollama models (both)
    ollama_models = config.get('ollama', {}).get('models', ['llama3.1:8b-instruct', 'mistral:7b-instruct-v0.3'])
    models.extend(ollama_models)
    
    # Ensure we have exactly 4 models
    if len(models) > 4:
        print(f"Warning: {len(models)} models found, using first 4")
        models = models[:4]
    elif len(models) < 4:
        print(f"Warning: Only {len(models)} models found, need 4")
    
    print(f"   Using {len(models)} models: {models}")
    
    prompt_types = ['zero_shot', 'few_shot', 'chain_of_thought']
    
    # Results storage
    all_results = {}
    
    print("\n3. Running annotation for all combinations...")
    print(f"   Total combinations: {len(models)} models × {len(prompt_types)} prompts = {len(models) * len(prompt_types)}")
    
    for model_name in models:
        for prompt_type in prompt_types:
            combo_key = f"{model_name}_{prompt_type}"
            print(f"\n   Processing: {combo_key}")
            
            try:
                # Get few-shot examples if needed
                examples = few_shot_examples if prompt_type == 'few_shot' else None
                
                # Annotate
                predictions = annotate_with_llm(
                    raw_texts, 
                    model_name, 
                    prompt_type, 
                    examples,
                    progress=True
                )
                
                # Calculate metrics
                metrics = calculate_metrics(
                    gold_labels, 
                    predictions, 
                    gold_tokens
                )
                
                # Store results
                all_results[combo_key] = {
                    'model': model_name,
                    'prompt_type': prompt_type,
                    'predictions': predictions,
                    'metrics': metrics
                }
                
                print(f"   ✓ F1 Overall: {metrics['F1_Overall']:.4f}")
                print(f"     F1_PER: {metrics['F1_PER']:.4f}, F1_ORG: {metrics['F1_ORG']:.4f}")
                print(f"     F1_LOC: {metrics['F1_LOC']:.4f}, F1_MISC: {metrics['F1_MISC']:.4f}")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
                # Store error result
                all_results[combo_key] = {
                    'model': model_name,
                    'prompt_type': prompt_type,
                    'error': str(e),
                    'metrics': {
                        'F1_Overall': 0.0,
                        'F1_PER': 0.0,
                        'F1_ORG': 0.0,
                        'F1_LOC': 0.0,
                        'F1_MISC': 0.0
                    }
                }
    
    # Save results
    print("\n4. Saving results...")
    results_dir = 'results'
    os.makedirs(results_dir, exist_ok=True)
    
    # Save full predictions
    predictions_file = os.path.join(results_dir, 'all_predictions.json')
    predictions_data = {
        combo: {
            'model': info['model'],
            'prompt_type': info['prompt_type'],
            'predictions': info.get('predictions', [])
        }
        for combo, info in all_results.items()
    }
    with open(predictions_file, 'w', encoding='utf-8') as f:
        json.dump(predictions_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Saved predictions to {predictions_file}")
    
    # Save metrics summary
    import pandas as pd
    metrics_data = []
    for combo, info in all_results.items():
        metrics = info.get('metrics', {})
        metrics_data.append({
            'Model': info['model'],
            'Prompt_Type': info['prompt_type'],
            'F1_PER': metrics.get('F1_PER', 0.0),
            'F1_ORG': metrics.get('F1_ORG', 0.0),
            'F1_LOC': metrics.get('F1_LOC', 0.0),
            'F1_MISC': metrics.get('F1_MISC', 0.0),
            'F1_Overall': metrics.get('F1_Overall', 0.0)
        })
    
    df = pd.DataFrame(metrics_data)
    comparison_file = os.path.join(results_dir, 'comparison_table.csv')
    df.to_csv(comparison_file, index=False)
    print(f"   ✓ Saved comparison table to {comparison_file}")
    
    # Find best combination
    best_idx = df['F1_Overall'].idxmax()
    best_row = df.loc[best_idx]
    print(f"\n5. Best combination:")
    print(f"   Model: {best_row['Model']}")
    print(f"   Prompt Type: {best_row['Prompt_Type']}")
    print(f"   F1 Overall: {best_row['F1_Overall']:.4f}")
    
    print("\n" + "=" * 60)
    print("Annotation pipeline complete!")
    print("=" * 60)
    
    return all_results, df


if __name__ == "__main__":
    try:
        results, comparison_df = run_annotation_pipeline()
        print(f"\nComparison Table Preview:")
        print(comparison_df.to_string(index=False))
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

