from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

def hello_world():
    logging.info("Hello World from EquiVision Airflow Setup!")
    return "Airflow is operational"

default_args = {
    'owner': 'equivision',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'equivision_test_dag',
    default_args=default_args,
    description='A simple test DAG to ensure Airflow is working',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['test', 'equivision'],
) as dag:

    hello_task = PythonOperator(
        task_id='hello_world_task',
        python_callable=hello_world,
    )

    hello_task
