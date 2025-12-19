import pandas as pd
import numpy as np
from pathlib import Path

CURATED_DIR = Path(__file__).parent.parent / "data" / "curated"

#----------------city center coordinates----------------
CITY_CENTER_LAT = 30.7333
CITY_CENTER_LON = 76.7794

df = pd.read_csv(CURATED_DIR / "orders_clean.csv")

#--------------------customer-corrdinates----------------------
df["customer_lat"] = CITY_CENTER_LAT
df["customer_lan"] = CITY_CENTER_LON


# ----------calculating distance from the center if the city taking as customer location----------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c
#------------ new column distance in km-----------------------
df["distance"] = haversine(df["lat"], df["lon"], df["customer_lat"], df["customer_lan"])

# -------------saved-------------------
output_file = CURATED_DIR / "orders_featured.csv"
output_file.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_file, index=False)
print(f"[SUCCESS] Featured data saved to: {output_file}")

