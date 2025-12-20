import pandas as pd
import numpy as np
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURATED_DIR = Path(__file__).parent.parent / "data" / "curated"

#----------------city center coordinates----------------
CITY_CENTER_LAT = 30.7333
CITY_CENTER_LON = 76.7794


def get_latest_processed_file():
    """Get the latest processed CSV file from the processed directory."""
    processed_files = list(PROCESSED_DIR.glob("*.csv"))
    if not processed_files:
        raise FileNotFoundError("No processed CSV files found")
    return max(processed_files, key=lambda f: f.stat().st_mtime)


def clean_data(df):
    """
    Clean the dataframe by:
    - Dropping nulls in name, lat, lon
    - Filling null cuisine with "unknown" and normalizing
    - Dropping duplicate rows
    - Filling null place with "unknown"
    """
    # drop nulls in name, lat, lon
    df = df.dropna(subset=["name", "lat", "lon"])
    
    # fill null cuisine with "unknown"
    df["cuisine"] = df["cuisine"].fillna("unknown")
    
    # lower the letter to avoid any explosion
    df["cuisine"] = df["cuisine"].str.lower().str.strip()
    
    # droping duplicate rows have same restaurant and same places
    df = df.drop_duplicates(subset=["name", "lat", "lon"])
    
    # fill null place with "unknown"
    df["place"] = df["place"].fillna("unknown")
    
    return df


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def feature_engineering(df):
    """
    Apply feature engineering steps:
    - Add customer coordinates
    - Calculate distance from restaurant to customer
    """
    df["customer_lat"] = CITY_CENTER_LAT
    df["customer_lon"] = CITY_CENTER_LON

    df["distance"] = haversine(df["lat"], df["lon"], df["customer_lat"], df["customer_lon"])

    return df


def transform_data():
    """
    Main transformation function that:
    1. Reads latest processed CSV
    2. Cleans the data
    3. Applies feature engineering
    4. Saves cleaned and featured datasets
    """
    # Get latest processed file
    processed_file = get_latest_processed_file()
    print(f"[INFO] Using latest processed file: {processed_file.name}")
    
    # Read data
    df = pd.read_csv(processed_file)
    
    # Clean data
    df_clean = clean_data(df.copy())
    
    # Save cleaned data
    output_clean = CURATED_DIR / "orders_clean.csv"
    output_clean.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(output_clean, index=False)
    print(f"[SUCCESS] Cleaned data saved to: {output_clean}")
    
    # Apply feature engineering
    df_featured = feature_engineering(df_clean.copy())
    
    # Save featured data
    output_featured = CURATED_DIR / "orders_featured.csv"
    output_featured.parent.mkdir(parents=True, exist_ok=True)
    df_featured.to_csv(output_featured, index=False)
    print(f"[SUCCESS] Featured data saved to: {output_featured}")
    
    return df_featured


if __name__ == "__main__":
    transform_data()

