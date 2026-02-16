
import json
import logging
import requests
import io
from pathlib import Path

# Optional import for local inference
try:
    import torch
    from PIL import Image
    from app.ml.vision.model import load_model, HorseBreedClassifier
    from app.ml.vision.dataset import get_transforms
except ImportError:
    # Handle the Windows NumPy DLL issue gracefully
    torch = None
    Image = None
    load_model = None
    get_transforms = None
    logging.getLogger(__name__).warning("Torch/NumPy failed to load. Running in proxy mode.")

logger = logging.getLogger(__name__)

class BreedClassifierService:
    def __init__(self):
        if torch:
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self.use_remote = False
        else:
            self.device = None
            self.use_remote = True # Force remote mode if torch is missing
            
        self.model = None
        self.class_names = []
        self.remote_url = "http://localhost:8001/predict/breed" # Docker container URL
        self._load_resources()

    def _load_resources(self):

        try:
            # 1. Try to load local resources first
            base_path = Path(__file__).resolve().parent
            weights_path = base_path / "weights/best_model.pth"
            
            # Flexible path for labels
            possible_paths = [
                Path("d:/EquiVision/backend/data/raw/horse-breeds/labels.json"), # Windows absolute
                base_path.parents[3] / "data/raw/horse-breeds/labels.json",      # Docker relative (4 levels up?)
                base_path.parents[2] / "data/raw/horse-breeds/labels.json",      # Docker relative (3 levels up)
                Path("data/raw/horse-breeds/labels.json"),                       # CWD relative
                Path("/app/data/raw/horse-breeds/labels.json")                   # Docker absolute
            ]
            
            labels_path = None
            for p in possible_paths:
                if p.exists():
                    labels_path = p
                    break
            
            if labels_path:
                 with open(labels_path, 'r') as f:
                    label_map = json.load(f)
                    self.class_names = sorted(list(label_map.values()))
                    logger.info(f"Loaded {len(self.class_names)} classes from {labels_path}")
            else:
                logger.warning("Labels file not found in any standard location")

            # 2. Try loading the model itself
            if load_model and weights_path.exists() and len(self.class_names) > 0:
                self.model = load_model(weights_path, num_classes=len(self.class_names), device=self.device)
                self.transform = get_transforms(is_training=False)
                logger.info("Horse Breed Classifier loaded locally.")
            else:
                raise ImportError("Local model loading not available or failed (missing weights/labels/module)")

        except Exception as e:
            logger.warning(f"Local Breed Classifier failed ({e}).Switching to Remote/Docker mode.")
            self.use_remote = True
            # In remote mode, we just need to forward the request

    def predict(self, image_file):
        """
        Predict breed from an image file (bytes or path).
        """
        if self.use_remote:
            return self._predict_remote(image_file)

        if not self.model:
             # If valid model isn't loaded AND remote isn't set (should be catched above), try remote as last resort
             return self._predict_remote(image_file)

        try:
            # Local Inference
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
            logger.error(f"Local Prediction failed: {e}. Trying remote fallback...")
            return self._predict_remote(image_file)

    def _predict_remote(self, image_file):
        """Forward prediction request to Docker container running on port 8001"""
        try:
            # Reset file pointer if it's a file-like object
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
                files = {'file': ('image.jpg', image_file, 'image/jpeg')}
            else:
                # It might be bytes or path
                files = {'file': open(image_file, 'rb')}

            response = requests.post(self.remote_url, files=files, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Remote service returned {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Remote Prediction failed: {e}")
            raise RuntimeError("Breed Classification unavailable (Local & Remote failed). Ensure Docker is running.")
