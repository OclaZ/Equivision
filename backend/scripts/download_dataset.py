
import os
import sys
import zipfile
import subprocess
from pathlib import Path

def download_and_setup_dataset():
    # Define paths
    dataset_name = "olgabelitskaya/horse-breeds"
    target_dir = Path("d:/EquiVision/backend/data/raw/horse-breeds")
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading dataset {dataset_name}...")
    try:
        # Using kaggle CLI instead of API to avoid boilerplate credential handling if env vars are set
        # User needs to have kaggle installed and credentials set up.
        # Using absolute path to kaggle executable in venv
        kaggle_exe = Path("d:/EquiVision/backend/venv/Scripts/kaggle.exe")
        subprocess.run([str(kaggle_exe), "datasets", "download", "-d", dataset_name, "-p", str(target_dir)], check=True)
        
        # Unzip
        print("Unzipping dataset...")
        zip_path = target_dir / "horse-breeds.zip"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
            
        # Clean up zip
        os.remove(zip_path)
        print(f"Dataset ready at {target_dir}")
        
    except FileNotFoundError:
        print("Error: 'kaggle' command not found. Please pip install kaggle and setup kaggle.json")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading dataset: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    download_and_setup_dataset()
