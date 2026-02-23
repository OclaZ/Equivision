"""
EquiVision — Data Collection DAG (Placeholder)
================================================
Schedule: Daily at 02:00 UTC
Purpose:  Scrape horse listings from Avito.ma, clean data, store in PostgreSQL

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
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='data_collection_pipeline',
    default_args=default_args,
    description='Scrape horse listings from Avito.ma and store in DB',
    schedule_interval='0 2 * * *',  # Daily at 02:00 UTC
    start_date=datetime(2026, 2, 23),
    catchup=False,
    tags=['data', 'scraping', 'equivision'],
) as dag:

    start = EmptyOperator(task_id='start')

    # TODO: Implement actual scraping logic
    scrape_listings = EmptyOperator(task_id='scrape_avito_listings')

    # TODO: Implement data cleaning
    clean_data = EmptyOperator(task_id='clean_and_validate')

    # TODO: Implement DB storage
    store_data = EmptyOperator(task_id='store_in_postgres')

    end = EmptyOperator(task_id='end')

    start >> scrape_listings >> clean_data >> store_data >> end
