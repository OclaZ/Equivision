# EquiVision Training Guide (For Friend's PC)

This guide explains how to set up the environment and train the new "God Tier" Horse Vision model from scratch on a new machine.

## Prerequisites

1.  **Python 3.10+** installed.
2.  **Git** installed.
3.  **CUDA (NVIDIA GPU)** recommended for training (but CPU works, just slower).

## Step 1: Clone & Setup

First, get the code and install dependencies.

```bash
# Clone the repository
git clone <YOUR_REPO_URL>
cd EquiVision

# Create a virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

## Step 2: Data Transfer (Crucial!)

The raw data and processed CSVs are **not in the repository** (they are gitignored). You need to place the following file manually:

1.  Get **`unified_horse_data.csv`** from the original developer.
2.  Place it in: `backend/data/processed/unified_horse_data.csv`
    _(You may need to create the folders `backend/data/processed/` if they don't exist)_.

## Step 3: Download & Clean Images

Run the following scripts to build the dataset from scratch using the CSV file.

**A. Download Images**
This script reads the CSV and downloads ~10,000 images into breed folders.

```bash
python backend/scripts/download_dataset_images.py
```

_Note: This may take 1-2 hours depending on internet speed._

**B. Process & Filter (YOLO)**
This script uses AI to crop horses and remove bad images.

```bash
python backend/scripts/process_scraped_images.py
```

_Output:_ Clean images will be in `backend/data/clean/horse-breeds-processed/`.

## Step 4: Train the Model

This script trains the new MobileNetV2 model on the cleaned dataset.

```bash
python backend/scripts/train_vision_scraped.py
```

### Outputs

After training, check `backend/app/ml/vision/weights_tf_scraped/` for:

- `horse_vision_scraped_final.h5` (The trained model)
- `class_indices.json` (The class mapping)

Send these two files back to the developer to integrate into the app!
