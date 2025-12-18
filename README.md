# NER Prompt Engineering Project - COMP 451 Project #2

This project evaluates Named Entity Recognition (NER) performance using prompt engineering with multiple Large Language Models (LLMs).

## Project Overview

- **4 LLMs**: GPT-4o/GPT-4o-mini (OpenAI), Gemini 1.5 Flash (Google), Llama-3.1-8B-Instruct (Ollama), Mistral-7B-Instruct-v0.3 (Ollama)
- **3 Prompt Styles**: Zero-shot, 3-shot Few-shot, Chain-of-Thought
- **12 Combinations**: All model × prompt combinations evaluated
- **Core Dataset**: 250 sentences sampled from the OntoNotes5 NER corpus via `tner/ontonotes5`
- **Target NER Classes**: Person, Location, Organization, Time, Currency
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

#### 1. Load and Evaluate on OntoNotes5 Subset

```python
from src.data_loader import load_project_dataset
from src.comparison import run_comparison

# Load 250 sentences from OntoNotes5 subset
data = load_project_dataset(num_examples=250)

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
│   ├── data_loader.py           # Load OntoNotes5 (tner/ontonotes5) subset
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
- Each entity type (Person, Location, Organization, Time, Currency)
- Overall F1 score
- All 12 model × prompt combinations

## Dataset Details and Citation

The core NER dataset used in this project is a 250-example subset of **OntoNotes5**, accessed via the Hugging Face dataset `tner/ontonotes5`.  
We map the rich OntoNotes label space onto five target classes:

- **Person**
- **Location**
- **Organization**
- **Time**
- **Currency**

For more details about OntoNotes, see:

> Hovy, Eduard, Mitchell Marcus, Martha Palmer, Lance Ramshaw, and Ralph Weischedel. 2006.  
> “OntoNotes: The 90% Solution.” In *Proceedings of the Human Language Technology Conference of the NAACL, Companion Volume: Short Papers*, 57–60, New York City, USA. Association for Computational Linguistics.  
> [https://aclanthology.org/N06-2015](https://aclanthology.org/N06-2015)

## Notes

- Ensure API keys are set in `configs/config.yaml`
- Ollama must be running for local model inference
- Web scraping may take time depending on network speed
- Evaluation on 140 sentences may take 30-60 minutes depending on API rate limits

