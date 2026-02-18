
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
        self.img_size = (224, 224)  # Default, overridden by scraped model

        try:
            base_path = Path(__file__).resolve().parent
            weights_pth = base_path / "weights/best_model.pth"

            # --- Priority 1: New Scraped Model (best accuracy) ---
            scraped_dir = base_path / "weights_tf_scraped"
            scraped_model_candidates = [
                scraped_dir / "best.h5",
                scraped_dir / "horse_vision_final.h5",
            ]
            scraped_classes = scraped_dir / "class_indices.json"

            if tf and scraped_classes.exists():
                for model_path in scraped_model_candidates:
                    if model_path.exists():
                        try:
                            self.model = tf.keras.models.load_model(str(model_path))
                            self.model_type = 'tf'
                            self.img_size = (260, 260)  # Scraped model uses 260x260

                            with open(scraped_classes, 'r') as f:
                                idx_map = json.load(f)
                            # Sort by index to get correct order
                            self.class_names = [k for k, v in sorted(idx_map.items(), key=lambda x: x[1])]

                            logger.info(f"Scraped Vision Model loaded: {model_path.name} ({len(self.class_names)} classes)")
                            logger.info(f"Classes: {self.class_names}")
                            return  # Success
                        except Exception as e:
                            logger.error(f"Failed to load scraped model {model_path}: {e}")

            # --- Priority 2: Legacy TF Model ---
            tf_model_candidates = [
                base_path / "weights_tf/horse_vision_tf.h5",
                base_path / "weights_tf/horse_vision_tf_final.h5",
                base_path / "weights_tf/model.h5"
            ]
            weights_tf = None
            for p in tf_model_candidates:
                if p.exists():
                    weights_tf = p
                    break

            # Load legacy labels
            labels_path = None
            for p in [
                base_path / "../../../data/raw/horse-breeds/labels.json",
                base_path / "weights_tf/labels.json",
            ]:
                if p.exists():
                    labels_path = p
                    break

            if labels_path:
                with open(labels_path, 'r') as f:
                    label_map = json.load(f)
                    self.class_names = sorted(list(label_map.values()))
                    logger.info(f"Legacy labels: {len(self.class_names)} classes from {labels_path}")

            if tf and weights_tf:
                try:
                    self.model = tf.keras.models.load_model(str(weights_tf))
                    self.model_type = 'tf'
                    logger.info(f"Legacy TF Model loaded from {weights_tf}")
                    return
                except Exception as e:
                    logger.error(f"Failed to load legacy TF model: {e}")

            # --- Priority 3: PyTorch ---
            if torch and load_model and weights_pth.exists() and len(self.class_names) > 0:
                self.model = load_model(weights_pth, num_classes=len(self.class_names), device=self.device)
                self.transform = get_transforms(is_training=False)
                self.model_type = 'torch'
                logger.info(f"PyTorch Model loaded from {weights_pth}")
                return

            raise ImportError("No local models (.h5 or .pth) found or libraries missing.")

        except Exception as e:
            logger.warning(f"Local Breed Classifier failed ({e}). Using Remote mode.")
            self.use_remote = True

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
                    return {
                        "error": "No horse detected in the image.",
                        "breed": "Unknown",
                        "confidence": 0.0,
                        "detection": {"object_detected": None}
                    }

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
                # Preprocess for TF model (uses self.img_size)
                img_input = image.resize(self.img_size)
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

    def visualize_prediction(self, image_file):
        """
        Returns the image with bounding box and prediction label drawn.
        """
        import cv2
        import numpy as np
        
        # Load image for CV2
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # Reset file pointer for standard prediction
        image_file.seek(0)
        
        # Get Prediction
        result = self.predict(image_file)
        
        if "error" in result:
             # Draw "No Horse Found" on image
             cv2.putText(img, "NO HORSE DETECTED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            # Draw Bounding Box
            bbox = result["detection"]["bbox"]
            label = f"{result['breed']} ({result['confidence']*100:.1f}%)"
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw Rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw Label Background
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.rectangle(img, (x1, y1 - 30), (x1 + w, y1), (0, 255, 0), -1)
            
            # Draw Text
            cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # Convert back to bytes
        _, img_encoded = cv2.imencode('.jpg', img)
        return io.BytesIO(img_encoded.tobytes())

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
