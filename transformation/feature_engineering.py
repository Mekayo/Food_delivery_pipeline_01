# Windows compatibility fix - must be imported before PySpark
import os
import sys
from pathlib import Path

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# Set HADOOP_HOME if not already set (Windows compatibility)
if "HADOOP_HOME" not in os.environ:
    project_root = Path(__file__).parent.parent
    hadoop_dir = project_root / "hadoop"
    if hadoop_dir.exists():
        os.environ["HADOOP_HOME"] = str(hadoop_dir)

# Disable Hadoop native IO for Windows compatibility
os.environ["HADOOP_OPTS"] = "-Djava.library.path="
os.environ["HADOOP_COMMON_LIB_NATIVE_DIR"] = ""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType
import math

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURATED_DIR = Path(__file__).parent.parent / "data" / "curated"

#----------------city center coordinates----------------
CITY_CENTER_LAT = 30.7333
CITY_CENTER_LON = 76.7794


def get_latest_processed_file():
    """
    Get the latest processed directory from the processed directory.

    json_to_csv.py writes each run to a timestamped folder in PROCESSED_DIR,
    so we need to pick the newest folder, not a flat CSV file.
    """
    processed_dirs = [p for p in PROCESSED_DIR.iterdir() if p.is_dir()]
    if not processed_dirs:
        raise FileNotFoundError("No processed directories found in data/processed")
    return max(processed_dirs, key=lambda f: f.stat().st_mtime)


def clean_data(df):
    """
    Clean the dataframe by:
    - Dropping nulls/empty in name, lat, lon
    - Filling null cuisine with "unknown" and normalizing
    - Dropping duplicate rows
    - Filling null place with "unknown"
    """
    # Filter out rows with null or empty name, lat, lon
    df = df.filter(
        F.col("name").isNotNull() & 
        (F.col("name") != "") &
        F.col("lat").isNotNull() & 
        F.col("lon").isNotNull()
    )
    
    # fill null in cuisine with "unknown"
    df = df.fillna({"cuisine": "unknown"})
    
    # lower the letter to avoid any explosion
    df = df.withColumn("cuisine", F.lower(F.trim(F.col("cuisine"))))
    
    # dropping duplicate rows have same restaurant and same places
    df = df.dropDuplicates(["name", "lat", "lon"])
    
    # fill null place with "unknown"
    df = df.fillna({"place": "unknown"})
    
    return df

# --------------calculating distance-------------------
def haversine_udf():
    """
    Create UDF for haversine distance calculation.
    Calculate the great circle distance between two points on Earth.
    Returns distance in kilometers.
    """
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    return F.udf(haversine, DoubleType())

# --------------feature_engineering-----------
def feature_engineering(df):
    R = 6371  # Earth radius in km

    df = (
        df
        .withColumn("customer_lat", F.lit(CITY_CENTER_LAT))
        .withColumn("customer_lon", F.lit(CITY_CENTER_LON))
    )

    df = df.withColumn(
        "distance",
        2 * R * F.asin(
            F.sqrt(
                F.pow(F.sin((F.radians(F.col("lat")) - F.radians(F.col("customer_lat"))) / 2), 2)
                + F.cos(F.radians(F.col("lat")))
                * F.cos(F.radians(F.col("customer_lat")))
                * F.pow(F.sin((F.radians(F.col("lon")) - F.radians(F.col("customer_lon"))) / 2), 2)
            )
        )
    )

    return df

# ------------ transform_data-----------
def transform_data():
    """
    Main transformation function that:
    1. Reads latest processed CSV
    2. Cleans the data
    3. Applies feature engineering
    4. Saves cleaned and featured datasets
    """
    spark = (
        SparkSession.builder
        .appName("FoodDeliveryPipeline")
        .master("local[*]")
        .config("spark.sql.warehouse.dir", "spark-warehouse")
        .config("spark.driver.memory", "2g")
        .config("spark.hadoop.io.native.lib.available", "false")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "1")
        .getOrCreate()
    )
    
    # Disable native IO in Hadoop config
    spark.sparkContext._jsc.hadoopConfiguration().set("io.native.lib.available", "false")

    try:
        # Get latest processed file
        processed_file = get_latest_processed_file()
        print(f"[INFO] Using latest processed file: {processed_file.name}")

        # Read data (handle both directory and single CSV file)
        if processed_file.is_dir():
            csv_files = list(processed_file.glob("*.csv"))
            if csv_files:
                df = spark.read.csv(str(csv_files[0]), header=True, inferSchema=True)
            else:
                df = spark.read.csv(str(processed_file), header=True, inferSchema=True)
        else:
            df = spark.read.csv(str(processed_file), header=True, inferSchema=True)

        # Clean data
        df_clean = clean_data(df)

        # Save cleaned data (Windows workaround: use Pandas to avoid Hadoop native lib issues)
        output_clean_dir = CURATED_DIR / "orders_clean"
        output_clean_dir.mkdir(parents=True, exist_ok=True)
        output_clean = output_clean_dir / "part-00000.csv"
        df_clean.toPandas().to_csv(output_clean, index=False, header=True)

        print(f"[SUCCESS] Cleaned data saved to: {output_clean}")

        # Apply feature engineering
        df_featured = feature_engineering(df_clean)

        # Save featured data (Windows workaround: use Pandas to avoid Hadoop native lib issues)
        output_featured_dir = CURATED_DIR / "orders_featured"
        output_featured_dir.mkdir(parents=True, exist_ok=True)
        output_featured = output_featured_dir / "part-00000.csv"
        df_featured.toPandas().to_csv(output_featured, index=False, header=True)

        print(f"[SUCCESS] Featured data saved to: {output_featured}")

        return df_featured
    finally :
        spark.stop()

if __name__ == "__main__":
    transform_data()

