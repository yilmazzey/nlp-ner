# NER Annotation Pipeline Guide

## Overview

This guide explains how to use the annotation pipeline to evaluate NER performance across 4 LLMs and 3 prompt styles.

## Step 1: Extract Raw Texts

Extract raw text fields from the dataset:

```bash
python extract_raw_texts.py
```

This creates `data/raw_texts.json` containing just the text strings (140 sentences).

## Step 2: Run Annotation Pipeline

Run the full annotation pipeline:

```bash
python annotate_dataset.py
```

This will:
1. Load raw texts and gold labels
2. For each of 4 LLMs × 3 prompt styles = 12 combinations:
   - Generate predictions using the LLM
   - Calculate F1-scores per entity type (PER, ORG, LOC, MISC)
   - Calculate overall F1-score
3. Save results to:
   - `results/all_predictions.json` - All predictions
   - `results/comparison_table.csv` - F1 scores for all combinations

## Step 3: Review Results

The comparison table (`results/comparison_table.csv`) contains:
- Model name
- Prompt type (zero_shot, few_shot, chain_of_thought)
- F1 scores for each entity type (PER, ORG, LOC, MISC)
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
- **F1-score per entity type**: PER, ORG, LOC, MISC
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
3. Dataset files exist:
   - `data/conll2003_validation_140.json`
   - `data/raw_texts.json`

## Output Format

### Predictions JSON
```json
{
  "gpt-4o_zero_shot": {
    "model": "gpt-4o",
    "prompt_type": "zero_shot",
    "predictions": [
      ["B-PER", "I-PER", "O", "B-LOC", ...],
      ...
    ]
  },
  ...
}
```

### Comparison CSV
```csv
Model,Prompt_Type,F1_PER,F1_ORG,F1_LOC,F1_MISC,F1_Overall
gpt-4o,zero_shot,0.85,0.78,0.82,0.71,0.79
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


