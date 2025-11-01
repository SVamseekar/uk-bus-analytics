#!/usr/bin/env python3
"""
Download LSOA-level demographic data from Nomis API
Replaces MSOA-level files with proper LSOA data
"""
import requests
import pandas as pd
import time
from pathlib import Path
from loguru import logger

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DEMOGRAPHICS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'demographics'
DEMOGRAPHICS_DIR.mkdir(parents=True, exist_ok=True)


def download_census_age_population():
    """
    Download Census 2021 TS009 - Age by single year and sex
    LSOA level for England and Wales
    """
    logger.info("Downloading Census 2021 TS009 (Age/Population) at LSOA level...")

    # Nomis API endpoint for Census 2021
    # Dataset: TS009 - Age by single year and sex
    # Geography: LSOA (2021 boundaries)

    url = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2072_1.bulk.csv"

    params = {
        'geography': '1249902593...1249936345',  # All England LSOAs
        'date': 'latest',
        'measures': '20100',  # Observation values
        'select': 'geography_code,geography_name,date,c_age_name,obs_value'
    }

    try:
        logger.info("Requesting data from Nomis API (this may take 2-3 minutes)...")
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()

        # Save raw response
        output_file = DEMOGRAPHICS_DIR / 'census_2021_age_lsoa.csv'
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Load and verify
        df = pd.read_csv(output_file)
        logger.success(f"✓ Downloaded {len(df)} records")
        logger.success(f"✓ Saved to: {output_file}")
        logger.info(f"  LSOAs: {df['GEOGRAPHY_CODE'].nunique()}")
        logger.info(f"  Age groups: {df['C_AGE_NAME'].nunique()}")

        return output_file

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download Census data: {e}")
        logger.warning("You may need to download manually from:")
        logger.warning("https://www.nomisweb.co.uk/datasets/c2021ts009")
        return None


def download_claimant_count():
    """
    Download Claimant Count (UCJSA) at LSOA level
    Proxy for unemployment at small area level
    """
    logger.info("Downloading Claimant Count (UCJSA) at LSOA level...")

    # Nomis API endpoint for Claimant Count
    # Dataset: Claimant count by sex and age
    url = "https://www.nomisweb.co.uk/api/v01/dataset/NM_162_1.bulk.csv"

    params = {
        'geography': '1249902593...1249936345',  # All England LSOAs
        'date': 'latest',  # Most recent month
        'measures': '20100',
        'sex': '0',  # Total (all sexes)
        'item': '1',  # Claimants as % of residents
        'select': 'geography_code,geography_name,date,sex_name,age_name,measures_name,obs_value'
    }

    try:
        logger.info("Requesting data from Nomis API (this may take 1-2 minutes)...")
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()

        # Save raw response
        output_file = DEMOGRAPHICS_DIR / 'claimant_count_lsoa.csv'
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Load and verify
        df = pd.read_csv(output_file)
        logger.success(f"✓ Downloaded {len(df)} records")
        logger.success(f"✓ Saved to: {output_file}")
        logger.info(f"  LSOAs: {df['GEOGRAPHY_CODE'].nunique()}")
        logger.info(f"  Date: {df['DATE_NAME'].unique()[0] if len(df) > 0 else 'N/A'}")

        return output_file

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download Claimant Count data: {e}")
        logger.warning("You may need to download manually from:")
        logger.warning("https://www.nomisweb.co.uk/datasets/ucjsa")
        return None


def process_census_data(census_file):
    """
    Process Census 2021 age data into pipeline-compatible format
    """
    if census_file is None or not census_file.exists():
        logger.warning("Census file not found, skipping processing")
        return None

    logger.info("Processing Census age data...")

    try:
        df = pd.read_csv(census_file, low_memory=False)

        # Rename columns to standard format
        df = df.rename(columns={
            'GEOGRAPHY_CODE': 'lsoa_code',
            'GEOGRAPHY_NAME': 'lsoa_name',
            'C_AGE_NAME': 'age_group',
            'OBS_VALUE': 'population'
        })

        # Pivot to wide format (one row per LSOA, columns for each age group)
        df_wide = df.pivot_table(
            index=['lsoa_code', 'lsoa_name'],
            columns='age_group',
            values='population',
            aggfunc='sum'
        ).reset_index()

        # Calculate key age bands
        age_cols = [col for col in df_wide.columns if col not in ['lsoa_code', 'lsoa_name']]

        # Add computed columns
        df_wide['total_population'] = df_wide[age_cols].sum(axis=1)
        df_wide['age_0_15'] = df_wide[[col for col in age_cols if 'Aged' in str(col) and any(x in str(col) for x in ['0 to 4', '5 to 9', '10 to 14', '15'])]].sum(axis=1)
        df_wide['age_16_64'] = df_wide[[col for col in age_cols if 'Aged' in str(col) and any(x in str(col) for x in ['16 to ', '20 to ', '30 to ', '40 to ', '50 to ', '60 to 64'])]].sum(axis=1)
        df_wide['age_65_plus'] = df_wide[[col for col in age_cols if 'Aged' in str(col) and ('65' in str(col) or '70' in str(col) or '75' in str(col) or '80' in str(col) or '85' in str(col) or '90' in str(col))]].sum(axis=1)

        output_file = DEMOGRAPHICS_DIR / 'age_population_lsoa.csv'
        df_wide.to_csv(output_file, index=False)

        logger.success(f"✓ Processed Census data: {len(df_wide)} LSOAs")
        logger.success(f"✓ Saved to: {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"Failed to process Census data: {e}")
        return None


def process_claimant_data(claimant_file):
    """
    Process Claimant Count data into pipeline-compatible format
    """
    if claimant_file is None or not claimant_file.exists():
        logger.warning("Claimant Count file not found, skipping processing")
        return None

    logger.info("Processing Claimant Count data...")

    try:
        df = pd.read_csv(claimant_file, low_memory=False)

        # Rename columns
        df = df.rename(columns={
            'GEOGRAPHY_CODE': 'lsoa_code',
            'GEOGRAPHY_NAME': 'lsoa_name',
            'OBS_VALUE': 'claimant_rate',
            'AGE_NAME': 'age_group'
        })

        # Aggregate to LSOA level (sum across age groups for total)
        df_agg = df.groupby(['lsoa_code', 'lsoa_name']).agg({
            'claimant_rate': 'mean'  # Average across age groups
        }).reset_index()

        output_file = DEMOGRAPHICS_DIR / 'claimant_count_lsoa_processed.csv'
        df_agg.to_csv(output_file, index=False)

        logger.success(f"✓ Processed Claimant Count data: {len(df_agg)} LSOAs")
        logger.success(f"✓ Saved to: {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"Failed to process Claimant Count data: {e}")
        return None


def main():
    """
    Main execution: Download and process LSOA demographics
    """
    logger.info("="*60)
    logger.info("LSOA DEMOGRAPHICS DOWNLOADER")
    logger.info("="*60)

    # Download Census 2021 age/population
    census_file = download_census_age_population()
    if census_file:
        time.sleep(2)  # Be nice to API
        process_census_data(census_file)

    # Download Claimant Count
    claimant_file = download_claimant_count()
    if claimant_file:
        time.sleep(2)
        process_claimant_data(claimant_file)

    logger.info("="*60)
    logger.success("DOWNLOAD COMPLETE")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("1. Verify files in data/raw/demographics/")
    logger.info("2. Run: python utils/create_lsoa_msoa_lookup.py")
    logger.info("3. Run: python run_full_pipeline.py")


if __name__ == "__main__":
    main()
