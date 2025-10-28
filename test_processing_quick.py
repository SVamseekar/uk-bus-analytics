#!/usr/bin/env python3
"""
Quick Processing Test
Test the processing pipeline on one region to verify it works
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from loguru import logger
# Import directly from file
import importlib.util
spec = importlib.util.spec_from_file_location("processing", "data_pipeline/02_data_processing.py")
processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processing)
DynamicDataProcessingPipeline = processing.DynamicDataProcessingPipeline

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

def main():
    """Test processing pipeline on one region"""
    logger.info("🧪 Quick Processing Test - Testing Yorkshire region")

    try:
        # Initialize pipeline
        pipeline = DynamicDataProcessingPipeline()

        # Discover data
        logger.info("\n1️⃣ Discovering regional data files...")
        regional_files = pipeline.discover_regional_data_files()

        if 'yorkshire' not in regional_files:
            logger.error("Yorkshire data not found!")
            return 1

        logger.info(f"✓ Found {len(regional_files['yorkshire'])} files for Yorkshire")

        # Discover demographic data
        logger.info("\n2️⃣ Discovering demographic files...")
        demo_files = pipeline.discover_demographic_files()
        logger.info(f"✓ Found {len(demo_files)} demographic datasets")

        # Load demographic data
        logger.info("\n3️⃣ Loading demographic data...")
        demographic_data = pipeline.load_all_demographic_data(demo_files)
        logger.info(f"✓ Loaded {len(demographic_data)} demographic datasets")

        # Process Yorkshire region only (limit to 3 files for quick test)
        logger.info("\n4️⃣ Processing Yorkshire region (first 3 files only)...")
        test_files = regional_files['yorkshire'][:3]

        result = pipeline.process_region('yorkshire', test_files)

        logger.info("\n" + "="*60)
        logger.success("✓ PROCESSING TEST COMPLETED")
        logger.info("="*60)
        logger.info(f"Region: {result['region_name']}")
        logger.info(f"Files processed: {result['files_processed']}")
        logger.info(f"Stops extracted: {result['stops_count']}")
        logger.info(f"Routes extracted: {result['routes_count']}")
        logger.info(f"Services extracted: {result['services_count']}")

        # Check if data was actually extracted
        if result['stops_count'] > 0 and result['routes_count'] > 0:
            logger.success("\n✅ PIPELINE IS WORKING CORRECTLY!")
            logger.info("You can now run the full processing on all regions")
            return 0
        else:
            logger.warning("\n⚠️ No data was extracted - check the files")
            return 1

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
