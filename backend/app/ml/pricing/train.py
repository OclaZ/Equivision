
import pandas as pd
import joblib
import json
import logging
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

from app.ml.pricing.preprocessing import PricingPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_pricing_model(data_path, output_dir):
    data_path = Path(data_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load & Preprocess
    logger.info("Loading and preprocessing data...")
    pp = PricingPreprocessor(str(data_path))
    df = pp.process()
    
    # Define features and target
    # We extract features from 'title' into 'breed' and 'gender'
    # We will use these + maybe 'location' (if clean enough) as input
    
    features = ['breed', 'gender'] # Simple start
    target = 'price_numeric'
    
    X = df[features]
    y = df[target]
    
    logger.info(f"Training on {len(df)} samples with features: {features}")
    
    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Create Pipeline
    # Categorical columns need encoding
    categorical_features = ['breed', 'gender']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    # Numerical columns (none for now, but good practice)
    # numerical_features = []
    # numerical_transformer = StandardScaler()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', categorical_transformer, categorical_features),
            # ('num', numerical_transformer, numerical_features)
        ])
    
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                               ('model', model)])
    
    # 4. Train
    logger.info("Fitting model...")
    pipeline.fit(X_train, y_train)
    
    # 5. Evaluate
    y_pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    
    logger.info(f"Model Evaluation:\nMAE: {mae:.2f}\nRMSE: {rmse:.2f}")
    
    # 6. Save Artifacts
    model_path = output_dir / "pricing_pipeline.joblib"
    joblib.dump(pipeline, model_path)
    logger.info(f"Model pipeline saved to {model_path}")

    # Save metrics
    metrics = {"mae": mae, "rmse": rmse}
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f)

if __name__ == "__main__":
    DATA_PATH = "d:/EquiVision/backend/data/raw/avito_horses.json"
    OUTPUT_DIR = "d:/EquiVision/backend/app/ml/pricing/weights"
    
    if Path(DATA_PATH).exists():
        train_pricing_model(DATA_PATH, OUTPUT_DIR)
    else:
        logger.error(f"Data file not found at {DATA_PATH}")
