#!/bin/zsh

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
EPOCHS=${1:-3}

if [ ! -f "$ROOT_DIR/data/train.json" ] || [ ! -f "$ROOT_DIR/data/test.json" ]; then
  echo "Preparing datasets..."
  python "$ROOT_DIR/data_preparation.py"
fi

python "$ROOT_DIR/train.py" \
  --model_save_path "$ROOT_DIR/models/saved_model" \
  --dataset_path "$ROOT_DIR/data/train.json" \
  --num_train_epoch "$EPOCHS"

python "$ROOT_DIR/pipeline.py" \
  --model_load_path "$ROOT_DIR/models/saved_model" \
  --input_file "$ROOT_DIR/data/test.json" \
  --output_file "$ROOT_DIR/outputs/predictions.json"

