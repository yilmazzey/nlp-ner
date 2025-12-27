"""
Convert dataset labels from BIO format to simplified format.
Removes B-/I- prefixes, keeping only entity types (e.g., "B-TIME" -> "TIME", "I-TIME" -> "TIME").
"""

import json
import os


def remove_bio_tags(label):
    """
    Remove BIO tag prefixes from labels.
    
    Args:
        label (str): Label with BIO tag (e.g., "B-TIME", "I-PERSON", "O")
    
    Returns:
        str: Simplified label (e.g., "TIME", "PERSON", "O")
    """
    if label == "O":
        return "O"
    
    # Remove B- or I- prefix
    if label.startswith("B-") or label.startswith("I-"):
        return label[2:]  # "B-TIME" -> "TIME", "I-TIME" -> "TIME"
    
    return label


def convert_dataset(input_path, output_path):
    """
    Convert dataset from BIO format to simplified format.
    
    Args:
        input_path (str): Path to input JSON file with BIO labels
        output_path (str): Path to output JSON file with simplified labels
    """
    print(f"Loading dataset from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert labels for each sample
    converted_samples = []
    total_labels_converted = 0
    
    for sample in data['samples']:
        original_labels = sample['labels']
        simplified_labels = [remove_bio_tags(label) for label in original_labels]
        
        converted_sample = sample.copy()
        converted_sample['labels'] = simplified_labels
        converted_samples.append(converted_sample)
        
        # Count conversions
        for orig, simp in zip(original_labels, simplified_labels):
            if orig != simp:
                total_labels_converted += 1
    
    # Create output data structure
    output_data = {
        'metadata': {
            **data.get('metadata', {}),
            'conversion_note': 'BIO tags removed - B-/I- prefixes converted to entity types only',
            'original_file': os.path.basename(input_path)
        },
        'samples': converted_samples
    }
    
    # Save converted dataset
    print(f"Saving converted dataset to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Conversion complete!")
    print(f"   Total samples: {len(converted_samples)}")
    print(f"   Labels converted: {total_labels_converted}")
    
    # Show example conversion
    if len(converted_samples) > 0:
        example = converted_samples[0]
        print(f"\nExample conversion (first sample):")
        print(f"   Tokens: {example['tokens'][:5]}...")
        print(f"   Original labels: {data['samples'][0]['labels'][:5]}...")
        print(f"   Simplified labels: {example['labels'][:5]}...")


if __name__ == "__main__":
    input_file = "selected_140_ontonotes5_samples.json"
    output_file = "selected_140_ontonotes5_samples_simplified.json"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, output_file)
    
    convert_dataset(input_path, output_path)






