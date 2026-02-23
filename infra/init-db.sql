-- ============================================================================
--  EquiVision — PostgreSQL Initialization Script
--  Creates additional databases needed by Airflow and MLflow
--  This runs automatically on first container boot via docker-entrypoint-initdb.d
-- ============================================================================

-- Create Airflow metadata database
SELECT 'CREATE DATABASE airflow_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_db')\gexec

-- Create MLflow tracking database
SELECT 'CREATE DATABASE mlflow_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mlflow_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO current_user;
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO current_user;
