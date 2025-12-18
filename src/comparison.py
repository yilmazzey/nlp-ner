"""
Run comparison across all 12 combinations (4 LLMs × 3 prompt styles)
and generate comparison_table.csv with F1 scores.
"""

import os

import pandas as pd
import yaml
from tqdm import tqdm

from .data_loader import load_project_dataset, get_few_shot_examples
from .predictor import predict
from .evaluator import calculate_metrics


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_comparison(data=None, output_path="results/comparison_table.csv"):
    """
    Run all 12 combinations and generate comparison table.

    Args:
        data (list, optional): List of sentence dictionaries. If None, loads project dataset (OntoNotes5 subset).
        output_path (str): Path to save comparison table CSV

    Returns:
        pd.DataFrame: Comparison table with F1 scores
    """
    config = load_config()
    
    # Load data if not provided
    if data is None:
        num_sentences = config['dataset']['num_sentences']
        data = load_project_dataset(num_examples=num_sentences)
    
    # Define all combinations
    models = []
    
    # OpenAI models
    openai_models = config.get('openai', {}).get('models', [])
    models.extend(openai_models)
    
    # Gemini models
    gemini_models = config.get('google_ai', {}).get('models', [])
    models.extend(gemini_models)
    
    # Ollama models
    ollama_models = config.get('ollama', {}).get('models', [])
    models.extend(ollama_models)
    
    prompt_types = ['zero_shot', 'few_shot', 'chain_of_thought']
    
    # Get few-shot examples
    num_few_shot = config.get('prompts', {}).get('few_shot_examples', 3)
    few_shot_examples = get_few_shot_examples(data, num_examples=num_few_shot)
    
    # Results storage
    results = []
    
    print(f"Running comparison across {len(models)} models × {len(prompt_types)} prompt types = {len(models) * len(prompt_types)} combinations")
    print(f"Evaluating on {len(data)} sentences\n")
    
    # Run each combination
    total_combinations = len(models) * len(prompt_types)
    current_combination = 0
    
    for model_name in models:
        for prompt_type in prompt_types:
            current_combination += 1
            print(f"\n[{current_combination}/{total_combinations}] Testing {model_name} with {prompt_type}...")
            
            try:
                # Get predictions for all sentences
                predictions = []
                sentences = []
                tokens_list = []
                true_labels = []
                
                for sentence_data in tqdm(data, desc=f"{model_name} - {prompt_type}"):
                    sentence = sentence_data['text']
                    tokens = sentence_data['tokens']
                    true_labs = sentence_data['labels']
                    
                    # Get few-shot examples if needed
                    examples = few_shot_examples if prompt_type == 'few_shot' else None
                    
                    try:
                        pred = predict(sentence, model_name, prompt_type, examples)
                        predictions.append(pred)
                        sentences.append(sentence)
                        tokens_list.append(tokens)
                        true_labels.append(true_labs)
                    except Exception as e:
                        print(f"  Error predicting: {e}")
                        # Fallback: use all 'O' labels
                        predictions.append(['O'] * len(tokens))
                        sentences.append(sentence)
                        tokens_list.append(tokens)
                        true_labels.append(true_labs)
                
                # Calculate metrics (5-class schema)
                metrics = calculate_metrics(true_labels, predictions, tokens_list)

                # Store results
                result = {
                    'Model': model_name,
                    'Prompt_Type': prompt_type,
                    'F1_PERSON': metrics.get('F1_PERSON', 0.0),
                    'F1_ORGANIZATION': metrics.get('F1_ORGANIZATION', 0.0),
                    'F1_LOCATION': metrics.get('F1_LOCATION', 0.0),
                    'F1_TIME': metrics.get('F1_TIME', 0.0),
                    'F1_CURRENCY': metrics.get('F1_CURRENCY', 0.0),
                    'F1_Overall': metrics['F1_Overall'],
                }
                results.append(result)
                
                print(f"  F1_Overall: {metrics['F1_Overall']:.4f}")
                print(
                    f"  F1_PERSON: {metrics.get('F1_PERSON', 0.0):.4f}, "
                    f"F1_ORGANIZATION: {metrics.get('F1_ORGANIZATION', 0.0):.4f}, "
                    f"F1_LOCATION: {metrics.get('F1_LOCATION', 0.0):.4f}, "
                    f"F1_TIME: {metrics.get('F1_TIME', 0.0):.4f}, "
                    f"F1_CURRENCY: {metrics.get('F1_CURRENCY', 0.0):.4f}"
                )
            
            except Exception as e:
                print(f"  Error with {model_name} - {prompt_type}: {e}")
                # Store error result
                result = {
                    'Model': model_name,
                    'Prompt_Type': prompt_type,
                    'F1_PERSON': 0.0,
                    'F1_ORGANIZATION': 0.0,
                    'F1_LOCATION': 0.0,
                    'F1_TIME': 0.0,
                    'F1_CURRENCY': 0.0,
                    'F1_Overall': 0.0,
                }
                results.append(result)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"\nComparison table saved to {output_path}")
    
    # Find best combination
    best_idx = df['F1_Overall'].idxmax()
    best_row = df.loc[best_idx]
    print(f"\nBest combination:")
    print(f"  Model: {best_row['Model']}")
    print(f"  Prompt Type: {best_row['Prompt_Type']}")
    print(f"  F1_Overall: {best_row['F1_Overall']:.4f}")
    
    return df, best_row


def get_best_model_prompt(comparison_table_path="results/comparison_table.csv"):
    """
    Get the best model and prompt combination from comparison table.
    
    Args:
        comparison_table_path (str): Path to comparison table CSV
    
    Returns:
        tuple: (model_name, prompt_type, f1_score)
    """
    df = pd.read_csv(comparison_table_path)
    best_idx = df['F1_Overall'].idxmax()
    best_row = df.loc[best_idx]
    
    return best_row['Model'], best_row['Prompt_Type'], best_row['F1_Overall']


if __name__ == "__main__":
    # Run comparison
    df, best = run_comparison()
    print("\nComparison Table:")
    print(df.to_string(index=False))

