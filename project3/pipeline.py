"""Inference pipeline for Project3 NER models."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from transformers import pipeline


def compute_token_spans(tokens: List[str], text: str) -> List[tuple[int, int]]:
    spans: List[tuple[int, int]] = []
    cursor = 0
    for token in tokens:
        # Find token occurrence starting from cursor to keep alignment stable.
        start = text.find(token, cursor)
        if start == -1:
            start = cursor
        end = start + len(token)
        spans.append((start, end))
        cursor = end
    return spans


def load_label_list(model_path: str) -> List[str]:
    mapping_path = os.path.join(model_path, "label_mapping.json")
    if not os.path.exists(mapping_path):
        return [
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
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    return mapping.get("label_list", [])


def run_pipeline(model_path: str, input_file: str, output_file: str) -> None:
    labels = load_label_list(model_path)
    ner_pipe = pipeline(
        "token-classification",
        model=model_path,
        aggregation_strategy="simple",
        device=-1,
    )

    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    outputs: List[Dict[str, Any]] = []
    for sample in dataset:
        tokens = sample["tokens"]
        text = " ".join(tokens)
        hf_predictions = ner_pipe(text)

        grouped_predictions = []
        token_predictions = ["O"] * len(tokens)
        spans = compute_token_spans(tokens, text)

        for pred in hf_predictions:
            entity_label = pred.get("entity_group", pred.get("entity", ""))
            start = int(pred.get("start", 0))
            end = int(pred.get("end", 0))
            score = float(pred.get("score", 0.0))
            grouped_predictions.append(
                {
                    "text": pred.get("word", ""),
                    "label": entity_label,
                    "start": start,
                    "end": end,
                    "score": score,
                }
            )

            tag_prefix = "B"
            for idx, (token_start, token_end) in enumerate(spans):
                if token_end <= start or token_start >= end:
                    continue
                token_predictions[idx] = f"{tag_prefix}-{entity_label}"
                tag_prefix = "I"

        outputs.append(
            {
                "text": text,
                "tokens": tokens,
                "predictions": token_predictions,
                "entities": grouped_predictions,
            }
        )

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)

    print(f"Saved predictions to {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NER inference using a saved Project3 model.")
    parser.add_argument("--model_load_path", required=True)
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_file", required=True)
    args = parser.parse_args()

    run_pipeline(args.model_load_path, args.input_file, args.output_file)


if __name__ == "__main__":
    main()
