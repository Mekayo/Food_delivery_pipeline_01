import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURATED_DIR = Path(__file__).parent.parent / "data" / "curated"

# get latest processed file
processed_files = list(PROCESSED_DIR.glob("*.csv"))
if not processed_files:
    raise FileNotFoundError("No processed CSV files found")
raw_file = max(processed_files, key=lambda f: f.stat().st_mtime)

df = pd.read_csv(raw_file)


#----------------------cleaning data ---------------------------
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

# -------------------save----------------------
output_file = CURATED_DIR / "orders_clean.csv"
output_file.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_file, index=False)
print(f"[SUCCESS] Cleaned data saved to: {output_file}")

