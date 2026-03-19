"""
EquiVision — Model Training Pipeline DAG
==========================================
Schedule: Weekly (Sunday at 04:00 UTC)
Purpose:  Train ML pricing model, evaluate, and save to weights directory.

This DAG executes the full pricing pipeline (pipeline.py) which:
  1. Loads horse data from CSV
  2. Engineers 27+ features (synthetic, domain, interaction)
  3. Trains XGBoost, LightGBM, Ridge, SVR, RandomForest + Stacking
  4. Saves the best pipeline to /ML_DL/ML/MODELS/weights/pricing_pipeline.joblib
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
import logging
import sys
import os
import json

logger = logging.getLogger(__name__)

sys.path.insert(0, "/")
sys.path.insert(0, "/opt/airflow/backend")

default_args = {
    'owner': 'equivision_ai',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=10),
}


def check_training_data(**context):
    """Check that training data files exist before proceeding."""
    data_paths = [
        "/opt/airflow/backend/data/processed/unified_horse_data.csv",
        "/ML_DL/data/horses_data.csv",
    ]
    found = None
    for p in data_paths:
        if os.path.exists(p):
            found = p
            break

    if not found:
        raise FileNotFoundError(
            f"Training data not found in any of: {data_paths}. "
            "Please ensure horse data CSV is available."
        )

    import pandas as pd
    df = pd.read_csv(found)
    logger.info(f"Training data found at {found}: {len(df)} rows, {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    
    context['ti'].xcom_push(key='data_path', value=found)
    context['ti'].xcom_push(key='row_count', value=len(df))
    return {"path": found, "rows": len(df)}


def evaluate_model(**context):
    """Read the model comparison JSON and log results."""
    metrics_path = "/ML_DL/ML/MODELS/weights/model_comparison.json"
    
    if not os.path.exists(metrics_path):
        logger.warning("No model_comparison.json found. Training may not have produced metrics.")
        return {"status": "no_metrics"}

    with open(metrics_path, "r") as f:
        metrics = json.load(f)

    logger.info(f"=== Model Training Results (v{metrics.get('version', '?')}) ===")
    logger.info(f"Winner: {metrics['winner']}")
    logger.info(f"R² Score: {metrics['winner_r2']}")
    logger.info(f"MAE: {metrics['winner_mae']}")
    logger.info(f"MAPE: {metrics['winner_mape']}%")
    
    if 'all_models' in metrics:
        for m in metrics['all_models']:
            logger.info(f"  {m['model']}: R²={m['test_r2']}, MAE={m['test_mae']}")

    # Push metrics to XCom for downstream tasks
    context['ti'].xcom_push(key='winner', value=metrics['winner'])
    context['ti'].xcom_push(key='r2_score', value=metrics['winner_r2'])
    context['ti'].xcom_push(key='mae', value=metrics['winner_mae'])
    
    return metrics


def verify_model_artifact(**context):
    """Verify the saved model artifact exists and is valid."""
    import joblib

    model_path = "/ML_DL/ML/MODELS/weights/pricing_pipeline.joblib"
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}")

    # Try loading it
    pipeline = joblib.load(model_path)
    logger.info(f"Model artifact verified: {model_path}")
    logger.info(f"Pipeline type: {type(pipeline)}")
    
    file_size = os.path.getsize(model_path) / (1024 * 1024)
    logger.info(f"Model file size: {file_size:.2f} MB")

    return {"model_path": model_path, "size_mb": round(file_size, 2)}


with DAG(
    dag_id='model_training_pipeline',
    default_args=default_args,
    description='Train XGBoost pricing model, evaluate, and register',
    schedule_interval='0 4 * * 0',  # Every Sunday 04:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['ml', 'training', 'equivision'],
) as dag:

    start = EmptyOperator(task_id='start')

    # Step 1: Validate training data exists
    check_data = PythonOperator(
        task_id='check_training_data',
        python_callable=check_training_data,
    )

    # Step 2: Run the full pricing pipeline training script
    train_pricing = BashOperator(
        task_id='train_pricing_model',
        bash_command='cd /ML_DL && python -m ML.MODELS.pipeline',
        execution_timeout=timedelta(hours=1),
    )

    # Step 3: Evaluate results from model_comparison.json
    evaluate = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
    )

    # Step 4: Verify model artifact saved successfully
    verify = PythonOperator(
        task_id='verify_model_artifact',
        python_callable=verify_model_artifact,
    )

    end = EmptyOperator(task_id='end')

    start >> check_data >> train_pricing >> evaluate >> verify >> end
