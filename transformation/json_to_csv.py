import pandas as pd
import json
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def get_latest_raw_file():
    """Get the latest raw JSON file from the raw directory."""
    raw_files = list(RAW_DIR.glob("*.json"))
    
    if not raw_files:
        raise FileNotFoundError("No raw JSON files found in data/raw")
    
    raw_file = max(raw_files, key=lambda f: f.stat().st_mtime)
    print(f"[INFO] Using latest raw file: {raw_file.name}")
    return raw_file


def parse_json_to_dataframe(raw_file):
    """
    Parse JSON file and convert to DataFrame.
    Extracts order information from Overpass API response format.
    """
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    data_rows = []
    
    for orders in raw_data["data"]["elements"]:
        data_rows.append(
            {
                "order_id": orders["id"],
                "name": orders["tags"].get("name"),
                "amenity": orders["tags"].get("amenity"),
                "cuisine": orders["tags"].get("cuisine"),
                "place": orders["tags"].get("addr:city"),
                "order_type": orders["type"],
                "lat": orders["lat"],
                "lon": orders["lon"],
            }
        )
    
    return pd.DataFrame(data_rows)


def json_to_csv():
    """
    Main function that:
    1. Gets the latest raw JSON file
    2. Parses JSON to DataFrame
    3. Saves DataFrame as CSV to processed directory
    """
    # Get latest raw file
    raw_file = get_latest_raw_file()
    
    # Parse JSON to DataFrame
    orders_df = parse_json_to_dataframe(raw_file)
    
    # Save to processed directory
    output_file = PROCESSED_DIR / f"orders_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    orders_df.to_csv(output_file, index=False)
    print(f"[SUCCESS] Processed orders saved to {output_file}")
    
    return orders_df


if __name__ == "__main__":
    json_to_csv()
