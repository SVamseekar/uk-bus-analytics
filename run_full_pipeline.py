#!/usr/bin/env python3
"""
Master Pipeline Runner - Runs steps 2,3,4 in correct sequence
"""
import subprocess
import sys

def main():
    print("="*80)
    print("RUNNING PROPER PIPELINE SEQUENCE")
    print("="*80)

    # Step 2: Data Processing (with utils)
    print("\n[1/3] Running 02_data_processing.py...")
    result = subprocess.run([sys.executable, "data_pipeline/02_data_processing.py"])
    if result.returncode != 0:
        print("❌ Step 2 failed")
        sys.exit(1)

    # Step 3: Data Validation
    print("\n[2/3] Running 03_data_validation.py...")
    result = subprocess.run([sys.executable, "data_pipeline/03_data_validation.py"])
    if result.returncode != 0:
        print("⚠️ Step 3 failed (continuing...)")

    # Step 4: Descriptive Analytics
    print("\n[3/3] Running 04_descriptive_analytics.py...")
    result = subprocess.run([sys.executable, "data_pipeline/04_descriptive_analytics.py"])
    if result.returncode != 0:
        print("⚠️ Step 4 failed (continuing...)")

    print("\n✅ Pipeline sequence complete!")

if __name__ == "__main__":
    main()
