"""
Run the complete data pipeline
Executes all stages in sequence
"""
import subprocess
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent

# Pipeline stages in order

scripts = [
    PROJECT_ROOT / "ingestion" / "ingest_raw.py",
    PROJECT_ROOT / "transformation" / "json_to_csv.py",
    PROJECT_ROOT / "transformation" / "clean_data.py",
    PROJECT_ROOT / "transformation" / "feature_engineering.py",
]

print("=" * 50)
print("Starting Food Delivery Data Pipeline")
print("=" * 50)

for script in scripts:
    print(f"\n[RUNNING] {script.name}")
    print("-" * 50)
    
    result = subprocess.run([sys.executable, str(script)], cwd=PROJECT_ROOT)
    
    if result.returncode != 0:
        print(f"\n[ERROR] Pipeline failed at {script.name}")
        sys.exit(1)
    
    print(f"[COMPLETED] {script.name}")

print("\n" + "=" * 50)
print("[SUCCESS] Pipeline completed successfully!")
print("=" * 50)

