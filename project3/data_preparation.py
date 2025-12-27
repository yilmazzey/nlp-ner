"""Data preparation utilities for Project3.

Builds train/test splits using Dataset1 as the baseline and Dataset2 as
additional training data. Dataset2 labels are normalised with regex and
converted into BIO format before merging.
"""

from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set

from sklearn.model_selection import train_test_split  # noqa: F401 (kept for quick exploration)

# Canonical label space
LABEL_LIST = [
    "O",
    "B-PERSON",
    "I-PERSON",
    "B-ORGANIZATION",
    "I-ORGANIZATION",
    "B-LOCATION",
    "I-LOCATION",
    "B-TIME",
    "I-TIME",
    "B-CURRENCY",
    "I-CURRENCY",
]
LABEL_TO_ID = {label: idx for idx, label in enumerate(LABEL_LIST)}

# Mapping from canonical entity group to BIO prefixes
ENTITY_TO_PREFIX = {
    "PERSON": ("B-PERSON", "I-PERSON"),
    "ORGANIZATION": ("B-ORGANIZATION", "I-ORGANIZATION"),
    "LOCATION": ("B-LOCATION", "I-LOCATION"),
    "TIME": ("B-TIME", "I-TIME"),
    "CURRENCY": ("B-CURRENCY", "I-CURRENCY"),
}

# Regex helpers reused when normalising Dataset2 labels
NON_ALPHA_RE = re.compile(r"[^A-Za-z]")
ORG_RE = re.compile(r"ORG|ORGANIZATION|COMPANY|CORP", re.IGNORECASE)
LOC_RE = re.compile(r"LOC|LOCATION|GPE|COUNTRY|CITY|STATE", re.IGNORECASE)
TIME_RE = re.compile(r"TIME|DATE|DAY|MONTH|YEAR|DECADE", re.IGNORECASE)
CURRENCY_RE = re.compile(r"CURRENCY|MONEY|DOLLAR|EURO|POUND|YEN", re.IGNORECASE)


@dataclass
class Sample:
    """In-memory representation of a token/label example."""

    tokens: Sequence[str]
    labels: Sequence[str]

    def to_hf_example(self) -> Dict[str, Sequence[str]]:
        return {"tokens": list(self.tokens), "ner_tags": [LABEL_TO_ID[label] for label in self.labels]}

    def entity_bases(self) -> Set[str]:
        bases: Set[str] = set()
        for label in self.labels:
            if label == "O":
                continue
            _, suffix = label.split("-", 1)
            bases.add(suffix)
        return bases


def load_dataset1(path: str) -> List[Sample]:
    """Load Dataset1 (curated OntoNotes subset) and clean labels."""

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    samples: List[Sample] = []
    for raw in payload.get("samples", []):
        tokens = raw["tokens"]
        labels = []
        for label in raw["labels"]:
            if label.startswith("B-MISC") or label.startswith("I-MISC"):
                labels.append("O")
            elif label in LABEL_TO_ID:
                labels.append(label)
            else:
                # Default to O if label not recognised.
                labels.append("O")
        if len(tokens) != len(labels):
            raise ValueError("Dataset1 mismatch between tokens and labels")
        samples.append(Sample(tokens=tokens, labels=labels))
    return samples


def normalise_dataset2_label(label: str) -> str:
    """Normalise Dataset2 label strings using regex heuristics."""

    if not label or label.upper() == "O":
        return "O"

    cleaned = NON_ALPHA_RE.sub("", label).upper()
    if not cleaned:
        return "O"

    if ORG_RE.fullmatch(cleaned) or ORG_RE.search(cleaned):
        return "ORGANIZATION"
    if LOC_RE.fullmatch(cleaned) or LOC_RE.search(cleaned):
        return "LOCATION"
    if TIME_RE.fullmatch(cleaned) or TIME_RE.search(cleaned):
        return "TIME"
    if CURRENCY_RE.fullmatch(cleaned) or CURRENCY_RE.search(cleaned):
        return "CURRENCY"
    if cleaned.startswith("PERSON") or cleaned in {"PERSON", "PEOPLE", "INDIVIDUAL", "INDIVIDUALS"}:
        return "PERSON"
    if cleaned in {"NORP", "NATIONALITY", "RELIGION"}:
        # Treat NORP-like categories as ORGANIZATION for consistency.
        return "ORGANIZATION"

    return "O"


def convert_to_bio(base_labels: Sequence[str]) -> List[str]:
    """Convert normalised base labels into BIO-formatted labels."""

    bio_labels: List[str] = []
    previous = "O"
    for base in base_labels:
        if base == "O":
            bio_labels.append("O")
            previous = "O"
            continue
        if base not in ENTITY_TO_PREFIX:
            bio_labels.append("O")
            previous = "O"
            continue
        prefix = ENTITY_TO_PREFIX[base][0 if previous != base else 1]
        bio_labels.append(prefix)
        previous = base
    return bio_labels


