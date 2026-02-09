
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.model_info = None
        self._load_model()

    def _load_model(self):
        try:
            model_info_path = Path(__file__).resolve().parent / "weights/model_info.json"
            
            if not model_info_path.exists():
                logger.error(f"Model info not found at {model_info_path}")
                raise FileNotFoundError("Pricing model not initialized")
            
            with open(model_info_path, 'r') as f:
                self.model_info = json.load(f)
            
            logger.info("Pricing model loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load Pricing model: {e}")
            raise

    def predict(self, breed: str = None, gender: str = None, age: int = None) -> Dict[str, Any]:
        """
        Predict horse price based on features.
        Currently uses rule-based approach with statistics.
        
        Args:
            breed: Horse breed (optional)
            gender: Horse gender (optional)
            age: Horse age in years (optional)
        
        Returns:
            Dictionary with price estimate and confidence interval
        """
        if not self.model_info:
            raise RuntimeError("Model not initialized")

        try:
            stats = self.model_info['statistics']
            
            # Simple rule-based pricing
            # Base price is the average
            base_price = stats['average']
            
            # Adjust based on breed (simplified)
            breed_multipliers = {
                'arabe': 1.3,
                'barbe': 1.1,
                'anglo': 1.4,
                'espagnol': 1.2,
                'frison': 1.5,
                'poney': 0.7,
                'shetland': 0.6,
            }
            
            multiplier = 1.0
            if breed and breed.lower() in breed_multipliers:
                multiplier = breed_multipliers[breed.lower()]
            
            estimated_price = base_price * multiplier
            
            # Calculate confidence interval (±30% for now)
            confidence_range = estimated_price * 0.3
            
            return {
                "estimated_price": round(estimated_price, 2),
                "currency": "DH",
                "confidence_interval": {
                    "min": round(estimated_price - confidence_range, 2),
                    "max": round(estimated_price + confidence_range, 2)
                },
                "model_type": self.model_info.get('type', 'unknown'),
                "factors_considered": {
                    "breed": breed or "not_specified",
                    "gender": gender or "not_specified",
                    "age": age or "not_specified"
                },
                "note": "Estimate based on market data from Avito.ma"
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
