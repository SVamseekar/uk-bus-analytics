#!/usr/bin/env python3
"""
Create LSOA-to-MSOA lookup table from postcode_lookup.csv
Required for merging MSOA-level business counts with LSOA-level stops
"""
import pandas as pd
from pathlib import Path
from loguru import logger

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
BOUNDARIES_DIR = PROJECT_ROOT / 'data' / 'raw' / 'boundaries'
DEMOGRAPHICS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'demographics'

def create_lsoa_msoa_lookup():
    """
    Extract unique LSOA-to-MSOA mapping from postcode lookup
    """
    logger.info("="*60)
    logger.info("CREATING LSOA-TO-MSOA LOOKUP TABLE")
    logger.info("="*60)

    postcode_file = BOUNDARIES_DIR / 'postcode_lookup.csv'

    if not postcode_file.exists():
        logger.error(f"Postcode lookup file not found: {postcode_file}")
        logger.error("Cannot create LSOA-MSOA lookup without this file")
        return None

    try:
        logger.info(f"Loading postcode lookup (321MB file, may take 30 seconds)...")

        # Load only needed columns to save memory
        df = pd.read_csv(
            postcode_file,
            usecols=['lsoa21cd', 'msoa21cd'],
            dtype={'lsoa21cd': 'str', 'msoa21cd': 'str'},
            low_memory=False
        )

        logger.info(f"Loaded {len(df)} postcode records")

        # Filter to England only (E01... and E02...)
        england = df[
            df['lsoa21cd'].str.startswith('E01', na=False) &
            df['msoa21cd'].str.startswith('E02', na=False)
        ]

        logger.info(f"Filtered to {len(england)} England records")

        # Get unique LSOA-MSOA pairs
        lookup = england[['lsoa21cd', 'msoa21cd']].drop_duplicates()

        # Rename to standard column names
        lookup = lookup.rename(columns={
            'lsoa21cd': 'lsoa_code',
            'msoa21cd': 'msoa_code'
        })

        # Sort by LSOA code
        lookup = lookup.sort_values('lsoa_code').reset_index(drop=True)

        # Save lookup table
        output_file = DEMOGRAPHICS_DIR / 'lsoa_to_msoa_lookup.csv'
        lookup.to_csv(output_file, index=False)

        logger.success(f"✓ Created LSOA-MSOA lookup: {len(lookup)} unique mappings")
        logger.success(f"✓ Saved to: {output_file}")

        # Show statistics
        msoa_counts = lookup.groupby('msoa_code').size()
        logger.info(f"\nStatistics:")
        logger.info(f"  Unique LSOAs: {lookup['lsoa_code'].nunique()}")
        logger.info(f"  Unique MSOAs: {lookup['msoa_code'].nunique()}")
        logger.info(f"  Avg LSOAs per MSOA: {msoa_counts.mean():.1f}")
        logger.info(f"  Min LSOAs per MSOA: {msoa_counts.min()}")
        logger.info(f"  Max LSOAs per MSOA: {msoa_counts.max()}")

        # Show example
        logger.info(f"\nExample mapping:")
        example_msoa = lookup['msoa_code'].iloc[0]
        example_lsoas = lookup[lookup['msoa_code'] == example_msoa]['lsoa_code'].tolist()
        logger.info(f"  MSOA {example_msoa} contains {len(example_lsoas)} LSOAs:")
        for lsoa in example_lsoas[:5]:
            logger.info(f"    - {lsoa}")
        if len(example_lsoas) > 5:
            logger.info(f"    ... and {len(example_lsoas) - 5} more")

        return output_file

    except Exception as e:
        logger.error(f"Failed to create LSOA-MSOA lookup: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    """
    Main execution
    """
    result = create_lsoa_msoa_lookup()

    if result:
        logger.info("="*60)
        logger.success("LOOKUP TABLE CREATED SUCCESSFULLY")
        logger.info("="*60)
        logger.info("\nNext step:")
        logger.info("Run: python run_full_pipeline.py")
    else:
        logger.error("="*60)
        logger.error("FAILED TO CREATE LOOKUP TABLE")
        logger.error("="*60)


if __name__ == "__main__":
    main()
