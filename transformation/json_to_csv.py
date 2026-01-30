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
# ---------java home for wind---------------- 
if "JAVA_HOME" not in os.environ:
    # Try common Java installation paths
    java_paths = [
        "/usr/lib/jvm/java-17-openjdk-amd64",
        "/usr/lib/jvm/java-11-openjdk-amd64",
        "/usr/lib/jvm/default-java"
    ]
    for path in java_paths:
        if os.path.exists(path):
            os.environ["JAVA_HOME"] = path
            break
# --------------------------------------------

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
import datetime
import json
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def get_latest_raw_file():
    
    raw_files = list(RAW_DIR.glob("*.json"))
    
    if not raw_files:
        raise FileNotFoundError("No raw JSON files found in data/raw")
    
    raw_file = max(raw_files, key=lambda f: f.stat().st_mtime)
    print(f"[INFO] Using latest raw file: {raw_file.name}")
    return raw_file


def parse_json_to_dataframe(spark, raw_file):
    
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    data_rows = []
    
    for orders in raw_data["data"]["elements"]:
        data_rows.append(
            (
                orders["id"],
                orders["tags"].get("name"),
                orders["tags"].get("amenity"),
                orders["tags"].get("cuisine"),
                orders["tags"].get("addr:city"),
                orders["type"],
                orders.get("lat"),
                orders.get("lon"),
            )
        )
    
    # Define schema
    schema = StructType([
        StructField("order_id", LongType(), True),
        StructField("name", StringType(), True),
        StructField("amenity", StringType(), True),
        StructField("cuisine", StringType(), True),
        StructField("place", StringType(), True),
        StructField("order_type", StringType(), True),
        StructField("lat", DoubleType(), True),
        StructField("lon", DoubleType(), True),
    ])
    
    return spark.createDataFrame(data_rows, schema=schema) 
    


def json_to_csv():
    
    spark = SparkSession.builder \
        .appName("FoodDeliveryPipeline") \
        .master("local[*]") \
        .config("spark.sql.warehouse.dir", "spark-warehouse") \
        .config("spark.driver.memory", "2g") \
        .config("spark.hadoop.io.native.lib.available", "false") \
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "1") \
        .getOrCreate()
    
    # Disable native IO in Hadoop config
    spark.sparkContext._jsc.hadoopConfiguration().set("io.native.lib.available", "false")
    try:
        # Get latest raw file
        raw_file = get_latest_raw_file()

        # Parse JSON to DataFrame
        orders_df = parse_json_to_dataframe(spark,raw_file)

        # Save to processed directory (Windows workaround: use Pandas to avoid Hadoop native lib issues)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = PROCESSED_DIR / f"orders_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "part-00000.csv"
        
        # Convert to Pandas and write CSV (avoids Hadoop native library issues on Windows)
        orders_df.toPandas().to_csv(output_file, index=False, header=True)
        print(f"[SUCCESS] Processed orders saved to {output_file}")

        return orders_df
    finally :
        spark.stop()

if __name__ == "__main__":
    json_to_csv()
