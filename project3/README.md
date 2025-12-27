# Project3: Custom NER Fine-tuning

Fresh setup focused on our curated datasets instead of the full OntoNotes5 release.

## Dataset Strategy

- **Dataset1** (`../data/selected_140_ontonotes5_samples.json`)
  - Acts as the canonical, human-reviewed baseline.
  - Converted to 11-label BIO format (MISC mapped to `O`).
  - Split deterministically: 85% train contribution + 15% held-out test.
- **Dataset2** (`../dataset2/final_annotated.json`)
  - Auto-annotated paragraphs.
  - Labels normalised with regex-backed cleaning and converted to BIO.
  - Entire dataset flows into the training split only.

The resulting train split combines `Dataset1_train` and `Dataset2_bio`; the test split is the remaining 15% of Dataset1 and is guaranteed to contain every entity class we train on (PERSON, ORGANIZATION, LOCATION, TIME, CURRENCY).

## Usage

1. Install requirements (first time only):
   ```bash
   cd project3
   pip install -r requirements.txt
   ```
2. Prepare the data:
   ```bash
   python data_preparation.py
   ```
   This generates:
   - `data/train.json`
   - `data/test.json`
   - `data/label_mapping.json`

3. Train a model (example with bert-base-uncased):
   ```bash
   python train.py \
     --model_save_path models/saved_model \
     --dataset_path data/train.json \
     --num_train_epoch 3
   ```

4. Run inference on the held-out test set:
   ```bash
   python pipeline.py \
     --model_load_path models/saved_model \
     --input_file data/test.json \
     --output_file outputs/predictions.json
   ```

Feel free to adjust hyperparameters or point the scripts at different output paths when experimenting.


