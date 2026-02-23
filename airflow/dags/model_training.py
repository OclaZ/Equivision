"""
EquiVision — Model Training DAG (Placeholder)
===============================================
Schedule: Weekly (Monday 04:00 UTC)
Purpose:  Train vision + pricing models, log to MLflow, compare with production

This is a PLACEHOLDER DAG. The actual task implementations will be added
when we code the pipeline logic.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'equivision',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    dag_id='model_training_pipeline',
    default_args=default_args,
    description='Train ML models, log to MLflow, compare and register',
    schedule_interval='0 4 * * 1',  # Every Monday at 04:00 UTC
    start_date=datetime(2026, 2, 23),
    catchup=False,
    tags=['ml', 'training', 'equivision'],
) as dag:

    start = EmptyOperator(task_id='start')

    # TODO: Pull latest training data
    pull_data = EmptyOperator(task_id='pull_training_data')

    # TODO: Train vision model (EfficientNetV2B0)
    train_vision = EmptyOperator(task_id='train_vision_model')

    # TODO: Train pricing model (XGBoost)
    train_pricing = EmptyOperator(task_id='train_pricing_model')

    # TODO: Log metrics to MLflow
    log_metrics = EmptyOperator(task_id='log_metrics_to_mlflow')

    # TODO: Compare with current production model
    evaluate = EmptyOperator(task_id='evaluate_and_compare')

    # TODO: Register model if better
    register = EmptyOperator(task_id='register_model')

    end = EmptyOperator(task_id='end')

    start >> pull_data
    pull_data >> [train_vision, train_pricing]
    [train_vision, train_pricing] >> log_metrics >> evaluate >> register >> end
