"""
Convert MISC labels to O in the simplified dataset
"""
import json
import os
from datetime import datetime

def convert_misc_to_o(input_path: str, output_path: str):
    """Convert all MISC labels to O"""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    converted_samples = []
    misc_count = 0
    total_labels = 0
    
    for sample in data['samples']:
        # Convert MISC to O
        converted_labels = ['O' if label == 'MISC' else label for label in sample['labels']]
        
        # Count conversions
        original_misc = sum(1 for l in sample['labels'] if l == 'MISC')
        misc_count += original_misc
        total_labels += len(sample['labels'])
        
        converted_samples.append({
            "tokens": sample["tokens"],
            "labels": converted_labels,
            "text": sample["text"],
            "token_count": sample.get("token_count", len(sample["tokens"])),
            "char_count": sample.get("char_count", len(sample["text"])),
            "entity_score": sample.get("entity_score", 0.0)
        })
    
    output_data = {
        "metadata": {
            "total_samples": len(converted_samples),
            "conversion_date": datetime.now().isoformat(),
            "conversion_note": "MISC labels converted to O - focus on 5 main entity types (PERSON, ORGANIZATION, LOCATION, TIME, CURRENCY)",
            "original_file": os.path.basename(input_path),
            "misc_labels_converted": misc_count,
            "total_labels": total_labels
        },
        "samples": converted_samples
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Conversion complete!")
    print(f"   Input file: {input_path}")
    print(f"   Output file: {output_path}")
    print(f"   Total samples: {len(converted_samples)}")
    print(f"   MISC labels converted to O: {misc_count} ({100*misc_count/total_labels:.2f}% of all labels)")
    print(f"\nLabel distribution in converted dataset:")
    
    # Count labels
    from collections import Counter
    all_labels = [l for s in converted_samples for l in s['labels']]
    label_counts = Counter(all_labels)
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"   {label:15s}: {count:5d} ({100*count/len(all_labels):.2f}%)")

if __name__ == "__main__":
    input_file = os.path.join(os.path.dirname(__file__), 'selected_140_ontonotes5_samples_simplified.json')
    output_file = os.path.join(os.path.dirname(__file__), 'selected_140_ontonotes5_samples_no_misc.json')
    convert_misc_to_o(input_file, output_file)

