from ingestion.fetch_data import fetch_data
from transformation.json_to_csv import json_to_csv
from transformation.feature_engin import transform_data


def main():
    print("Fetching data from Overpass API")
    print("-"*50)

    fetch_data()
    print("-"*50)    
    print("Step 2: Converting JSON to processed CSV data file")
    json_to_csv() 
    print("-"*50)
    print("Step 3: Curating processed data (cleaning and feature engineering)")
    transform_data()
    print("-"*50)
    
    print("Pipeline completed successfully")


if __name__ == "__main__":
    main()

