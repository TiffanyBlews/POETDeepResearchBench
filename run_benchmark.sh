#!/bin/bash
# POET Bench - Complete Evaluation Pipeline
# This script runs the full POET benchmark evaluation with example data

# ===========================================
# 🚀 QUICK START CONFIGURATION
# ===========================================

# Target model name list (matches files in data/test_data/raw_data/)
TARGET_MODELS=("gpt")

# Common parameters for both RACE and Citation evaluations
RAW_DATA_DIR="data/test_data/raw_data"
OUTPUT_DIR="results"
N_TOTAL_PROCESS=2
QUERY_DATA_PATH="data/prompt_data/query.jsonl"

# 🎯 POET Query selection parameters (RECOMMENDED: Enable for full POET evaluation)
ENABLE_QUERY_SELECTION=true     # Set to true for POET evaluation
QUERY_THRESHOLD=4.0             # Minimum score threshold for query selection
QUERY_INPUT_FILE="data/query_analysis/raw_query.md"
QUERY_OUTPUT_DIR="data/query_analysis/"

# ===========================================
# 🔧 OPTIONAL CONFIGURATION
# ===========================================

# Limit on number of prompts to process (for testing). Uncomment to enable
LIMIT="--limit 5"               # Uncomment for quick testing

# Skip article cleaning step. Uncomment to enable
# SKIP_CLEANING="--skip_cleaning"

# Only process specific language data. Uncomment to enable
# ONLY_ZH="--only_zh"           # Only process Chinese data
# ONLY_EN="--only_en"           # Only process English data

# Force re-evaluation even if results exist. Uncomment to enable
# FORCE="--force"

# Specify log output file
OUTPUT_LOG_FILE="output.log"

# ===========================================
# 📋 PRE-FLIGHT CHECKS
# ===========================================

echo "🚀 POET Bench - Complete Evaluation Pipeline"
echo "=============================================="

# Clear log file
echo "Starting POET benchmark evaluation, log output to: $OUTPUT_LOG_FILE" > "$OUTPUT_LOG_FILE"

