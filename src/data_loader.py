"""
Data loader for OntoNotes5 (tner/ontonotes5) from HuggingFace.
Extracts sentences and BIO labels for NER evaluation in 5 classes:
Person, Location, Organization, Time, Currency.
"""

import os
from typing import List, Dict, Tuple

import yaml
from datasets import load_dataset


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# OntoNotes5 raw label groups mapped to project classes
ONTO2PROJECT = {
    # Person
    "PERSON": "PERSON",
    # Organization-like
    "ORG": "ORGANIZATION",
    "NORP": "ORGANIZATION",  # nationalities, religious, political groups
    # Location-like
    "GPE": "LOCATION",  # geopolitical entity
    "LOC": "LOCATION",
    "FAC": "LOCATION",  # facilities, treated as locations
    # Time
    "DATE": "TIME",
    "TIME": "TIME",
    # Currency / Money
    "MONEY": "CURRENCY",
}

PROJECT_ENTITY_TYPES = ["PERSON", "LOCATION", "ORGANIZATION", "TIME", "CURRENCY"]


def map_ontonotes_label(raw_label: str) -> str:
    """
    Map OntoNotes-style label (e.g., B-PERSON, I-ORG, O) to project label.

    Returns:
        str: Mapped BIO label with project class names or 'O'.
    """
    if raw_label == "O":
        return "O"

    if "-" not in raw_label:
        return "O"

    prefix, ent = raw_label.split("-", 1)
    mapped = ONTO2PROJECT.get(ent)
    if mapped is None:
        return "O"

    if prefix not in {"B", "I"}:
        return "O"

    return f"{prefix}-{mapped}"


def load_ontonotes5_subset(num_examples: int = 250, split: str = "train") -> List[Dict]:
    """
    Load OntoNotes5 subset from tner/ontonotes5 and map labels to 5 project classes.

    Args:
        num_examples (int): Number of sentences to sample.
        split (str): Dataset split to use (train/validation/test).

    Returns:
        list: List of dicts with 'tokens', 'labels', 'text'.
    """
    print(f"Loading OntoNotes5 dataset (tner/ontonotes5, split={split})...")
    ds = load_dataset("tner/ontonotes5", split=split)

    # Figure out which feature holds the tag IDs (usually "tags")
    tag_field_name = None
    for cand in ("tags", "ner_tags", "labels"):
        if cand in ds.features:
            tag_field_name = cand
            break
    if tag_field_name is None:
        raise KeyError("Could not find tag field ('tags' / 'ner_tags' / 'labels') in OntoNotes5 dataset")

    tag_feature = ds.features[tag_field_name].feature  # often ClassLabel, but not always

    # Some datasets expose ClassLabel with .names, others already store string tags.
    label_names = None
    if hasattr(tag_feature, "names"):
        label_names = tag_feature.names

    sentences: List[Dict] = []

    for example in ds:
        tokens = example.get("tokens") or example.get("words")
        tag_values = example.get(tag_field_name)

        if tokens is None or tag_values is None:
            continue

        # Convert to raw string labels only (no project mapping here).
        # We'll do careful mapping to PERSON/LOCATION/ORG/TIME/CURRENCY later in the pipeline.
        if label_names is not None:
            # tag_values are integer IDs → map via ClassLabel names
            raw_labels = [label_names[i] for i in tag_values]
        else:
            # tag_values are already strings
            raw_labels = [str(v) for v in tag_values]

        # Build text
        text = " ".join(tokens)

        sentences.append(
            {
                "tokens": tokens,
                "labels": raw_labels,  # keep original OntoNotes labels
                "text": text,
            }
        )

        if len(sentences) >= num_examples:
            break

    print(f"Loaded {len(sentences)} sentences from OntoNotes5 subset")

    # Cache to disk
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(cache_dir, exist_ok=True)
    # Store raw OntoNotes labels (no project mapping yet)
    cache_file = os.path.join(cache_dir, f"ontonotes5_raw_ner_{num_examples}.json")

    try:
        import json

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(sentences, f, indent=2, ensure_ascii=False)
        print(f"Cached OntoNotes5 subset to {cache_file}")
    except Exception as e:
        print(f"Warning: could not cache OntoNotes5 subset: {e}")

    return sentences


def load_project_dataset(num_examples: int = 250, split: str = "train") -> List[Dict]:
    """
    Public entry point for loading the project NER dataset.
    Currently uses OntoNotes5 subset (tner/ontonotes5).
    """
    # Try to load from cache first
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    cache_file = os.path.join(cache_dir, f"ontonotes5_raw_ner_{num_examples}.json")

    if os.path.exists(cache_file):
        try:
            import json

            print(f"Loading project dataset from cache: {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded {len(data)} sentences from cache")
            return data
        except Exception as e:
            print(f"Warning: could not load cached dataset: {e}")

    return load_ontonotes5_subset(num_examples=num_examples, split=split)


def get_few_shot_examples(data: List[Dict], num_examples: int = 3) -> List[Dict]:
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
    # Simple manual test
    subset = load_ontonotes5_subset(num_examples=5, split="train")
    print("\nFirst example:")
    print("Text:", subset[0]["text"])
    print("Tokens:", subset[0]["tokens"])
    print("Labels:", subset[0]["labels"])

