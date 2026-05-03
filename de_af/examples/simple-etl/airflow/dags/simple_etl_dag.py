"""Simple ETL DAG: CSV → Staging → Marts with data quality validation."""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'de-af',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'simple_etl_pipeline',
    default_args=default_args,
    description='CSV to Parquet ETL with dbt and Great Expectations',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['analytics', 'users', 'etl'],
)

extract_csv = BashOperator(
    task_id='extract_csv',
    bash_command='python scripts/extract_users.py',
    dag=dag,
)

dbt_staging = BashOperator(
    task_id='dbt_run_staging',
    bash_command='dbt run --select staging.stg_users',
    dag=dag,
)

dbt_marts = BashOperator(
    task_id='dbt_run_marts',
    bash_command='dbt run --select marts.dim_users',
    dag=dag,
)

dbt_tests = BashOperator(
    task_id='dbt_test',
    bash_command='dbt test',
    dag=dag,
)

great_expectations_validate = BashOperator(
    task_id='validate_great_expectations',
    bash_command='great_expectations checkpoint run users_checkpoint',
    dag=dag,
)

# Pipeline dependencies
extract_csv >> dbt_staging >> dbt_marts >> dbt_tests >> great_expectations_validate
