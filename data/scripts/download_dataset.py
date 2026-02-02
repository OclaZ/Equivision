import os
import shutil
import zipfile
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

# Configuration
DATASET_NAME = "olgabelitskaya/horse-breeds"
TARGET_DIR = Path("data/raw")
ZIP_FILE = TARGET_DIR / "horse-breeds.zip"

def download_dataset():
    """Download horse breeds dataset from Kaggle."""
    api = KaggleApi()
    
    # Check if kaggle.json exists or environment variables are set
    if not os.environ.get("KAGGLE_USERNAME") and not (Path.home() / ".kaggle/kaggle.json").exists():
        print("Error: Kaggle API credentials not found.")
        print("Please place 'kaggle.json' in ~/.kaggle/ or set KAGGLE_USERNAME and KAGGLE_KEY env vars.")
        return

    print(f"Authenticating with Kaggle...")
    api.authenticate()

    print(f"Downloading {DATASET_NAME} to {TARGET_DIR}...")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        api.dataset_download_files(DATASET_NAME, path=TARGET_DIR, unzip=False)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download: {e}")
        return

    # Extract if zip exists (API download name might differ, checking directory)
    # The API usually downloads as {dataset-name}.zip or specifically named file
    # We'll look for any zip file in the target dir if expected one isn't there
    found_zip = list(TARGET_DIR.glob("*.zip"))
    if found_zip:
        zip_path = found_zip[0]
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TARGET_DIR)
        print("Extraction complete.")
        # Optional: Remove zip
        # os.remove(zip_path)
    else:
        print("No zip file found to extract.")

if __name__ == "__main__":
    download_dataset()
