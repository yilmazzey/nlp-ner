"""
Main prediction function for NER using different LLMs and prompt styles.
"""

import re
from typing import List, Optional
from .prompts import get_prompt
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient
from .data_loader import get_few_shot_examples


def predict(sentence: str, model_name: str, prompt_type: str, examples: Optional[List] = None):
    """
    Predict NER labels for a given sentence using a trained model.
    
    Parameters:
        sentence (str): Input sentence.
        model_name (str): Model name (e.g., 'gpt-4o', 'gemini-1.5-flash', 'llama3.1:8b-instruct', 'mistral:7b-instruct-v0.3').
        prompt_type (str): Prompt type ('zero_shot', 'few_shot', 'chain_of_thought').
        examples (list, optional): Examples for few-shot prompting.
    
    Returns:
        predictions (list): Predicted NER labels for the sentence.
    """
    # Tokenize sentence (simple whitespace tokenization)
    tokens = sentence.split()
    
    # Get appropriate prompt
    if prompt_type == 'few_shot' and examples is None:
        raise ValueError("Examples are required for few-shot prompting")
    
    prompt = get_prompt(sentence, prompt_type, examples)
    
    # Select appropriate client based on model name
    response = None
    
    # OpenAI models
    if model_name in ['gpt-4o', 'gpt-4o-mini']:
        try:
            client = OpenAIClient()
            response = client.generate(prompt, model_name=model_name)
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            raise
    
    # Gemini models
    elif 'gemini' in model_name.lower():
        try:
            client = GeminiClient()
            response = client.generate(prompt, model_name=model_name)
        except Exception as e:
            print(f"Error with Gemini API: {e}")
            raise
    
    # Ollama models
    elif model_name in ['llama3.1:8b-instruct', 'mistral:7b-instruct-v0.3']:
        try:
            client = OllamaClient()
            response = client.generate(prompt, model_name=model_name)
        except Exception as e:
            print(f"Error with Ollama: {e}")
            raise
    
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    if response is None:
        raise ValueError("No response received from model")
    
    # Parse response to extract labels
    predictions = parse_labels_from_response(response, tokens)
    
    return predictions


def parse_labels_from_response(response: str, tokens: List[str]) -> List[str]:
    """
    Parse BIO labels from LLM response.
    
    Args:
        response (str): Raw response from LLM
        tokens (list): List of tokens in the sentence
    
    Returns:
        list: List of predicted labels
    """
    # Try to extract labels from response
    # Look for patterns like "B-PER I-PER O B-LOC" or labels on separate lines
    
    # Remove any reasoning text before "Labels:" if present
    if "Labels:" in response:
        response = response.split("Labels:")[-1].strip()
    
    # Try to find a line that looks like labels
    lines = response.split('\n')
    label_line = None
    
    for line in lines:
        line = line.strip()
        # Check if line contains BIO labels
        if re.search(r'\b(B|I)-(PER|ORG|LOC|MISC)\b', line) or 'O' in line:
            label_line = line
            break
    
    if label_line is None:
        # Try to extract from the entire response
        label_line = response.strip()
    
    # Extract labels (e.g., B-PERSON, I-LOCATION, O, etc.)
    # Match BIO labels for project classes or O
    label_pattern = r'\b(B|I)-(PERSON|ORGANIZATION|LOCATION|TIME|CURRENCY)\b|\bO\b'
    found_labels = re.findall(label_pattern, label_line)
    
    # Convert tuples to label strings
    labels = []
    for match in found_labels:
        if isinstance(match, tuple):
            if match[0] and match[1]:
                labels.append(f"{match[0]}-{match[1]}")
            else:
                labels.append("O")
        else:
            labels.append("O")
    
    # If we didn't find enough labels, pad with 'O'
    while len(labels) < len(tokens):
        labels.append('O')
    
    # If we found too many labels, truncate
    labels = labels[:len(tokens)]
    
    return labels


def predict_batch(sentences: List[str], model_name: str, prompt_type: str, 
                  few_shot_examples: Optional[List] = None, progress_callback=None):
    """
    Predict labels for multiple sentences.
    
    Args:
        sentences (list): List of sentences
        model_name (str): Model name
        prompt_type (str): Prompt type
        few_shot_examples (list, optional): Examples for few-shot prompting
        progress_callback (callable, optional): Callback function for progress updates
    
    Returns:
        list: List of predicted label lists
    """
    predictions = []
    
    for i, sentence in enumerate(sentences):
        try:
            pred = predict(sentence, model_name, prompt_type, few_shot_examples)
            predictions.append(pred)
            
            if progress_callback:
                progress_callback(i + 1, len(sentences))
        except Exception as e:
            print(f"Error predicting sentence {i+1}: {e}")
            # Fallback: return all 'O' labels
            tokens = sentence.split()
            predictions.append(['O'] * len(tokens))
    
    return predictions


if __name__ == "__main__":
    # Test the predictor
    test_sentence = "Barack Obama visited France in 2014."
    
    print("Testing predictor with different models...")
    print(f"Sentence: {test_sentence}\n")
    
    # Test with Ollama (if available)
    try:
        client = OllamaClient()
        if client.is_available():
            print("Testing with Ollama...")
            pred = predict(test_sentence, "llama3.1:8b-instruct", "zero_shot")
            print(f"Predictions: {pred}")
    except Exception as e:
        print(f"Ollama test failed: {e}")