def load_dataset2(path: str) -> List[Sample]:
    """Load Dataset2, normalise labels with regex, and convert to BIO."""

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    raw_samples = payload.get("samples", payload)
    samples: List[Sample] = []
    converted = 0
    dropped = 0

    for raw in raw_samples:
        tokens = raw.get("tokens")
        labels = raw.get("labels")
        if not tokens or not labels or len(tokens) != len(labels):
            dropped += 1
            continue

        base_labels = [normalise_dataset2_label(label) for label in labels]
        bio_labels = convert_to_bio(base_labels)
        samples.append(Sample(tokens=tokens, labels=bio_labels))
        converted += 1

    print(f"Dataset2: converted {converted} samples, dropped {dropped} malformed entries.")
    return samples


def choose_test_indices(samples: Sequence[Sample], test_fraction: float, seed: int = 42) -> List[int]:
    """Select test indices ensuring coverage of all entity classes present."""

    total = len(samples)
    if total == 0:
        return []

    desired = max(1, round(total * test_fraction))

    rng = random.Random(seed)
    all_indices = list(range(total))
    rng.shuffle(all_indices)

    # Determine required classes from Dataset1 coverage.
    required_classes: Set[str] = set()
    for sample in samples:
        required_classes.update(sample.entity_bases())

    test_indices: Set[int] = set()
    covered: Set[str] = set()

    for idx in all_indices:
        if len(test_indices) >= desired and covered >= required_classes:
            break
        sample_classes = samples[idx].entity_bases()
        if not sample_classes:
            continue
        if not sample_classes.issubset(covered) or len(test_indices) < desired:
            test_indices.add(idx)
            covered.update(sample_classes)
            if len(test_indices) == desired and covered >= required_classes:
                break

    # Fill up remaining slots if coverage satisfied but count below desired.
    if len(test_indices) < desired:
        for idx in all_indices:
            if idx in test_indices:
                continue
            test_indices.add(idx)
            if len(test_indices) == desired:
                break

    return sorted(test_indices)


def summarise_split(name: str, samples: Sequence[Sample]) -> None:
    label_counts: Dict[str, int] = {label: 0 for label in LABEL_LIST}
    for sample in samples:
        for label in sample.labels:
            label_counts[label] += 1
    total_tokens = sum(len(sample.tokens) for sample in samples)
    print(f"\n{name} split: {len(samples)} samples, {total_tokens} tokens")
    for label in LABEL_LIST:
        if label == "O":
            continue
        count = label_counts[label]
        if count:
            print(f"  {label:14s}: {count}")


def save_split(path: str, samples: Sequence[Sample]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = [sample.to_hf_example() for sample in samples]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    dataset1_path = os.path.join(root, "..", "data", "selected_140_ontonotes5_samples.json")
    dataset2_path = os.path.join(root, "..", "dataset2", "final_annotated.json")

    dataset1 = load_dataset1(dataset1_path)
    dataset2 = load_dataset2(dataset2_path)

    print(f"Dataset1: {len(dataset1)} samples loaded.")
    print(f"Dataset2: {len(dataset2)} samples ready for training.")

    test_indices = choose_test_indices(dataset1, test_fraction=0.15, seed=42)
    test_set = [dataset1[idx] for idx in test_indices]
    train_seed_indices = [idx for idx in range(len(dataset1)) if idx not in test_indices]
    train_seed = [dataset1[idx] for idx in train_seed_indices]

    required_classes: Set[str] = set()
    for sample in dataset1:
        required_classes.update(sample.entity_bases())
    test_coverage: Set[str] = set()
    for sample in test_set:
        test_coverage.update(sample.entity_bases())
    missing = required_classes - test_coverage
    if missing:
        raise RuntimeError(
            "Test split is missing required entity classes: " + ", ".join(sorted(missing))
        )

    # Combine Dataset1 train portion with all of Dataset2
    train_set = train_seed + dataset2

    summarise_split("Train", train_set)
    summarise_split("Test", test_set)

    # Persist splits
    save_split(os.path.join(root, "data", "train.json"), train_set)
    save_split(os.path.join(root, "data", "test.json"), test_set)

    # Save label mapping for downstream scripts
    label_mapping = {
        "label_list": LABEL_LIST,
        "label_to_id": LABEL_TO_ID,
        "num_labels": len(LABEL_LIST),
    }
    with open(os.path.join(root, "data", "label_mapping.json"), "w", encoding="utf-8") as f:
        json.dump(label_mapping, f, indent=2, ensure_ascii=False)

    print("\nSaved train/test splits and label mapping to project3/data/.")


if __name__ == "__main__":
    main()

