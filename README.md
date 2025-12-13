# NER Prompt Engineering Project - COMP 451 Project #2

This project evaluates Named Entity Recognition (NER) performance using prompt engineering with multiple Large Language Models (LLMs).

## Project Overview

- **4 LLMs**: GPT-4o/GPT-4o-mini (OpenAI), Gemini 1.5 Flash (Google), Llama-3.1-8B-Instruct (Ollama), Mistral-7B-Instruct-v0.3 (Ollama)
- **3 Prompt Styles**: Zero-shot, 3-shot Few-shot, Chain-of-Thought
- **12 Combinations**: All model × prompt combinations evaluated
- **Dataset**: 140 sentences from conll2003 validation split
- **Web Scraping**: 70+ news paragraphs from BBC/Hurriyet

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys in `configs/config.yaml`:
```yaml
openai:
  api_key: "your-openai-api-key"
google_ai:
  api_key: "your-google-ai-api-key"
```

3. For Ollama models, ensure Ollama is installed and running:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.1:8b-instruct
ollama pull mistral:7b-instruct-v0.3
```

## Usage

### Quick Start (Run Full Pipeline)

```bash
python run_pipeline.py
```

This will run all steps: scraping, comparison, and annotation.

You can also run individual steps:
```bash
python run_pipeline.py --step scrape    # Only web scraping
python run_pipeline.py --step compare   # Only comparison
python run_pipeline.py --step annotate  # Only annotation (requires comparison_table.csv)
```

### Manual Usage

#### 1. Load and Evaluate on conll2003

```python
from src.data_loader import load_conll2003
from src.comparison import run_comparison

# Load 140 sentences from validation split
data = load_conll2003(num_sentences=140)

# Run all 12 combinations and generate comparison table
run_comparison(data, output_path="results/comparison_table.csv")
```

#### 2. Web Scraping

```bash
python scraping/news_scraper.py
```

This will scrape news articles and save 70+ paragraphs to `dataset2/raw_news.json`.

#### 3. Annotate Dataset2

```python
from src.annotator import annotate_dataset2

# Uses best model+prompt from comparison results
annotate_dataset2(
    input_path="dataset2/raw_news.json",
    output_path="dataset2/final_annotated.json"
)
```

## Project Structure

```
ner_nlp/
├── scraping/
│   └── news_scraper.py          # Web scraping script
├── dataset2/
│   └── final_annotated.json     # Required submission file
├── src/
│   ├── data_loader.py           # Load conll2003 dataset
│   ├── prompts.py               # Prompt templates
│   ├── openai_client.py         # OpenAI API client
│   ├── gemini_client.py         # Google Gemini API client
│   ├── ollama_client.py         # Ollama API client
│   ├── predictor.py             # Main prediction function
│   ├── evaluator.py             # F1-score evaluation
│   ├── annotator.py             # Dataset2 annotation
│   └── comparison.py            # Generate comparison table
├── results/
│   └── comparison_table.csv     # F1 scores for all combinations
└── configs/
    └── config.yaml              # Configuration file
```

## Results

The comparison table (`results/comparison_table.csv`) contains F1 scores for:
- Each entity type (PER, ORG, LOC, MISC)
- Overall F1 score
- All 12 model × prompt combinations

## Notes

- Ensure API keys are set in `configs/config.yaml`
- Ollama must be running for local model inference
- Web scraping may take time depending on network speed
- Evaluation on 140 sentences may take 30-60 minutes depending on API rate limits

