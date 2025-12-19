"""
tasks:
Fetch API

Save raw JSON

NOTHING ELSE
"""
import requests
import datetime as dt
import json
from pathlib import Path

# query for overpass to get api for project api getting from link is large string that why calling query like this


API_URL = (
    "https://overpass-api.de/api/interpreter?data="
    "[out:json][timeout:25];"
    "area[\"name\"=\"Chandigarh\"][\"boundary\"=\"administrative\"]->.searchArea;"
    "("
    "node[\"amenity\"=\"restaurant\"](area.searchArea);"
    "node[\"amenity\"=\"fast_food\"](area.searchArea);"
    "node[\"amenity\"=\"cafe\"](area.searchArea);"
    ");"
    "out tags center;"
)

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Fetched Data
response = requests.get(API_URL, timeout=30)
response.raise_for_status()
api_data = response.json()

# metadata
raw_payload = {
    "metadata": {
        "source": "overpass_turbo",
        "endpoint": API_URL,
        "ingestion_timestamp": dt.datetime.utcnow().isoformat()
    },
    "data": api_data
}

#  saving data to files
RAW_DIR.mkdir(parents=True, exist_ok=True)

filename = f"orders_{dt.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
file_path = RAW_DIR / filename

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(raw_payload, f, indent=2, ensure_ascii=False)

print(f"[SUCCESS] Raw data saved to: {file_path}")