# Check required files
echo "Checking required files..."
REQUIRED_FILES=(
    "$QUERY_INPUT_FILE"
    "data/prompt_data/query.jsonl"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        echo "Please ensure all example data files are present."
        exit 1
    else
        echo "✅ Found: $file"
    fi
done

# Check environment variables
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. Some features may not work."
fi

if [[ -z "$JINA_API_KEY" ]]; then
    echo "⚠️  Warning: JINA_API_KEY not set. Web scraping in FACT evaluation will fail."
fi

echo ""
echo "🎯 Configuration Summary:"
echo "  Target Models: ${TARGET_MODELS[*]}"
echo "  POET Query Selection: $ENABLE_QUERY_SELECTION"
echo "  Query Threshold: $QUERY_THRESHOLD"
echo "  Process Limit: ${LIMIT:-"No limit"}"
echo "  Output Directory: $OUTPUT_DIR"
echo ""

# Note: Query selection and criteria generation are integrated into the RACE evaluation phase

# ===========================================
# 🔄 MAIN EVALUATION LOOP
# ===========================================

# Loop through each model in the target models list
for TARGET_MODEL in "${TARGET_MODELS[@]}"; do
  echo "🔄 Running benchmark for target model: $TARGET_MODEL"
  echo -e "\n\n========== Starting evaluation for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"

  # Check if model data exists
  MODEL_DATA_FILE="$RAW_DATA_DIR/$TARGET_MODEL.jsonl"
  if [[ ! -f "$MODEL_DATA_FILE" ]]; then
    echo "❌ Model data file not found: $MODEL_DATA_FILE"
    echo "Skipping $TARGET_MODEL..."
    continue
  fi
  echo "✅ Found model data: $MODEL_DATA_FILE"

  # --- Phase 1: POET Query Selection & RACE Evaluation ---
  echo ""
  echo "📊 Phase 1: POET Query Selection & RACE Evaluation for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  RACE_OUTPUT="$OUTPUT_DIR/race/$TARGET_MODEL"
  mkdir -p $RACE_OUTPUT

  # Base command for current target model
  PYTHON_CMD="python -u deepresearch_bench_race.py \"$TARGET_MODEL\" --raw_data_dir $RAW_DATA_DIR --max_workers $N_TOTAL_PROCESS --query_file $QUERY_DATA_PATH --output_dir $RACE_OUTPUT"

  # Add POET query selection parameters
  if [[ "$ENABLE_QUERY_SELECTION" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --enable_query_selection --query_selection_threshold $QUERY_THRESHOLD --raw_query_file $QUERY_INPUT_FILE --query_analysis_dir $QUERY_OUTPUT_DIR"
  fi

  # Add optional parameters
  if [[ -n "$LIMIT" ]]; then
    PYTHON_CMD="$PYTHON_CMD $LIMIT"
  fi

  if [[ -n "$SKIP_CLEANING" ]]; then
    PYTHON_CMD="$PYTHON_CMD $SKIP_CLEANING"
  fi

  if [[ -n "$ONLY_ZH" ]]; then
    PYTHON_CMD="$PYTHON_CMD $ONLY_ZH"
  fi

  if [[ -n "$ONLY_EN" ]]; then
    PYTHON_CMD="$PYTHON_CMD $ONLY_EN"
  fi

  if [[ -n "$FORCE" ]]; then
    PYTHON_CMD="$PYTHON_CMD $FORCE"
  fi

  # Execute command and append stdout and stderr to single log file
  echo "Executing command: $PYTHON_CMD" | tee -a "$OUTPUT_LOG_FILE"
  eval $PYTHON_CMD >> "$OUTPUT_LOG_FILE" 2>&1

  echo "✅ Completed RACE benchmark test for target model: $TARGET_MODEL"
  echo -e "\n========== RACE test completed for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"

  # --- Phase 2: FACT Citation Evaluation ---
  echo ""
  echo "🔗 Phase 2: FACT Citation Evaluation for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  CITATION_OUTPUT="$OUTPUT_DIR/fact/$TARGET_MODEL"
  RAW_DATA_PATH="$RAW_DATA_DIR/$TARGET_MODEL.jsonl"
  mkdir -p $CITATION_OUTPUT
  echo "Extracting citations for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  python -u -m utils.extract --raw_data_path $RAW_DATA_PATH --output_path $CITATION_OUTPUT/extracted.jsonl --query_data_path $QUERY_DATA_PATH --n_total_process $N_TOTAL_PROCESS
  echo "Deduplicate citations for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  python -u -m utils.deduplicate --raw_data_path $CITATION_OUTPUT/extracted.jsonl --output_path $CITATION_OUTPUT/deduplicated.jsonl --query_data_path $QUERY_DATA_PATH --n_total_process $N_TOTAL_PROCESS
  echo "Scrape webpages for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  python -u -m utils.scrape --raw_data_path $CITATION_OUTPUT/deduplicated.jsonl --output_path $CITATION_OUTPUT/scraped.jsonl --n_total_process 1
  echo "Validate citations for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  python -u -m utils.validate --raw_data_path $CITATION_OUTPUT/scraped.jsonl --output_path $CITATION_OUTPUT/validated.jsonl --query_data_path $QUERY_DATA_PATH --n_total_process $N_TOTAL_PROCESS
  echo "Collecting statistics for $TARGET_MODEL" | tee -a "$OUTPUT_LOG_FILE"
  python -u -m utils.stat --input_path $CITATION_OUTPUT/validated.jsonl --output_path $CITATION_OUTPUT/fact_result.txt
  echo "✅ Completed FACT benchmark test for target model: $TARGET_MODEL"
  echo -e "\n========== FACT test completed for $TARGET_MODEL ==========\n" >> "$OUTPUT_LOG_FILE"
  echo ""
  echo "🎉 $TARGET_MODEL evaluation completed successfully!"
  echo "📊 Results saved in:"
  echo "   - RACE: $RACE_OUTPUT/race_result.txt"
  echo "   - FACT: $CITATION_OUTPUT/fact_result.txt"
  echo "--------------------------------------------------"
done

echo ""
echo "🎉 All benchmark tests completed successfully!"
echo "📋 Full logs saved in: $OUTPUT_LOG_FILE"
echo "📊 Results directory: $OUTPUT_DIR"
echo ""
echo "🚀 Next steps:"
echo "  1. Check results in the '$OUTPUT_DIR' directory"
echo "  2. View detailed logs in '$OUTPUT_LOG_FILE'"
echo "  3. Use different query thresholds by modifying QUERY_THRESHOLD and re-running"
