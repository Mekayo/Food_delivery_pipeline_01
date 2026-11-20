import requests
import datetime as dt
import json
import time
from pathlib import Path

# query for overpass to get api for project api getting from link is large string that why calling query like this
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
QUERY = (
    "[out:json][timeout:180];"
    "area[\"name\"=\"Chandigarh\"][\"boundary\"=\"administrative\"]->.a;"
    "area[\"name\"=\"Delhi\"][\"boundary\"=\"administrative\"]->.b;"
    "area[\"name\"=\"Mumbai\"][\"boundary\"=\"administrative\"]->.c;"
    "area[\"name\"=\"Bengaluru\"][\"boundary\"=\"administrative\"]->.d;"
    "(.a;.b;.c;.d;)->.searchArea;"
    "("
    "node[\"amenity\"=\"restaurant\"](area.searchArea);"
    "node[\"amenity\"=\"fast_food\"](area.searchArea);"
    "node[\"amenity\"=\"cafe\"](area.searchArea);"
    ");out body;"
)

HEADERS = {"User-Agent": "food-delivery-pipeline/1.0 (29004hitesh@gmail.com)"}

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


def fetch_data():
     
    max_retries = 3
    backoff_seconds = 5

    # Fetched Data with retries
    for attempt in range(1, max_retries + 1):
        for url in ENDPOINTS:
            try:
                response = requests.post(url, data={"data": QUERY},
                                     headers=HEADERS, timeout=(10, 200))
                response.raise_for_status()
                api_data = response.json()
                break
            except requests.RequestException as e:
                print(f"[WARN] {url} failed: {e}")
        else:
            if attempt == max_retries:
                raise RuntimeError("All Overpass endpoints failed")
            time.sleep(backoff_seconds)
            continue
        break   

    # metadata
    raw_payload = {
        "metadata": {
            "source": "overpass_turbo",
            "endpoint": QUERY,
            "ingestion_timestamp": dt.datetime.now(dt.timezone.utc).isoformat()
        },
        "data": api_data
    }

    #  saving data to files
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"orders_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    file_path = RAW_DIR / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Raw data saved to: {file_path}")
    return raw_payload


if __name__ == "__main__":
    fetch_data()
