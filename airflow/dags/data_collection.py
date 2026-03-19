"""
EquiVision — Data Collection Pipeline DAG
==========================================
Schedule: Daily at 02:00 UTC
Purpose:  Scrape horse listings from PostgreSQL Data source,
          clean data, validate, and store in the main DB.

This DAG uses BashOperator to run the scraping/seeding scripts.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
import logging
import sys
import os

logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, "/opt/airflow/backend")
sys.path.insert(0, "/")

default_args = {
    'owner': 'equivision',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def validate_data(**context):
    """Validate the data in the database after seeding."""
    import psycopg2

    db_url = os.environ.get(
        "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", ""
    )
    # Connect to the main equivision_db, not airflow_db
    pg_user = os.environ.get("POSTGRES_USER", "oclaz")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "112001")

    conn = psycopg2.connect(
        host="database",
        port=5432,
        dbname="equivision_db",
        user=pg_user,
        password=pg_pass,
    )
    cur = conn.cursor()

    # Count horse listings
    cur.execute("SELECT COUNT(*) FROM horse_listings")
    count = cur.fetchone()[0]
    logger.info(f"Total horse listings in DB: {count}")

    # Count users
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    logger.info(f"Total users in DB: {user_count}")

    cur.close()
    conn.close()

    if count == 0:
        raise ValueError("No horse listings found in database! Data collection may have failed.")

    return {"listing_count": count, "user_count": user_count}


def check_data_freshness(**context):
    """Check the freshness of the data in the database."""
    import psycopg2

    pg_user = os.environ.get("POSTGRES_USER", "oclaz")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "112001")

    conn = psycopg2.connect(
        host="database",
        port=5432,
        dbname="equivision_db",
        user=pg_user,
        password=pg_pass,
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(scraped_at) as latest,
               COUNT(*) as total,
               COUNT(CASE WHEN is_active THEN 1 END) as active
        FROM horse_listings
    """)
    row = cur.fetchone()
    logger.info(f"Latest scrape: {row[0]}, Total: {row[1]}, Active: {row[2]}")

    cur.close()
    conn.close()

    return {"latest_scrape": str(row[0]), "total": row[1], "active": row[2]}


with DAG(
    dag_id='data_collection_pipeline',
    default_args=default_args,
    description='Collect, validate, and store horse listings data',
    schedule_interval='0 2 * * *',  # Daily at 02:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['data', 'scraping', 'equivision'],
) as dag:

    start = EmptyOperator(task_id='start')

    # Seed/refresh data from the backend seed script
    seed_data = BashOperator(
        task_id='seed_database',
        bash_command='cd /opt/airflow/backend && python seed.py',
        env={
            "DATABASE_URL": f"postgresql://{os.environ.get('POSTGRES_USER', 'oclaz')}:{os.environ.get('POSTGRES_PASSWORD', '112001')}@database:5432/equivision_db",
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        },
    )

    validate = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
    )

    freshness_check = PythonOperator(
        task_id='check_data_freshness',
        python_callable=check_data_freshness,
    )

    end = EmptyOperator(task_id='end')

    start >> seed_data >> validate >> freshness_check >> end
