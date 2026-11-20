import os
from sqlalchemy import create_engine, text
import pandas as pd
from transformation.feature_engineering import CURATED_DIR

# DB Config: default matches docker-compose.yaml
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")  # mapped port from docker-compose
DB_NAME = os.getenv("POSTGRES_DB", "food_delivery")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_db_engine():
    """Create a SQLAlchemy engine connected to PostgreSQL."""
    return create_engine(DATABASE_URL)


def load_curated_to_postgres():
    """Load latest curated featured restaurants dataset into PostgreSQL."""
    curated_file = CURATED_DIR / "restaurants_featured" / "restaurants_featured.csv"
    if not curated_file.exists():
        raise FileNotFoundError(f"Curated file not found at: {curated_file}")

    print(f"[INFO] Reading curated dataset for DB load: {curated_file}")
    df = pd.read_csv(curated_file)

    engine = get_db_engine()

    # Create table or replace data into dim_restaurants
    table_name = "dim_restaurants"
    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        # Create primary key/index on restaurant_id
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_restaurant_id ON {table_name}(restaurant_id);"))
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar()

    print(f"[SUCCESS] Loaded {count} records into PostgreSQL table '{table_name}'")
    return count


if __name__ == "__main__":
    load_curated_to_postgres()
