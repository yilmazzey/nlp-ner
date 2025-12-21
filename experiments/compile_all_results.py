#!/usr/bin/env python3
"""
Compile results from all models and create comparison plots.
Finds the most recent results for each model and prompt type,
then creates separate plots for each metric (F1, Precision, Recall, Accuracy).
Includes both token-level and spaCy entity-level metrics.
"""

import json
import glob
import os
from collections import defaultdict
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Try to import spaCy for entity-level metrics
try:
    import spacy
    from spacy.scorer import Scorer
    from spacy.training.example import Example
    from typing import List, Dict
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("⚠️ spaCy model not found, using blank('en')")
        nlp = spacy.blank("en")
    
    SPACY_AVAILABLE = True
except ImportError:
    print("⚠️ spaCy not available. Entity-level metrics will be skipped.")
    SPACY_AVAILABLE = False
    nlp = None

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

def parse_timestamp(timestamp_str):
    """Parse timestamp string YYYYMMDD_HHMMSS to datetime object"""
    try:
        return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    except:
        return datetime.min

def find_latest_results(results_dir="results"):
    """
    Find the most recent result file for each (model, prompt_type) combination.
    Returns: dict[model][prompt_type] = (filepath, data)
    """
    result_files = glob.glob(os.path.join(results_dir, "*_results_*.json"))
    
    # Structure: model -> prompt_type -> (timestamp, filepath, data)
    model_results = defaultdict(lambda: defaultdict(lambda: (datetime.min, None, None)))
    
    for filepath in result_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            metadata = data.get('metadata', {})
            model = metadata.get('model', 'unknown')
            prompt_type = metadata.get('prompt_type', 'unknown')
            timestamp_str = metadata.get('timestamp', '')
            
            timestamp = parse_timestamp(timestamp_str)
            
            # Keep only the most recent for each (model, prompt_type)
            current_timestamp, _, _ = model_results[model][prompt_type]
            if timestamp > current_timestamp:
                model_results[model][prompt_type] = (timestamp, filepath, data)
                
        except Exception as e:
            print(f"⚠️ Error reading {filepath}: {e}")
            continue
    
    return model_results

def labels_to_spacy_doc(text: str, tokens: List[str], labels: List[str], nlp) -> 'spacy.tokens.Doc':
    """Convert token labels to spacy Doc with entities"""
    # Create Doc from text
    doc = nlp(text)
    
    # Find character spans for entities from labels
    entities = []
    current_entity = None
    current_start = None
    current_end = None
    
    # Map tokens to character positions in text
    char_positions = []
    pos = 0
    text_lower = text.lower()
    
    for token in tokens:
        token_lower = token.lower()
        token_start = text_lower.find(token_lower, pos)
        if token_start != -1:
            char_positions.append((token_start, token_start + len(token)))
            pos = token_start + len(token)
        else:
            # Approximate position
            char_positions.append((pos, pos + len(token)))
            pos += len(token) + 1
    
    # Extract entity spans
    for i, (label, (start, end)) in enumerate(zip(labels, char_positions)):
        if label != 'O':
            if current_entity is None or current_entity != label:
                # End previous entity if any
                if current_entity is not None:
                    entities.append((current_start, current_end, current_entity))
                # Start new entity
                current_entity = label
                current_start = start
                current_end = end
            else:
                # Extend current entity
                current_end = end
        else:
            # End current entity if any
            if current_entity is not None:
                entities.append((current_start, current_end, current_entity))
                current_entity = None
    
    # Add last entity if exists
    if current_entity is not None:
        entities.append((current_start, current_end, current_entity))
    
    # Set entities on doc
    doc.set_ents([doc.char_span(start, end, label=ent_type) 
                  for start, end, ent_type in entities 
                  if doc.char_span(start, end, label=ent_type) is not None])
    
    return doc

def calculate_spacy_entity_metrics(true_docs: List, pred_docs: List) -> Dict:
    """Calculate entity-level metrics using spaCy Scorer"""
    if not SPACY_AVAILABLE:
        return {}
    
    scorer = Scorer(nlp)
    
    # Create Example objects for scorer
    examples = []
    for true_doc, pred_doc in zip(true_docs, pred_docs):
        example = Example(predicted=pred_doc, reference=true_doc)
        examples.append(example)
    
    # Calculate scores
    scores = scorer.score(examples)
    
    # Extract entity-level metrics
    ents_p = scores.get('ents_p', 0.0)
    ents_r = scores.get('ents_r', 0.0)
    ents_f = scores.get('ents_f', 0.0)
    
    metrics = {
        'F1': ents_f,
        'Precision': ents_p,
        'Recall': ents_r
    }
    
    return metrics

def extract_metrics(data):
    """Extract overall metrics from result data (token-level)"""
    metrics = data.get('metrics', {})
    return {
        'F1': metrics.get('F1_Overall', 0.0),
        'Precision': metrics.get('Precision_Overall', 0.0),
        'Recall': metrics.get('Recall_Overall', 0.0),
        'Accuracy': metrics.get('Accuracy', 0.0)
    }

