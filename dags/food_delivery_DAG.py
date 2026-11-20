from airflow.sdk import dag, task
from pendulum import datetime
from datetime import timedelta

from ingestion import fetch_data
from transformation import json_to_csv
from transformation import feature_engineering
from storage import postgres_loader


@dag(
    dag_id="food_delivery_etl_pipeline",
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    default_args={
        "owner": "airflow",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    catchup=False,
    description="ETL pipeline for food delivery restaurant data with Pandas & PostgreSQL",
    tags=["food-delivery", "etl", "restaurant-data"],
)
def food_delivery_pipeline():

    @task
    def fetch_data_task():
        """Fetch restaurant location and metadata from Overpass API."""
        fetch_data.fetch_data()
        return "Data fetched successfully"

    @task
    def json_to_csv_task():
        """Parse raw JSON into clean tabular format using Pandas."""
        output_file = json_to_csv.json_to_csv()
        return str(output_file)

    @task
    def transform_data_task():
        """Clean dataset and calculate distance features."""
        df_featured = feature_engineering.transform_data()
        return f"Transformed {len(df_featured)} records"

    @task
    def load_to_postgres_task():
        """Load curated dataset into PostgreSQL warehouse."""
        rows_loaded = postgres_loader.load_curated_to_postgres()
        return f"Loaded {rows_loaded} rows to Postgres"

    # Define DAG task dependency chain
    (
        fetch_data_task()
        >> json_to_csv_task()
        >> transform_data_task()
        >> load_to_postgres_task()
    )


food_etl_dag = food_delivery_pipeline()

if __name__ == "__main__":
    food_etl_dag.test()
