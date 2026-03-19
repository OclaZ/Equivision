
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        try:
            # Load the trained XGBoost Pipeline
            weights_dir = Path(__file__).resolve().parent / "weights"
            model_path = weights_dir / "pricing_pipeline.joblib"
            
            if not model_path.exists():
                logger.warning(f"ML Pipeline not found at {model_path}. creating dummy pipeline for dev.")
                # In production, we should maybe raise error or download from S3
                # For now, we will raise error to force training
                # raise FileNotFoundError("Pricing model not initialized. Run train.py first.")
                return

            self.pipeline = joblib.load(model_path)
            logger.info(f"XGBoost Pricing Model loaded from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load Pricing model: {e}")
            self.pipeline = None

    def predict(self, breed: Optional[str] = None, gender: Optional[str] = None, 
                age: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
        """
        Predict horse price using XGBoost ML pipeline.
        
        Args:
            breed: Horse breed (e.g. 'Arabian')
            gender: 'Mare', 'Stallion', 'Gelding'
            age: Age in years
            height: Height in cm
        """
        if not self.pipeline:
            # Fallback to simple logic if model not trained yet
            return {
                "estimated_price": 0,
                "note": "Model not trained yet. Contact admin."
            }

        try:
            # Create DataFrame from inputs (Pipeline expects specific columns)
            # Add fake name, source, and price to allow engineer_features to work
            input_df = pd.DataFrame([{
                'name': "Unknown",
                'source': "API",
                'price': 10000,  # Fake price to generate synthetic features
                'breed': breed if breed else "Unknown",
                'gender': gender if gender else "Unknown",
                'age': age if age is not None else np.nan, # Imputer will handle NaN
                'height': height if height is not None else np.nan
            }])
            
            # Apply feature engineering to create the required 27 columns natively
            try:
                from .pipeline import engineer_features
                input_df, _ = engineer_features(input_df, is_training=False, breed_premium_map={})
            except ImportError as e:
                logger.error(f"Failed to import feature engineering pipeline: {e}")
                # Fallback if import fails just let it crash down below to explain missing cols
            
            # Predict (V3 Pipeline predicts log1p of price in EUR/MAD)
            predicted_log = self.pipeline.predict(input_df)[0]
            predicted_price = np.expm1(float(predicted_log))
            predicted_price = max(0, float(predicted_price)) # No negative prices
            
            # Confidence Interval logic (Simplified, since XGBoost doesn't give std natively easily)
            # We can use the MAE from training as a rough interval
            # Or just +/- 20%
            confidence_range = predicted_price * 0.2
            
            return {
                "estimated_price": round(predicted_price, 0),
                "currency": "MAD",
                "confidence_interval": {
                    "min": round(max(0, predicted_price - confidence_range), 0),
                    "max": round(predicted_price + confidence_range, 0)
                },
                "ml_model_version": "v2.0 (XGBoost)",
                "inputs": {
                    "breed": breed,
                    "gender": gender,
                    "age": age,
                    "height": height
                }
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
