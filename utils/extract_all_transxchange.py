"""
Extract all TransXChange XML files from zip archives across all 9 regions

Author: UK Bus Analytics Project
Date: 2025-11-02
"""

import zipfile
from pathlib import Path
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_all_transxchange_zips(input_dir: str = 'data/raw/transport',
                                   output_dir: str = 'data/raw/transxchange_extracted'):
    """
    Extract all TransXChange zip files from all 9 regions

    Args:
        input_dir: Directory containing regional transport zip files
        output_dir: Directory to extract XML files to
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all zip files
    zip_files = list(input_path.rglob('*.zip'))
    logger.info(f"Found {len(zip_files)} zip files across all regions")

    extracted_count = 0
    xml_count = 0
    failed_count = 0

    for i, zip_file in enumerate(zip_files, 1):
        # Get region name from parent directory
        region = zip_file.parent.name
        operator = zip_file.stem

        logger.info(f"\n[{i}/{len(zip_files)}] Processing: {region}/{operator}")

        # Create region-specific output directory
        region_output = output_path / region / operator
        region_output.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # List all files in zip
                file_list = zip_ref.namelist()
                xml_files = [f for f in file_list if f.endswith('.xml')]

                if not xml_files:
                    logger.warning(f"  No XML files found in {zip_file.name}")
                    continue

                # Extract XML files
                for xml_file in xml_files:
                    zip_ref.extract(xml_file, region_output)
                    xml_count += 1

                extracted_count += 1
                logger.info(f"  ✓ Extracted {len(xml_files)} XML files")

        except zipfile.BadZipFile:
            logger.error(f"  ✗ Bad zip file: {zip_file.name}")
            failed_count += 1
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            failed_count += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("EXTRACTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total zip files found: {len(zip_files)}")
    logger.info(f"Successfully extracted: {extracted_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Total XML files extracted: {xml_count}")
    logger.info(f"Output directory: {output_path}")
    logger.info("=" * 80)

    return extracted_count, xml_count


if __name__ == '__main__':
    extract_all_transxchange_zips()