def calculate_spacy_metrics_from_data(data):
    """Calculate spaCy entity-level metrics from saved predictions"""
    if not SPACY_AVAILABLE:
        return {}
    
    predictions = data.get('predictions', [])
    if not predictions:
        return {}
    
    true_docs = []
    pred_docs = []
    
    for pred_data in predictions:
        text = pred_data.get('sentence', '')
        tokens = pred_data.get('tokens', [])
        true_labels = pred_data.get('true_labels', [])
        pred_labels = pred_data.get('predicted_labels', [])
        
        if text and tokens and len(true_labels) == len(tokens) and len(pred_labels) == len(tokens):
            true_doc = labels_to_spacy_doc(text, tokens, true_labels, nlp)
            pred_doc = labels_to_spacy_doc(text, tokens, pred_labels, nlp)
            true_docs.append(true_doc)
            pred_docs.append(pred_doc)
    
    if not true_docs:
        return {}
    
    return calculate_spacy_entity_metrics(true_docs, pred_docs)

def create_comparison_plots(model_results, output_dir="results"):
    """Create separate plots for each metric"""
    
    # Collect all data (token-level and spaCy entity-level)
    plot_data_token = []
    plot_data_spacy = []
    
    print("\nCalculating spaCy entity-level metrics...")
    for model, prompt_results in model_results.items():
        for prompt_type, (timestamp, filepath, data) in prompt_results.items():
            if data is None:
                continue
            
            # Token-level metrics
            metrics = extract_metrics(data)
            plot_data_token.append({
                'Model': model,
                'Prompt Type': prompt_type.replace('_', '-').title(),
                'F1': metrics['F1'],
                'Precision': metrics['Precision'],
                'Recall': metrics['Recall'],
                'Accuracy': metrics['Accuracy'],
                'Timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # spaCy entity-level metrics
            if SPACY_AVAILABLE:
                spacy_metrics = calculate_spacy_metrics_from_data(data)
                if spacy_metrics:
                    plot_data_spacy.append({
                        'Model': model,
                        'Prompt Type': prompt_type.replace('_', '-').title(),
                        'F1': spacy_metrics.get('F1', 0.0),
                        'Precision': spacy_metrics.get('Precision', 0.0),
                        'Recall': spacy_metrics.get('Recall', 0.0),
                        'Timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    })
    
    # Use token-level data as default
    plot_data = plot_data_token
    df = pd.DataFrame(plot_data)
    
    # Create separate DataFrame for spaCy metrics
    df_spacy = None
    if plot_data_spacy:
        df_spacy = pd.DataFrame(plot_data_spacy)
    
    if not plot_data:
        print("❌ No data found to plot!")
        return
    
    df = pd.DataFrame(plot_data)
    
    # Print summary
    print("\n" + "=" * 80)
    print("Results Summary")
    print("=" * 80)
    print(df.to_string(index=False))
    print("=" * 80)
    
    # Standardize prompt type names
    prompt_mapping = {
        'zero-shot': 'Zero-Shot',
        'few-shot': 'Few-Shot',
        'chain-of-thought': 'Chain-of-Thought',
        'Zero-Shot': 'Zero-Shot',
        'Few-Shot': 'Few-Shot',
        'Chain-Of-Thought': 'Chain-of-Thought'
    }
    df['Prompt Type'] = df['Prompt Type'].map(lambda x: prompt_mapping.get(x.lower(), x))
    
    # Define metrics and their display names
    metrics_to_plot = {
        'F1': 'F1 Score',
        'Precision': 'Precision',
        'Recall': 'Recall',
        'Accuracy': 'Accuracy'
    }
    
    # For spaCy, we don't have Accuracy (entity-level only)
    metrics_to_plot_spacy = {
        'F1': 'F1 Score',
        'Precision': 'Precision',
        'Recall': 'Recall'
    }
    
    # Sort models for consistent ordering
    models_order = sorted(df['Model'].unique())
    prompt_order = ['Zero-Shot', 'Few-Shot', 'Chain-of-Thought']
    
    # Create token-level plots
    for metric, metric_name in metrics_to_plot.items():
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # Group by Model, with bars for each prompt type
        bar_width = 0.25
        x = list(range(len(models_order)))
        colors = ['#2E86AB', '#A23B72', '#F18F01']  # Distinct colors for prompt types
        
        # Create bars for each prompt type
        for i, prompt in enumerate(prompt_order):
            values = []
            positions = []
            
            for model in models_order:
                row = df[(df['Model'] == model) & (df['Prompt Type'] == prompt)]
                if len(row) > 0:
                    values.append(row[metric].iloc[0])
                else:
                    values.append(0)
                positions.append(x[models_order.index(model)] + i * bar_width)
            
            ax.bar(positions, values, bar_width, label=prompt, color=colors[i], alpha=0.85, edgecolor='white', linewidth=1.5)
            
            # Add value labels on bars
            for j, (pos, val) in enumerate(zip(positions, values)):
                if val > 0:
                    ax.text(pos, val + 0.01, f'{val:.3f}', 
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Customize plot
        ax.set_xlabel('Model', fontsize=13, fontweight='bold')
        ax.set_ylabel(metric_name, fontsize=13, fontweight='bold')
        ax.set_title(f'NER {metric_name} Comparison: All Models × Prompt Types', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks([x[i] + bar_width for i in range(len(models_order))])
        ax.set_xticklabels([m.replace(':', ':\n') for m in models_order], fontsize=11, ha='center')
        ax.legend(title='Prompt Type', fontsize=11, title_fontsize=12, loc='upper left')
        ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
        ax.set_ylim(0, 1.05)
        
        plt.tight_layout()
        
        # Save plot
        output_file = os.path.join(output_dir, f'all_models_{metric.lower()}_comparison.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()
    
    # Create spaCy entity-level plots if available
    if df_spacy is not None and len(df_spacy) > 0:
        metrics_to_plot_spacy = {
            'F1': 'F1 Score',
            'Precision': 'Precision',
            'Recall': 'Recall'
        }
        # Standardize prompt type names for spaCy data
        df_spacy = pd.DataFrame(plot_data_spacy)
        prompt_mapping = {
            'zero-shot': 'Zero-Shot',
            'few-shot': 'Few-Shot',
            'chain-of-thought': 'Chain-of-Thought',
            'Zero-Shot': 'Zero-Shot',
            'Few-Shot': 'Few-Shot',
            'Chain-Of-Thought': 'Chain-of-Thought'
        }
        df_spacy['Prompt Type'] = df_spacy['Prompt Type'].map(lambda x: prompt_mapping.get(x.lower(), x))
        
        models_order_spacy = sorted(df_spacy['Model'].unique())
        prompt_order_spacy = ['Zero-Shot', 'Few-Shot', 'Chain-of-Thought']
        
        for metric, metric_name in metrics_to_plot_spacy.items():
            fig, ax = plt.subplots(figsize=(16, 8))
            
            # Group by Model, with bars for each prompt type
            bar_width = 0.25
            x = list(range(len(models_order_spacy)))
            colors = ['#2E86AB', '#A23B72', '#F18F01']  # Distinct colors for prompt types
            
            # Create bars for each prompt type
            for i, prompt in enumerate(prompt_order_spacy):
                values = []
                positions = []
                
                for model in models_order_spacy:
                    row = df_spacy[(df_spacy['Model'] == model) & (df_spacy['Prompt Type'] == prompt)]
                    if len(row) > 0:
                        values.append(row[metric].iloc[0])
                    else:
                        values.append(0)
                    positions.append(x[models_order_spacy.index(model)] + i * bar_width)
                
                ax.bar(positions, values, bar_width, label=prompt, color=colors[i], alpha=0.85, edgecolor='white', linewidth=1.5)
                
                # Add value labels on bars
                for j, (pos, val) in enumerate(zip(positions, values)):
                    if val > 0:
                        ax.text(pos, val + 0.01, f'{val:.3f}', 
                               ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            # Customize plot
            ax.set_xlabel('Model', fontsize=13, fontweight='bold')
            ax.set_ylabel(f'{metric_name} (Entity-Level)', fontsize=13, fontweight='bold')
            ax.set_title(f'NER {metric_name} Comparison (spaCy Entity-Level): All Models × Prompt Types', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_xticks([x[i] + bar_width for i in range(len(models_order_spacy))])
            ax.set_xticklabels([m.replace(':', ':\n') for m in models_order_spacy], fontsize=11, ha='center')
            ax.legend(title='Prompt Type', fontsize=11, title_fontsize=12, loc='upper left')
            ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
            ax.set_ylim(0, 1.05)
            
            plt.tight_layout()
            
            # Save plot
            output_file = os.path.join(output_dir, f'all_models_{metric.lower()}_spacy_comparison.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"✅ Saved (spaCy entity-level): {output_file}")
            plt.close()
        
        # Save spaCy summary CSV
        spacy_summary_file = os.path.join(output_dir, 'all_models_spacy_comparison_summary.csv')
        df_spacy.to_csv(spacy_summary_file, index=False)
        print(f"✅ Saved spaCy summary CSV: {spacy_summary_file}")
    
    # Also create a combined summary CSV (token-level)
    summary_file = os.path.join(output_dir, 'all_models_comparison_summary.csv')
    df.to_csv(summary_file, index=False)
    print(f"✅ Saved token-level summary CSV: {summary_file}")
    
    return df, df_spacy

def main():
    results_dir = "results"
    
    print("=" * 80)
    print("Compiling Results from All Models")
    print("=" * 80)
    
    # Find latest results for each model
    model_results = find_latest_results(results_dir)
    
    # Print what we found
    print("\nFound results for:")
    for model in sorted(model_results.keys()):
        print(f"\n  {model}:")
        for prompt_type, (timestamp, filepath, _) in sorted(model_results[model].items()):
            print(f"    - {prompt_type}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({os.path.basename(filepath)})")
    
    # Create plots
    print("\n" + "=" * 80)
    print("Creating Comparison Plots")
    print("=" * 80)
    
    df, df_spacy = create_comparison_plots(model_results, results_dir)
    
    print("\n" + "=" * 80)
    print("✅ All done!")
    print("=" * 80)

if __name__ == "__main__":
    main()

