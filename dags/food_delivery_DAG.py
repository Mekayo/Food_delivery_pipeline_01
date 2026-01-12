from datetime import datetime, timedelta

from airflow import DAG

# Support both Airflow 2.x (preferred) and older python_operator fallback.
# type: ignore used to silence linter when Airflow stubs are missing locally.
try:
    from airflow.operators.python import PythonOperator  # type: ignore
except ImportError:  # pragma: no cover
    from airflow.operators.python_operator import PythonOperator  # type: ignore

from ingestion import fetch_data
from transformation import json_to_csv
from transformation import feature_engineering


POSTGRES_Conn_ID="postgres_default"

# DAGs

with DAG(
    dag_id='food_delivery_etl_pipeline',
    default_args={
        'owner': 'airflow',
        'start_date': datetime(2024, 1, 1),
        'retries': 1,
        'retry_delay': timedelta(minutes=5)
    },
    schedule_interval='@daily',
    catchup=False,
    description='ETL pipeline for food delivery restaurant data',
    tags=['food-delivery', 'etl', 'restaurant-data']
) as dag:
    
    # Task 1: Fetch data from Overpass API
    fetch_task = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_data.fetch_data,
        dag=dag
    )
    
    # Task 2: Convert JSON to CSV
    json_to_csv_task = PythonOperator(
        task_id='json_to_csv',
        python_callable=json_to_csv.json_to_csv,
        dag=dag
    )
    
    # Task 3: Transform data (clean and feature engineering)
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=feature_engineering.transform_data,
        dag=dag
    )
    
    # Define task dependencies
    fetch_task >> json_to_csv_task >> transform_task
