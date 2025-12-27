"""Training script for Project3 NER fine-tuning."""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List

import numpy as np
import torch
from datasets import load_dataset
import evaluate
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

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
ID_TO_LABEL = {idx: label for label, idx in LABEL_TO_ID.items()}

seqeval = evaluate.load("seqeval")


def tokenize_and_align_labels(batch, tokenizer):
    tokenized = tokenizer(
        batch["tokens"],
        truncation=True,
        is_split_into_words=True,
        padding=False,
    )

    aligned_labels: List[List[int]] = []
    for i, labels in enumerate(batch["ner_tags"]):
        word_ids = tokenized.word_ids(batch_index=i)
        previous_word = None
        label_ids: List[int] = []
        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)
            elif word_id != previous_word:
                label_ids.append(labels[word_id])
            else:
                label_ids.append(-100)
            previous_word = word_id
        aligned_labels.append(label_ids)
    tokenized["labels"] = aligned_labels
    return tokenized


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions.argmax(-1)

    true_predictions: List[List[str]] = []
    true_labels: List[List[str]] = []

    for prediction, label in zip(predictions, labels):
        filtered_preds: List[str] = []
        filtered_labels: List[str] = []
        for pred, lab in zip(prediction, label):
            if lab == -100:
                continue
            filtered_preds.append(ID_TO_LABEL[pred])
            filtered_labels.append(ID_TO_LABEL[lab])
        true_predictions.append(filtered_preds)
        true_labels.append(filtered_labels)

    results = seqeval.compute(predictions=true_predictions, references=true_labels)
    return {
        "f1": results.get("overall_f1", 0.0),
        "precision": results.get("overall_precision", 0.0),
        "recall": results.get("overall_recall", 0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune a token classification model on Project3 data.")
    parser.add_argument("--model_save_path", required=True, help="Directory to store the trained model.")
    parser.add_argument("--dataset_path", required=True, help="Path to train.json produced by data_preparation.py.")
    parser.add_argument("--val_dataset_path", help="Optional validation dataset path.")
    parser.add_argument("--model_name", default="bert-base-uncased", help="HF model checkpoint to fine-tune.")
    parser.add_argument("--num_train_epoch", type=int, default=5, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=8, help="Per-device batch size.")
    parser.add_argument("--learning_rate", type=float, default=3e-5, help="Learning rate.")
    args = parser.parse_args()

    os.makedirs(args.model_save_path, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name,
        num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
    )

    train_dataset = load_dataset("json", data_files=args.dataset_path, split="train")
    val_dataset = None
    if args.val_dataset_path:
        if os.path.exists(args.val_dataset_path):
            val_dataset = load_dataset("json", data_files=args.val_dataset_path, split="train")
        else:
            print(f"Validation dataset not found at {args.val_dataset_path}. Continuing without validation.")

    tokenized_train = train_dataset.map(
        lambda batch: tokenize_and_align_labels(batch, tokenizer),
        batched=True,
        remove_columns=train_dataset.column_names,
    )

    tokenized_val = None
    if val_dataset is not None:
        tokenized_val = val_dataset.map(
            lambda batch: tokenize_and_align_labels(batch, tokenizer),
            batched=True,
            remove_columns=val_dataset.column_names,
        )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    has_val = tokenized_val is not None
    training_args = TrainingArguments(
        output_dir=args.model_save_path,
        num_train_epochs=args.num_train_epoch,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        evaluation_strategy="epoch" if has_val else "no",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=has_val,
        metric_for_best_model="f1" if has_val else None,
        greater_is_better=True,
        logging_steps=10,
        logging_first_step=True,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics if has_val else None,
    )

    trainer.train()
    trainer.save_model(args.model_save_path)
    tokenizer.save_pretrained(args.model_save_path)

    mapping = {
        "label_list": LABEL_LIST,
        "label_to_id": LABEL_TO_ID,
        "num_labels": len(LABEL_LIST),
    }
    with open(os.path.join(args.model_save_path, "label_mapping.json"), "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print("Training complete. Model saved to", args.model_save_path)


if __name__ == "__main__":
    main()
