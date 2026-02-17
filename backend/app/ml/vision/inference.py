
import json
import logging
import requests
import io
from pathlib import Path

# Optional imports for local inference
try:
    from PIL import Image
    import numpy as np
    
    # Try Torch
    try:
        import torch
        from app.ml.vision.model import load_model
        from app.ml.vision.dataset import get_transforms
    except ImportError:
        torch = None
        load_model = None
        get_transforms = None

    # Try TensorFlow
    try:
        import tensorflow as tf
    except ImportError:
        tf = None

    # Try YOLO (Ultralytics)
    try:
        from ultralytics import YOLO
    except ImportError:
        YOLO = None

except ImportError:
    Image = None
    torch = None
    tf = None
    logging.getLogger(__name__).warning("ML libraries failed to load. Running in proxy mode.")

logger = logging.getLogger(__name__)

class BreedClassifierService:
    def __init__(self):
        self.device = None
        self.use_remote = False
        self.model_type = None # 'torch' or 'tf'
        
        if torch:
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        elif tf:
            # TF handles devices differently, we just check if it's available
            pass
        else:
            self.use_remote = True
            
        self.model = None
        self.yolo_model = None
        self.class_names = []
        self.remote_url = "http://localhost:8001/predict/breed"
        
        if YOLO:
            try:
                # Use the nano model for speed in production
                self.yolo_model = YOLO('yolov8n.pt')
                logger.info("YOLOv8 Detection model loaded.")
            except Exception as e:
                logger.error(f"Failed to load YOLO: {e}")

        self._load_resources()

    def _load_resources(self):

        try:
            # 1. Paths
            base_path = Path(__file__).resolve().parent
            weights_pth = base_path / "weights/best_model.pth"
            weights_tf = base_path / "weights_tf/horse_vision_tf.h5"
            
            # Find labels
            labels_path = None
            possible_paths = [
                Path("data/clean/horse-breeds/labels.json"),
                Path("data/raw/horse-breeds/labels.json"),
                base_path / "../../../data/clean/horse-breeds/labels.json",
                base_path / "weights_tf/labels.json",
                Path("d:/EquiVision/backend/data/raw/horse-breeds/labels.json")
            ]
            
            for p in possible_paths:
                if p.exists():
                    labels_path = p
                    break
            
            if labels_path:
                 with open(labels_path, 'r') as f:
                    label_map = json.load(f)
                    # For TF, labels are usually sorted folders
                    self.class_names = sorted(list(label_map.values()))
                    logger.info(f"Loaded {len(self.class_names)} classes from {labels_path}")

            # 2. Try loading TensorFlow model first (since it's the new request)
            if tf and weights_tf.exists():
                self.model = tf.keras.models.load_model(str(weights_tf))
                self.model_type = 'tf'
                logger.info(f"TensorFlow Model loaded from {weights_tf}")
                return # Success

            # 3. Fallback to PyTorch
            if torch and load_model and weights_pth.exists() and len(self.class_names) > 0:
                self.model = load_model(weights_pth, num_classes=len(self.class_names), device=self.device)
                self.transform = get_transforms(is_training=False)
                self.model_type = 'torch'
                logger.info(f"PyTorch Model loaded from {weights_pth}")
                return # Success

            raise ImportError("No local models (.h5 or .pth) found or libraries missing.")

        except Exception as e:
            logger.warning(f"Local Breed Classifier failed to start ({e}). Using Remote mode.")
            self.use_remote = True

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
            full_image = Image.open(image_file).convert("RGB")
            image = full_image # Default to full image if YOLO fails/misses
            detection_info = None

            # 1. Stage 1: Object Detection (YOLO)
            if self.yolo_model:
                results = self.yolo_model(full_image, verbose=False)
                best_box = None
                max_area = 0
                
                for r in results:
                    for box in r.boxes:
                        if int(box.cls) == 17: # 'horse' class
                            coords = box.xyxy[0].tolist()
                            area = (coords[2] - coords[0]) * (coords[3] - coords[1])
                            if area > max_area:
                                max_area = area
                                best_box = coords
                
                if best_box:
                    # Crop to horse with a small margin
                    x1, y1, x2, y2 = best_box
                    mw, mh = (x2-x1)*0.05, (y2-y1)*0.05 # 5% margin
                    image = full_image.crop((
                        max(0, x1-mw), max(0, y1-mh), 
                        min(full_image.width, x2+mw), min(full_image.height, y2+mh)
                    ))
                    detection_info = {
                        "object_detected": "horse",
                        "bbox": [round(c, 2) for c in best_box],
                        "cropped": True
                    }
                else:
                    logger.warning("No horse detected by YOLO. Proceeding with full image.")
                    detection_info = {"object_detected": None, "cropped": False}

            # 2. Stage 2: Breed Classification
            if self.model_type == 'torch':
                input_tensor = self.transform(image).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    outputs = self.model(input_tensor)
                    probabilities = torch.nn.functional.softmax(outputs, dim=1)
                    confidence, predicted_idx = torch.max(probabilities, 1)
                    confidence_score = confidence.item()
                    predicted_class = self.class_names[predicted_idx.item()]
                    all_probs = probabilities[0].tolist()

            elif self.model_type == 'tf':
                # Preprocess for MobileNetV2
                img_input = image.resize((224, 224))
                img_array = np.array(img_input).astype(np.float32)
                img_array = np.expand_dims(img_array, axis=0)
                
                predictions = self.model.predict(img_array, verbose=0)
                predicted_idx = np.argmax(predictions[0])
                confidence_score = float(predictions[0][predicted_idx])
                predicted_class = self.class_names[predicted_idx]
                all_probs = predictions[0].tolist()
            
            else:
                return self._predict_remote(image_file)

            result = {
                "breed": predicted_class,
                "confidence": float(f"{confidence_score:.4f}"),
                "detection": detection_info,
                "all_probabilities": {
                    cls: float(f"{prob:.4f}") 
                    for cls, prob in zip(self.class_names, all_probs)
                }
            }
            return result
            
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
