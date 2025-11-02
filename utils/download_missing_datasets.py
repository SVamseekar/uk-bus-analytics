"""
Download Missing Datasets for UK Bus Analytics

Downloads:
1. Rural-Urban Classification 2011 (LSOA level)
2. LSOA Boundaries GeoJSON 2021
3. Car Ownership Census 2021 (Table TS045)

Author: UK Bus Analytics Project
Date: 2025-11-02
"""

import requests
import pandas as pd
from pathlib import Path
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def download_rural_urban_classification():
    """
    Download Rural-Urban Classification 2011 for LSOAs
    """
    logger.info("Downloading Rural-Urban Classification 2011...")

    output_dir = Path('data/raw/boundaries')
    output_dir.mkdir(parents=True, exist_ok=True)

    # ONS Rural-Urban Classification
    url = "https://assets.publishing.service.gov.uk/media/5a7dfce7e5274a2e87dba3b7/RUC11_LAD11_EN.csv"

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        output_file = output_dir / 'rural_urban_2011.csv'
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Verify the file
        df = pd.read_csv(output_file)
        logger.info(f"✓ Downloaded Rural-Urban Classification: {len(df)} records")
        logger.info(f"  Saved to: {output_file}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download Rural-Urban Classification: {e}")
        logger.info("  Alternative: Manual download from ONS Geography Portal")
        return False


def download_lsoa_boundaries():
    """
    Download LSOA Boundaries 2021 GeoJSON
    """
    logger.info("Downloading LSOA Boundaries 2021...")

    output_dir = Path('data/raw/boundaries')
    output_dir.mkdir(parents=True, exist_ok=True)

    # ONS Geography Portal - LSOA Boundaries (Simplified version for better performance)
    # Using BGC (Generalised Clipped) boundaries for smaller file size
    url = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_Dec_2021_Boundaries_EW_BGC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"

    try:
        logger.info("  Note: This is a large file (~100MB), may take a few minutes...")
        response = requests.get(url, timeout=300, stream=True)
        response.raise_for_status()

        output_file = output_dir / 'lsoa_2021_boundaries.geojson'

        # Stream download for large file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Check file size
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"✓ Downloaded LSOA Boundaries: {file_size_mb:.1f} MB")
        logger.info(f"  Saved to: {output_file}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download LSOA Boundaries: {e}")
        logger.info("  Alternative: Manual download from ONS Geography Portal")
        logger.info("  URL: https://geoportal.statistics.gov.uk/")
        return False


def download_car_ownership():
    """
    Download Car Ownership Census 2021 (Table TS045)
    Using NOMIS API
    """
    logger.info("Downloading Car Ownership Census 2021...")

    output_dir = Path('data/raw/demographics')
    output_dir.mkdir(parents=True, exist_ok=True)

    # NOMIS API for Census 2021 Table TS045
    # Note: NOMIS API has changed, using alternative approach

    try:
        # Alternative: Download from ONS Bulk Data Service
        # This URL provides car ownership at LSOA level
        url = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2072_1.data.csv"

        params = {
            'geography': '1249934337...1249936433',  # LSOA codes range
            'c2021_carsno_10': '0,1,2,3,4',  # Number of cars categories
            'measures': '20100',  # Observation count
            'select': 'date,geography_code,geography_name,c2021_carsno_10_name,obs_value'
        }

        logger.info("  Fetching from NOMIS API (may take 1-2 minutes)...")
        response = requests.get(url, params=params, timeout=180)

        if response.status_code == 200:
            output_file = output_dir / 'car_ownership_2021_raw.csv'
            with open(output_file, 'wb') as f:
                f.write(response.content)

            # Process the data
            df = pd.read_csv(output_file)

            if not df.empty:
                logger.info(f"✓ Downloaded Car Ownership: {len(df)} records")

                # Process to calculate % no car by LSOA
                if 'OBS_VALUE' in df.columns and 'C2021_CARSNO_10_NAME' in df.columns:
                    processed = df.pivot_table(
                        index='GEOGRAPHY_CODE',
                        columns='C2021_CARSNO_10_NAME',
                        values='OBS_VALUE',
                        aggfunc='sum'
                    ).reset_index()

                    # Calculate percentage with no car
                    if 'No cars or vans in household' in processed.columns:
                        total_households = processed.drop('GEOGRAPHY_CODE', axis=1).sum(axis=1)
                        processed['pct_no_car'] = (processed['No cars or vans in household'] / total_households) * 100

                        output_file_processed = output_dir / 'car_ownership_2021_processed.csv'
                        processed.to_csv(output_file_processed, index=False)
                        logger.info(f"  Processed {len(processed)} LSOAs")
                        logger.info(f"  Saved to: {output_file_processed}")

                return True
            else:
                logger.warning("  API returned empty data")
                return False
        else:
            logger.error(f"  API returned status code: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"✗ Failed to download Car Ownership: {e}")
        logger.info("  Alternative: Manual download from NOMIS Web")
        logger.info("  URL: https://www.nomisweb.co.uk/")
        logger.info("  Table: Census 2021, TS045 - Car or van availability")
        return False


def main():
    """
    Download all missing datasets
    """
    logger.info("=" * 80)
    logger.info("DOWNLOADING MISSING DATASETS")
    logger.info("=" * 80)

    results = {}

    # Dataset 1: Rural-Urban Classification
    logger.info("\n[1/3] Rural-Urban Classification")
    results['rural_urban'] = download_rural_urban_classification()
    time.sleep(1)

    # Dataset 2: LSOA Boundaries
    logger.info("\n[2/3] LSOA Boundaries GeoJSON")
    results['lsoa_boundaries'] = download_lsoa_boundaries()
    time.sleep(1)

    # Dataset 3: Car Ownership
    logger.info("\n[3/3] Car Ownership Census 2021")
    results['car_ownership'] = download_car_ownership()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 80)

    for dataset, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"{dataset}: {status}")

    total_success = sum(results.values())
    logger.info(f"\nCompleted: {total_success}/{len(results)} datasets")
    logger.info("=" * 80)

    return results


if __name__ == '__main__':
    main()
