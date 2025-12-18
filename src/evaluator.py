"""
Evaluation metrics for NER: F1-score per entity type and overall.
"""

from typing import List, Dict, Tuple
import numpy as np


def extract_entities(tokens: List[str], labels: List[str]) -> List[Tuple[str, int, int, str]]:
    """
    Extract entities from tokens and labels.
    
    Args:
        tokens (list): List of tokens
        labels (list): List of BIO labels
    
    Returns:
        list: List of (entity_type, start_idx, end_idx, text) tuples
    """
    entities = []
    current_entity = None
    
    for i, (token, label) in enumerate(zip(tokens, labels)):
        if label.startswith('B-'):
            # Start of new entity
            if current_entity is not None:
                entities.append(current_entity)
            entity_type = label[2:]  # Remove 'B-' prefix
            current_entity = (entity_type, i, i, token)
        elif label.startswith('I-'):
            # Continuation of entity
            if current_entity is not None:
                entity_type, start_idx, _, text = current_entity
                if entity_type == label[2:]:  # Same entity type
                    current_entity = (entity_type, start_idx, i, text + ' ' + token)
                else:
                    # Different entity type - end previous, start new
                    entities.append(current_entity)
                    entity_type = label[2:]
                    current_entity = (entity_type, i, i, token)
            else:
                # I- without B- - treat as B-
                entity_type = label[2:]
                current_entity = (entity_type, i, i, token)
        else:
            # O label - end current entity if any
            if current_entity is not None:
                entities.append(current_entity)
                current_entity = None
    
    # Add last entity if exists
    if current_entity is not None:
        entities.append(current_entity)
    
    return entities


def calculate_metrics(true_labels: List[List[str]], pred_labels: List[List[str]],
                      tokens_list: List[List[str]], entity_types: List[str] = None) -> Dict:
    """
    Calculate precision, recall, and F1-score per entity type and overall.

    Args:
        true_labels (list): List of true label lists
        pred_labels (list): List of predicted label lists
        tokens_list (list): List of token lists
        entity_types (list, optional): List of entity types to evaluate.
            Defaults to ['PERSON', 'LOCATION', 'ORGANIZATION', 'TIME', 'CURRENCY'].

    Returns:
        dict: Dictionary with metrics per entity type and overall
    """
    if entity_types is None:
        entity_types = ['PERSON', 'LOCATION', 'ORGANIZATION', 'TIME', 'CURRENCY']
    
    # Extract entities for each sentence
    true_entities_all = []
    pred_entities_all = []
    
    for tokens, true_labs, pred_labs in zip(tokens_list, true_labels, pred_labels):
        true_entities = extract_entities(tokens, true_labs)
        pred_entities = extract_entities(tokens, pred_labs)
        true_entities_all.append(true_entities)
        pred_entities_all.append(pred_entities)
    
    # Calculate metrics per entity type
    metrics = {}
    
    for entity_type in entity_types:
        true_entities_type = []
        pred_entities_type = []
        
        for true_ents, pred_ents in zip(true_entities_all, pred_entities_all):
            true_entities_type.extend([e for e in true_ents if e[0] == entity_type])
            pred_entities_type.extend([e for e in pred_ents if e[0] == entity_type])
        
        # Convert to sets for comparison (using (start, end, text) as key)
        true_set = set((e[1], e[2], e[3]) for e in true_entities_type)
        pred_set = set((e[1], e[2], e[3]) for e in pred_entities_type)
        
        # Calculate TP, FP, FN
        tp = len(true_set & pred_set)
        fp = len(pred_set - true_set)
        fn = len(true_set - pred_set)
        
        # Calculate precision, recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics[f'F1_{entity_type}'] = f1
        metrics[f'Precision_{entity_type}'] = precision
        metrics[f'Recall_{entity_type}'] = recall
        metrics[f'TP_{entity_type}'] = tp
        metrics[f'FP_{entity_type}'] = fp
        metrics[f'FN_{entity_type}'] = fn
    
    # Calculate overall metrics (micro-averaged)
    all_true_entities = []
    all_pred_entities = []
    
    for true_ents, pred_ents in zip(true_entities_all, pred_entities_all):
        all_true_entities.extend(true_ents)
        all_pred_entities.extend(pred_ents)
    
    # Convert to sets
    true_set_all = set((e[1], e[2], e[3]) for e in all_true_entities)
    pred_set_all = set((e[1], e[2], e[3]) for e in all_pred_entities)
    
    tp_all = len(true_set_all & pred_set_all)
    fp_all = len(pred_set_all - true_set_all)
    fn_all = len(true_set_all - pred_set_all)
    
    precision_overall = tp_all / (tp_all + fp_all) if (tp_all + fp_all) > 0 else 0.0
    recall_overall = tp_all / (tp_all + fn_all) if (tp_all + fn_all) > 0 else 0.0
    f1_overall = 2 * precision_overall * recall_overall / (precision_overall + recall_overall) if (precision_overall + recall_overall) > 0 else 0.0
    
    metrics['F1_Overall'] = f1_overall
    metrics['Precision_Overall'] = precision_overall
    metrics['Recall_Overall'] = recall_overall
    metrics['TP_Overall'] = tp_all
    metrics['FP_Overall'] = fp_all
    metrics['FN_Overall'] = fn_all
    
    return metrics


def evaluate_single(sentence_data: Dict, predictions: List[str]) -> Dict:
    """
    Evaluate predictions for a single sentence.
    
    Args:
        sentence_data (dict): Dictionary with 'tokens' and 'labels' keys
        predictions (list): List of predicted labels
    
    Returns:
        dict: Metrics dictionary
    """
    return calculate_metrics(
        [sentence_data['labels']],
        [predictions],
        [sentence_data['tokens']]
    )


if __name__ == "__main__":
    # Test the evaluator
    tokens = ["Barack", "Obama", "visited", "France", "in", "2014", "."]
    true_labels = ["B-PER", "I-PER", "O", "B-LOC", "O", "O", "O"]
    pred_labels = ["B-PER", "I-PER", "O", "B-LOC", "O", "O", "O"]
    
    metrics = calculate_metrics(
        [true_labels],
        [pred_labels],
        [tokens]
    )
    
    print("Test metrics:")
    for key, value in metrics.items():
        if 'F1' in key:
            print(f"{key}: {value:.4f}")


