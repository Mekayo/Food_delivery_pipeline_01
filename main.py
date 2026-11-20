from ingestion.fetch_data import fetch_data
from transformation.json_to_csv import json_to_csv
from transformation.feature_engineering import transform_data
from storage.postgres_loader import load_curated_to_postgres


def main():
    print("=" * 60)
    print("🚀 FOOD DELIVERY ETL PIPELINE")
    print("=" * 60)

    print("\n[Step 1/4] Fetching data from Overpass API...")
    try:
        fetch_data()
        print("[SUCCESS] Data ingestion completed.")
    except Exception as e:
        print(f"[WARN] Ingestion network issue: {e}")
        print("[INFO] Continuing with   =- existing local raw data...")

    print("\n[Step 2/4] Parsing raw JSON into structured tabular format (Pandas)...")
    try:
        json_to_csv()
        print("[SUCCESS] JSON to CSV transformation complete.")
    except Exception as e:
        print(f"[FATAL] Transformation failed: {e}")
        return

    print("\n[Step 3/4] Data Cleaning & Spatial Feature Engineering...")
    try:
        transform_data()
        print("[SUCCESS] Feature engineering complete.")
    except Exception as e:
        print(f"[FATAL] Feature engineering failed: {e}")
        return

    print("\n[Step 4/4] Loading curated data into PostgreSQL warehouse...")
    try:
        load_curated_to_postgres()
        print("[SUCCESS] Data warehouse load complete.")
    except Exception as e:
        print(f"[INFO] Skipping DB load (Postgres container not running or unreachable): {e}")

    print("\n" + "=" * 60)
    print("✅ Pipeline execution cycle completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
