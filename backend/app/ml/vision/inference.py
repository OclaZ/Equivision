
import torch
from pathlib import Path
from PIL import Image
import json
import logging

from app.ml.vision.model import load_model, HorseBreedClassifier
from app.ml.vision.dataset import get_transforms

logger = logging.getLogger(__name__)

class BreedClassifierService:
    def __init__(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.class_names = []
        self._load_resources()

    def _load_resources(self):
        try:
            # Paths
            # Assuming this service is initialized from backend root
            base_path = Path(__file__).resolve().parent
            weights_path = base_path / "weights/best_model.pth"
            labels_path = Path("d:/EquiVision/backend/data/raw/horse-breeds/labels.json")
            
            # Load Class Names
            if not labels_path.exists():
                logger.error(f"Labels file not found at {labels_path}")
                raise FileNotFoundError("Labels file missing")
            
            with open(labels_path, 'r') as f:
                label_map = json.load(f)
                # Sort exactly as in dataset.py to match indices
                self.class_names = sorted(list(label_map.values()))
            
            # Load Model
            if not weights_path.exists():
                logger.error(f"Model weights not found at {weights_path}")
                raise FileNotFoundError("Model weights missing")

            self.model = load_model(weights_path, num_classes=len(self.class_names), device=self.device)
            self.transform = get_transforms(is_training=False)
            
            logger.info("Horse Breed Classifier loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load Breed Classifier: {e}")
            raise

    def predict(self, image_file):
        """
        Predict breed from an image file (bytes or path).
        """
        if not self.model:
            raise RuntimeError("Model not initialized")

        try:
            image = Image.open(image_file).convert("RGB")
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted_idx = torch.max(probabilities, 1)
            
            predicted_class = self.class_names[predicted_idx.item()]
            confidence_score = confidence.item()
            
            return {
                "breed": predicted_class,
                "confidence": float(f"{confidence_score:.4f}"),
                "all_probabilities": {
                    cls: float(f"{prob:.4f}") 
                    for cls, prob in zip(self.class_names, probabilities[0].tolist())
                }
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
