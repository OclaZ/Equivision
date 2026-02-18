
import pandas as pd
import joblib
import json
import logging
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
DATA_PATH = Path("data/processed/unified_horse_data.csv")
OUTPUT_DIR = Path("app/ml/pricing/weights")

def train_pricing_model():
    if not DATA_PATH.exists():
        logger.error(f"Processed data not found at {DATA_PATH}. Run unify_data.py first.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    logger.info(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # 2. Feature Definition
    # Target
    target = 'price'
    
    # Features
    categorical_features = ['breed', 'gender']
    numerical_features = ['age', 'height']
    
    X = df[categorical_features + numerical_features]
    y = df[target]
    
    logger.info(f"Training on {len(df)} samples.")
    logger.info(f"Categorical: {categorical_features}")
    logger.info(f"Numerical: {numerical_features}")
    
    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Preprocessing Pipelines
    # Categorical: Impute 'Unknown' -> OneHot
    cat_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Numerical: Impute Mean -> Scale
    num_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')), # Use median to be robust to outliers
        ('scaler', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', cat_pipeline, categorical_features),
            ('num', num_pipeline, numerical_features)
        ])
    
    # 5. Model (XGBoost)
    model = XGBRegressor(
        n_estimators=200, 
        learning_rate=0.05, 
        max_depth=6, 
        random_state=42,
        n_jobs=-1
    )
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                               ('model', model)])
    
    # 6. Train
    logger.info("Fitting model...")
    pipeline.fit(X_train, y_train)
    
    # 7. Evaluate
    y_pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Model Evaluation:\nMAE: {mae:,.2f} MAD\nRMSE: {rmse:,.2f} MAD\nR2: {r2:.3f}")
    
    # 8. Save Artifacts
    model_path = OUTPUT_DIR / "pricing_pipeline.joblib"
    joblib.dump(pipeline, model_path)
    logger.info(f"Model pipeline saved to {model_path}")

    # Save metrics
    metrics = {"mae": mae, "rmse": rmse, "r2": r2, "samples": len(df)}
    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f)

if __name__ == "__main__":
    train_pricing_model()
