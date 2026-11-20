import json
import datetime
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def get_latest_raw_file() -> Path:
    """Return the most recently modified JSON file from data/raw."""
    raw_files = list(RAW_DIR.glob("*.json"))
    if not raw_files:
        raise FileNotFoundError("No raw JSON files found in data/raw")
    raw_file = max(raw_files, key=lambda f: f.stat().st_mtime)
    print(f"[INFO] Using latest raw file: {raw_file.name}")
    return raw_file


def parse_json_to_dataframe(raw_file: Path) -> pd.DataFrame:
    """Parse raw Overpass JSON elements into a Pandas DataFrame."""
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    elements = raw_data.get("data", {}).get("elements", [])
    data_rows = []

    for element in elements:
        tags = element.get("tags", {})
        data_rows.append(
            {
                "restaurant_id": element.get("id"),
                "name": tags.get("name"),
                "amenity": tags.get("amenity"),
                "cuisine": tags.get("cuisine"),
                "place": tags.get("addr:city"),
                "node_type": element.get("type"),
                "lat": element.get("lat"),
                "lon": element.get("lon"),
            }
        )

    df = pd.DataFrame(data_rows)
    return df


def json_to_csv() -> Path:
    """Extract raw JSON and save processed tabular data as CSV."""
    raw_file = get_latest_raw_file()
    df = parse_json_to_dataframe(raw_file)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROCESSED_DIR / f"restaurants_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "restaurants.csv"

    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"[SUCCESS] Processed {len(df)} restaurants saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    json_to_csv()
