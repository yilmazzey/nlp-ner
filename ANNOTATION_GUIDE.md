# NER Annotation Pipeline Guide

## Overview

This guide explains how to use the annotation pipeline to evaluate NER performance across 4 LLMs and 3 prompt styles on a 250-example subset of OntoNotes5.

## Step 1: Prepare Dataset

The core dataset is loaded via `src.data_loader.load_project_dataset`, which builds (and caches) a 250-example OntoNotes5 subset:

```python
from src.data_loader import load_project_dataset

data = load_project_dataset(num_examples=250)
print(len(data))
```

This creates (and reuses) `data/ontonotes5_ner_250.json`.

## Step 2: Run Annotation Pipeline

Run the full annotation pipeline:

```bash
python annotate_dataset.py
```

This will:
1. Load gold labels from the OntoNotes5 subset (250 examples)
2. For each of 4 LLMs × 3 prompt styles = 12 combinations:
   - Generate predictions using the LLM
   - Calculate F1-scores per entity type (Person, Location, Organization, Time, Currency)
   - Calculate overall F1-score
3. Save results to:
   - `results/all_predictions.json` - All predictions
   - `results/comparison_table.csv` - F1 scores for all combinations

## Step 3: Review Results

The comparison table (`results/comparison_table.csv`) contains:
- Model name
- Prompt type (zero_shot, few_shot, chain_of_thought)
- F1 scores for each entity type (Person, Location, Organization, Time, Currency)
- Overall F1 score

## Models and Prompts

### Models (4 total):
1. **GPT-4o** or **GPT-4o-mini** (OpenAI)
2. **Gemini 1.5 Flash** (Google)
3. **Llama-3.1-8B-Instruct** (Ollama)
4. **Mistral-7B-Instruct-v0.3** (Ollama)

### Prompt Styles (3 total):
1. **Zero-shot**: Basic instruction prompt
2. **Few-shot**: Includes 3 example sentences with correct labels
3. **Chain-of-Thought**: Includes reasoning steps before entity identification

## Evaluation Metrics

The evaluator calculates:
- **F1-score per entity type**: Person, Location, Organization, Time, Currency
- **Overall F1-score**: Micro-averaged across all entity types
- **Entity-level matching**: Compares entities (not just tokens) for accuracy

## Requirements

Before running, ensure:
1. API keys are set in `configs/config.yaml`:
   - OpenAI API key (for GPT models)
   - Google AI API key (for Gemini)
   - HuggingFace token (for dataset access)
2. Ollama is running (for local models):
   ```bash
   ollama pull llama3.1:8b-instruct
   ollama pull mistral:7b-instruct-v0.3
   ```
3. Dataset files exist (generated on first run):
   - `data/ontonotes5_ner_250.json`

## Output Format

### Predictions JSON
```json
{
  "gpt-4o_zero_shot": {
    "model": "gpt-4o",
    "prompt_type": "zero_shot",
    "predictions": [
      ["B-PERSON", "I-PERSON", "O", "B-LOCATION", ...],
      ...
    ]
  },
  ...
}
```

### Comparison CSV
```csv
Model,Prompt_Type,F1_PERSON,F1_ORGANIZATION,F1_LOCATION,F1_TIME,F1_CURRENCY,F1_Overall
gpt-4o,zero_shot,0.85,0.78,0.82,0.71,0.60,0.79
...
```

## Troubleshooting

### API Errors
- Check API keys in `configs/config.yaml`
- Verify API quotas/limits
- Check network connectivity

### Ollama Errors
- Ensure Ollama is running: `ollama list`
- Pull required models: `ollama pull <model-name>`
- Check Ollama URL in config (default: http://localhost:11434)

### Tokenization Mismatches
- The predictor uses simple whitespace tokenization
- LLM responses are parsed to extract BIO labels
- If predictions don't match token count, they're padded/truncated

## Next Steps

After annotation:
1. Review `results/comparison_table.csv` to find best model+prompt
2. Use best combination for Dataset2 annotation (scraped news)
3. Generate report with F1 scores, prompts, and analysis


