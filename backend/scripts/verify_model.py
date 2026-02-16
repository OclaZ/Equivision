import sys
import os
from pathlib import Path

# Add backend to python path
sys.path.append(os.path.join(os.getcwd()))

import torch
from PIL import Image
import random

try:
    from app.ml.vision.inference import BreedClassifierService
except ImportError as e:
    print(f"Error importing BreedClassifierService: {e}")
    sys.exit(1)

def main():
    print("="*60)
    print("      EquiVision Model Verification Tool")
    print("="*60)

    # 1. Check for Model Weights
    weights_path = Path("app/ml/vision/weights/best_model.pth")
    if not weights_path.exists():
        print(f"❌ Custom weights not found at: {weights_path}")
        print("   Please copy 'best_model.pth' from your friend's PC to this location.")
        return
    else:
        print(f"✅ Found weights file: {weights_path} ({weights_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # 2. Check for Labels
    labels_path = Path("data/raw/horse-breeds/labels.json")
    if not labels_path.exists():
        print(f"❌ Labels file not found at: {labels_path}")
        return
    else:
        print(f"✅ Found labels file: {labels_path}")

    # 3. Initialize Service
    print("\nInitializing BreedClassifierService...")
    try:
        service = BreedClassifierService()
        if service.use_remote:
            print("⚠️  Service initialized in REMOTE mode (Docker).")
            print("   This likely means Torch failed to load or weights were invalid.")
        else:
            print("✅ Service initialized in LOCAL mode (CPU).")
            print(f"   Classes loaded: {len(service.class_names)}")
            print(f"   Classes: {', '.join(service.class_names)}")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return

    # 4. Run Prediction on a few random images
    print("\nRunning Test Predictions...")
    data_dir = Path("data/raw/horse-breeds")
    
    # Get one image from each of the new breeds
    test_breeds = {
        "08": "Barb",
        "09": "Andalusian",
        "10": "Hanoverian",
        "11": "Lusitano"
    }

    for breed_id, breed_name in test_breeds.items():
        images = list(data_dir.glob(f"{breed_id}_*.jpg"))
        if not images:
            print(f"   ⚠️  No images found for {breed_name}")
            continue
            
        test_img = random.choice(images)
        print(f"\n   Testing {breed_name} Image: {test_img.name}")
        
        try:
            result = service.predict(test_img)
            pred_breed = result['breed']
            conf = result['confidence']
            
            icon = "✅" if pred_breed == breed_name else "⚠️ "
            print(f"   {icon} Prediction: {pred_breed} ({conf:.1%})")
            
            # Show top 3
            probs = result.get('all_probabilities', {})
            top3 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"      Top 3: {', '.join([f'{k}: {v:.1%}' for k,v in top3])}")
            
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}")

    print("\n" + "="*60)
    print("Verification Complete!")

if __name__ == "__main__":
    main()
