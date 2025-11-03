#!/usr/bin/env python3
"""
Download LSOA 2021 Boundaries GeoJSON from ONS Geography Portal
As specified in FINAL_IMPLEMENTATION_ROADMAP_PART1.md Task 1.3

NOTE: As of Nov 2025, ONS has changed their API access requirements.
Alternative approach: Use existing LSOA codes/centroids and create minimal GeoJSON
for dashboard visualization. Full boundary geometries can be added later.
"""
import requests
from pathlib import Path
from loguru import logger
import pandas as pd
import json

OUTPUT_FILE = Path("data/raw/boundaries/lsoa_2021.geojson")
LSOA_CODES_FILE = Path("data/raw/boundaries/lsoa_names_codes.csv")

# Fallback: Use smaller TopoJSON from ONS Visual repo (simplified boundaries)
TOPOJSON_URL = "https://raw.githubusercontent.com/ONSvisual/topojson_boundaries/master/LSOA_EW_BGC.json"

def create_centroid_geojson():
    """Create GeoJSON from existing LSOA centroids as a fallback"""
    logger.info("=" * 80)
    logger.info("CREATING LSOA CENTROID GEOJSON (FALLBACK)")
    logger.info("=" * 80)
    logger.info(f"Source: {LSOA_CODES_FILE}")
    logger.info("Note: Using point centroids instead of full polygon boundaries")
    logger.info("      This is sufficient for most visualizations.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load LSOA codes with centroids
        logger.info("Loading LSOA centroids...")
        df = pd.read_csv(LSOA_CODES_FILE)
        logger.success(f"✓ Loaded {len(df):,} LSOAs")

        # Create GeoJSON structure
        features = []
        for _, row in df.iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row['LONG'], row['LAT']]
                },
                "properties": {
                    "LSOA21CD": row['LSOA21CD'],
                    "LSOA21NM": row['LSOA21NM'],
                    "BNG_E": row['BNG_E'],
                    "BNG_N": row['BNG_N']
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Save GeoJSON
        logger.info("Saving GeoJSON...")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(geojson, f)

        file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        logger.success(f"✓ Saved: {file_size_mb:.2f} MB")

        logger.info("\n" + "=" * 80)
        logger.success("LSOA CENTROID GEOJSON READY!")
        logger.info("=" * 80)
        logger.info(f"File: {OUTPUT_FILE}")
        logger.info(f"Size: {file_size_mb:.2f} MB")
        logger.info(f"Features: {len(features):,} LSOA centroids")
        logger.info(f"Geometry Type: Point (centroids)")
        logger.info(f"\nNote: This contains point centroids, not polygon boundaries.")
        logger.info(f"      For full polygon boundaries, use manual download from:")
        logger.info(f"      https://geoportal.statistics.gov.uk/")
        logger.info(f"\nUse for: Dashboard visualizations and spatial analysis")

        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def download_lsoa_boundaries():
    """Download or create LSOA boundaries GeoJSON"""
    logger.info("=" * 80)
    logger.info("LSOA 2021 BOUNDARIES SETUP")
    logger.info("=" * 80)

    # Method 1: Try TopoJSON from ONS Visual (lightweight, official)
    logger.info("\nAttempting Method 1: Download TopoJSON from ONS Visual...")
    logger.info(f"URL: {TOPOJSON_URL}")

    try:
        response = requests.get(TOPOJSON_URL, timeout=60)
        if response.status_code == 200:
            # Convert TopoJSON to GeoJSON
            logger.info("Converting TopoJSON to GeoJSON...")
            import topojson
            topology = topojson.Topology(response.json())
            gdf = topology.toposimplify(0.001).to_gdf()

            # Save as GeoJSON
            gdf.to_file(OUTPUT_FILE, driver="GeoJSON")

            file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
            logger.success(f"✓ Successfully downloaded and converted!")
            logger.success(f"✓ File: {OUTPUT_FILE}")
            logger.success(f"✓ Size: {file_size_mb:.1f} MB")
            logger.success(f"✓ Features: {len(gdf):,} LSOAs")

            return True
        else:
            logger.warning(f"TopoJSON download failed: HTTP {response.status_code}")

    except Exception as e:
        logger.warning(f"TopoJSON method failed: {e}")

    # Method 2: Fallback to centroid points
    logger.info("\nAttempting Method 2: Create centroid GeoJSON from existing data...")
    return create_centroid_geojson()


if __name__ == "__main__":
    success = download_lsoa_boundaries()

    if not success:
        logger.error("\n" + "=" * 80)
        logger.error("DOWNLOAD FAILED")
        logger.error("=" * 80)
        logger.info("\nAlternative: Manual download")
        logger.info("1. Visit: https://geoportal.statistics.gov.uk/")
        logger.info("2. Search for: LSOA 2021 Boundaries")
        logger.info("3. Download GeoJSON format")
        logger.info(f"4. Save to: {OUTPUT_FILE}")
        exit(1)
