import datetime
from pathlib import Path
import numpy as np
import pandas as pd

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURATED_DIR = Path(__file__).parent.parent / "data" / "curated"

# Chandigarh city center coordinates
CITY_CENTERS = {
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794, "core_km": 5.0,  "suburban_km": 12.0},
    "Delhi":      {"lat": 28.6139, "lon": 77.2090, "core_km": 10.0, "suburban_km": 25.0},
    "Mumbai":     {"lat": 19.0760, "lon": 72.8777, "core_km": 8.0,  "suburban_km": 20.0},
    "Bengaluru":  {"lat": 12.9716, "lon": 77.5946, "core_km": 8.0,  "suburban_km": 18.0},
}
EARTH_RADIUS_KM = 6371.0


def get_latest_processed_file() -> Path:
    """Find the newest CSV file from processed restaurant directories."""
    processed_dirs = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
    if not processed_dirs:
        raise FileNotFoundError("No processed directories found in data/processed")
    latest_dir = max(processed_dirs, key=lambda d: d.stat().st_mtime)

    csv_files = list(latest_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {latest_dir}")
    return csv_files[0]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the restaurant dataset:
    - Drop rows where name, lat, or lon is missing
    - Fill null cuisine and place with 'unknown'
    - Normalize cuisine strings (lowercase, trimmed)
    - Deduplicate based on name, lat, lon
    """
    cleaned = df.copy()

    # Drop null or empty name, lat, lon
    cleaned = cleaned.dropna(subset=["name", "lat", "lon"])
    cleaned = cleaned[cleaned["name"].astype(str).str.strip() != ""]

    # Fill defaults and clean casing
    cleaned["cuisine"] = cleaned["cuisine"].fillna("unknown").astype(str).str.strip().str.lower()
    cleaned["place"] = cleaned["place"].fillna("unknown").astype(str).str.strip()

    # Ensure numeric coordinates
    cleaned["lat"] = pd.to_numeric(cleaned["lat"], errors="coerce")
    cleaned["lon"] = pd.to_numeric(cleaned["lon"], errors="coerce")
    cleaned = cleaned.dropna(subset=["lat", "lon"])

    # Remove duplicates
    cleaned = cleaned.drop_duplicates(subset=["name", "lat", "lon"])
    return cleaned


def calculate_haversine_distance( lat1: pd.Series, lon1: pd.Series, lat2: float, lon2: float) -> pd.Series:
    
    """Vectorized Haversine distance calculation in kilometers using NumPy."""
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return np.round(EARTH_RADIUS_KM * c, 2)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Assign each restaurant to its nearest city and compute zone from that city's thresholds."""
    featured = df.copy()

    # One column of distances per city: shape (n_rows, 4)
    distances = pd.DataFrame({
        city: calculate_haversine_distance(featured["lat"], featured["lon"], c["lat"], c["lon"])
        for city, c in CITY_CENTERS.items()
    })

    featured["city"] = distances.idxmin(axis=1)           # name of the closest center
    featured["distance_to_center_km"] = distances.min(axis=1)

    # Per-row thresholds, looked up by that row's city
    core_limit = featured["city"].map({k: v["core_km"] for k, v in CITY_CENTERS.items()})
    suburban_limit = featured["city"].map({k: v["suburban_km"] for k, v in CITY_CENTERS.items()})

    d = featured["distance_to_center_km"]
    featured["delivery_zone"] = np.select(
        [d <= core_limit, d <= suburban_limit],
        ["Core Zone", "Suburban Zone"],
        default="Outskirts",
    )
    return featured

# ===================================================
# main cleaning pipline

def transform_data():
    """Execute cleaning and feature engineering workflow."""
    input_file = get_latest_processed_file()
    print(f"[INFO] Reading processed dataset: {input_file}")
    df = pd.read_csv(input_file)

    # 1. Clean
    df_clean = clean_data(df)
    clean_dir = CURATED_DIR / "restaurants_clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_file = clean_dir / "restaurants_clean.csv"
    df_clean.to_csv(clean_file, index=False, encoding="utf-8")
    print(f"[SUCCESS] Cleaned data saved: {clean_file} ({len(df_clean)} records)")

    # 2. Enrich with features
    df_featured = add_features(df_clean)
    featured_dir = CURATED_DIR / "restaurants_featured"
    featured_dir.mkdir(parents=True, exist_ok=True)
    featured_file = featured_dir / "restaurants_featured.csv"
    df_featured.to_csv(featured_file, index=False, encoding="utf-8")
    print(f"[SUCCESS] Featured data saved: {featured_file} ({len(df_featured)} records)")

    return df_featured


if __name__ == "__main__":
    transform_data()
