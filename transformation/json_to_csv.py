import pandas as pd
import json
from pathlib import Path

RAW_DIR = Path(r"C:\Users\monst\Desktop\Food_Delivery_01\data\raw")

# get all json files
raw_files = list(RAW_DIR.glob("*.json"))

if not raw_files:
    raise FileNotFoundError("No raw JSON files found in data/raw")

# pick the latest file (by modified time)
raw_file = max(raw_files, key=lambda f: f.stat().st_mtime)

print(f"[INFO] Using latest raw file: {raw_file.name}")

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

orders_df = pd.DataFrame(data_rows)
output_file = Path(r"C:\Users\monst\Desktop\Food_Delivery_01\data\processed\orders_" + str(pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")) + ".csv")
output_file.parent.mkdir(parents=True, exist_ok=True)
orders_df.to_csv(output_file, index=False)
print(f"[SUCCESS] processed orders saved to {output_file}")
