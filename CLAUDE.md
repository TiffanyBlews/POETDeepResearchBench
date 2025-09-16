# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POET Bench is a comprehensive benchmark for evaluating Deep Research Agents (DRAs) based on real commercial value. \

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

### Running Evaluations

**Main benchmark evaluation with POET query selection:**
```bash
bash run_benchmark.sh
```

**Manual RACE evaluation with POET query selection:**
```bash
python -u deepresearch_bench_race.py "model_name" \
    --raw_data_dir data/test_data/raw_data \
    --max_workers 10 \
    --query_file data/prompt_data/query.jsonl \
    --output_dir results/race/model_name \
    --enable_query_selection \
    --query_selection_threshold 4.0 \
    --raw_query_file data/query_analysis/raw_query.md
```

**Standalone query selection (optional):**
```bash
# Select high-value queries using POET criteria
python query_selector.py --input_file data/query_analysis/raw_query.md --output_dir data/query_analysis/ --threshold 4.0 --export_selected
```

**Manual RACE evaluation only (without query selection):**
```bash
python -u deepresearch_bench_race.py "model_name" --raw_data_dir data/test_data/raw_data --max_workers 10 --query_file data/prompt_data/query.jsonl --output_dir results/race/model_name
```

**FACT evaluation components (run in sequence):**
```bash
# Extract citations
python -u -m utils.extract --raw_data_path data/test_data/raw_data/model_name.jsonl --output_path results/fact/model_name/extracted.jsonl --query_data_path data/prompt_data/query.jsonl --n_total_process 10

# Deduplicate citations
python -u -m utils.deduplicate --raw_data_path results/fact/model_name/extracted.jsonl --output_path results/fact/model_name/deduplicated.jsonl --query_data_path data/prompt_data/query.jsonl --n_total_process 10

# Scrape webpages
python -u -m utils.scrape --raw_data_path results/fact/model_name/deduplicated.jsonl --output_path results/fact/model_name/scraped.jsonl --n_total_process 10

# Validate citations
python -u -m utils.validate --raw_data_path results/fact/model_name/scraped.jsonl --output_path results/fact/model_name/validated.jsonl --query_data_path data/prompt_data/query.jsonl --n_total_process 10

# Generate statistics
python -u -m utils.stat --input_path results/fact/model_name/validated.jsonl --output_path results/fact/model_name/fact_result.txt
```

## Architecture

### Core Components

**Evaluation Scripts:**
- `deepresearch_bench_race.py`: Main RACE evaluation implementation with weighted scoring across 4 dimensions (comprehensiveness, depth, instruction-following, readability)
- `run_benchmark.sh`: Orchestrates full evaluation pipeline for multiple models

**Utils Pipeline:**
- `utils/extract.py`: Extracts factual statements and citations from research articles
- `utils/deduplicate.py`: Removes duplicate statement-URL pairs
- `utils/scrape.py`: Web scraping for citation validation using Jina API
- `utils/validate.py`: LLM-based verification of whether citations support claims
- `utils/stat.py`: Generates final FACT evaluation statistics
- `utils/api.py`: AIClient wrapper for LLM API calls (configured for Gemini)

**Data Processing:**
- `utils/clean_article.py`: ArticleCleaner for preprocessing research articles
- `utils/score_calculator.py`: Weighted scoring calculations for RACE evaluation
- `utils/json_extractor.py`: JSON extraction from LLM markdown responses

### Key Data Formats

**Input format for model outputs** (`data/test_data/raw_data/<model_name>.jsonl`):
```json
{
    "id": "task_id",
    "prompt": "original_query_text",
    "article": "generated_research_article_with_citations"
}
```

**Benchmark queries:** `data/prompt_data/query.jsonl` (100 tasks)

**Results location:**
- RACE: `results/race/<model_name>/race_result.txt`
- FACT: `results/fact/<model_name>/fact_result.txt`

## Configuration

### Required Environment Variables
```bash
export OPENAI_API_KEY="your_openai_api_key_here"    # For LLM evaluation
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"  # OpenAI compatible API base URL
export OPENAI_MODEL="google/gemini-2.5-pro"         # Model name to use
export JINA_API_KEY="your_jina_api_key_here"        # For web scraping
```

### Customizing Models to Evaluate
Edit `TARGET_MODELS` array in `run_benchmark.sh`:
```bash
TARGET_MODELS=("your-model-name" "another-model")
```

### Evaluation Parameters
Key parameters in `run_benchmark.sh`:
- `N_TOTAL_PROCESS=10`: Number of parallel processes
- `LIMIT="--limit 2"`: Uncomment to limit number of queries for testing
- `SKIP_CLEANING="--skip_cleaning"`: Skip article preprocessing
- `ONLY_ZH="--only_zh"` / `ONLY_EN="--only_en"`: Language-specific evaluation

## Development Notes

- The codebase supports both Chinese and English evaluation with separate prompt templates in `prompt/`
- Multi-threaded evaluation with configurable worker processes
- Retry logic built into API calls (MAX_RETRIES=10)
- Results are logged to `output.log` during benchmark runs
- Uses OpenAI compatible API for LLM evaluation, configured via environment variables
- Custom LLM integration possible by modifying `AIClient` class in `utils/api.py`
- 项目整体流程参考POET.MD