#!/usr/bin/env python3
"""
Download UK Business Counts from NOMIS API
Dataset: NM_189_1 - Business Register Employment Survey 2024
"""
import requests
import pandas as pd
from pathlib import Path
from loguru import logger
import time

DEMOGRAPHICS_DIR = Path("data/raw/demographics")
OUTPUT_CSV = DEMOGRAPHICS_DIR / "business_counts.csv"

# NOMIS API configuration for Business Register Employment Survey
NOMIS_DATASET = "NM_189_1"
NOMIS_BASE_URL = "https://www.nomisweb.co.uk/api/v01/dataset"

def download_business_counts_nomis():
    """
    Download business counts from NOMIS API at MSOA level
    """
    logger.info(f"Downloading business counts from NOMIS API: {NOMIS_DATASET}")

    # NOMIS API URL for business data at MSOA level
    url = f"{NOMIS_BASE_URL}/{NOMIS_DATASET}.data.csv"

    # Parameters for MSOA-level business counts
    params = {
        'geography': 'TYPE297',  # MSOA geography type
        'time': 'latest',  # Latest available data
        'select': 'geography_code,geography_name,obs_value,date_name',
        'recordlimit': 0  # No limit - get all records
    }

    logger.info(f"API URL: {url}")
    logger.info(f"Parameters: {params}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}...")

            response = requests.get(url, params=params, timeout=300)

            if response.status_code == 200:
                content = response.content
                logger.success(f"Downloaded {len(content):,} bytes")

                # Parse CSV
                from io import StringIO
                df = pd.read_csv(StringIO(content.decode('utf-8')))

                logger.info(f"Loaded {len(df):,} records")
                logger.info(f"Columns: {list(df.columns)}")

                # Check if we have data
                if len(df) == 0:
                    logger.error("Downloaded file has no data rows")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    return False

                # Rename columns to match pipeline expectations
                df = df.rename(columns={
                    'GEOGRAPHY_CODE': 'msoa_code',
                    'GEOGRAPHY_NAME': 'msoa_name',
                    'OBS_VALUE': 'business_count',
                    'DATE_NAME': 'date'
                })

                # Keep only relevant columns
                keep_cols = [col for col in ['msoa_code', 'msoa_name', 'business_count', 'date'] if col in df.columns]
                df = df[keep_cols]

                # Remove date if not needed
                if 'date' in df.columns:
                    logger.info(f"Date range: {df['date'].unique()}")
                    df = df.drop(columns=['date'])

                # Check for empty values
                empty_count = df['business_count'].isna().sum()
                if empty_count > 0:
                    logger.warning(f"⚠ {empty_count:,} records have empty business_count values ({empty_count/len(df)*100:.1f}%)")

                # Show sample
                logger.info(f"Sample data:\n{df.head(10)}")

                # Save to CSV
                df.to_csv(OUTPUT_CSV, index=False)
                logger.success(f"✓ Saved to: {OUTPUT_CSV}")
                logger.success(f"✓ {len(df):,} MSOA records with {len(df.columns)} columns")

                return True

            else:
                logger.error(f"HTTP {response.status_code}: {response.text[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return False

        except Exception as e:
            logger.error(f"Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return False

    return False

if __name__ == "__main__":
    success = download_business_counts_nomis()
    if not success:
        logger.error("Failed to download business counts from NOMIS")
        logger.info("You may need to manually download from: https://www.nomisweb.co.uk/datasets/nm_189_1")
        exit(1)
