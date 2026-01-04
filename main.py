from ingestion.fetch_data import fetch_data
from transformation.json_to_csv import json_to_csv
from transformation.feature_engineering import transform_data


def main():
    print("\nStep 1: Fetching data from Overpass API")
    print("-" * 50)

    # Ingestion step (resilient)
    try:
        fetch_data()
        print("[SUCCESS] Ingestion completed")
    except Exception as e:
        # Do NOT kill the pipeline if API fails
        print("[WARN] Ingestion failed, continuing with latest available raw data")
        print("Reason:", e)

    print("-" * 50)

    print("Step 2: Converting JSON to processed CSV data file")
    try:
        json_to_csv()
        print("[SUCCESS] JSON to CSV processing completed")
    except Exception as e:
        print("[FATAL] Processing failed. Pipeline stopped.")
        print("Reason:", e)
        return

    print("-" * 50)

    print("Step 3: Curating processed data (cleaning + feature engineering)")
    try:
        transform_data()
        print("[SUCCESS] Feature engineering completed")
    except Exception as e:
        print("[FATAL] Transformation failed. Pipeline stopped.")
        print("Reason:", e)
        return

    print("-" * 50)
    print("[SUCCESS] Pipeline completed successfully")


if __name__ == "__main__":
    main()
