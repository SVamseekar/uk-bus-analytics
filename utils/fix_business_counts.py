#!/usr/bin/env python3
"""
Fix business_counts.csv to use standard column names
"""
from pathlib import Path
import pandas as pd
from loguru import logger

DEMOGRAPHICS_DIR = Path("data/raw/demographics")

def main():
    logger.info("Fixing business_counts.csv column names...")

    business_file = DEMOGRAPHICS_DIR / "business_counts.csv"
    if not business_file.exists():
        logger.error(f"File not found: {business_file}")
        return

    # Read file
    df = pd.read_csv(business_file, low_memory=False)
    logger.info(f"Loaded {len(df)} MSOA records")
    logger.info(f"Current columns: {list(df.columns)}")

    # Rename columns to standard format
    df = df.rename(columns={
        'GEOGRAPHY_CODE': 'msoa_code',
        'GEOGRAPHY_NAME': 'msoa_name',
        'OBS_VALUE': 'business_count',
        'DATE': 'date'
    })

    # Drop date column if not needed
    if 'date' in df.columns:
        df = df.drop(columns=['date'])

    # Backup original
    backup = DEMOGRAPHICS_DIR / "business_counts.csv.ORIGINAL_BACKUP"
    if not backup.exists():
        business_file.rename(backup)
        logger.info(f"Backed up original to: {backup}")

    # Save fixed version
    df.to_csv(business_file, index=False)
    logger.success(f"✓ Fixed {business_file}")
    logger.info(f"New columns: {list(df.columns)}")
    logger.info(f"Sample MSOA codes: {df['msoa_code'].head(3).tolist()}")

if __name__ == "__main__":
    main()
