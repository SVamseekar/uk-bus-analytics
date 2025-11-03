#!/usr/bin/env python3
"""
Process Census 2021 TS045 Car Ownership Data from NOMIS Bulk Download
Converts bulk CSV to pipeline-ready format with lsoa_code and pct_no_car
"""
import pandas as pd
from pathlib import Path
from loguru import logger

INPUT_FILE = Path("data/raw/demographics/census2021-ts045-lsoa.csv")
OUTPUT_FILE = Path("data/raw/demographics/car_ownership_2021.csv")

def process_car_ownership():
    """Process TS045 bulk download to pipeline format"""

    logger.info("=" * 80)
    logger.info("PROCESSING CAR OWNERSHIP CENSUS 2021 - TS045 LSOA")
    logger.info("=" * 80)

    # Load data
    logger.info(f"Loading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)

    logger.info(f"Loaded {len(df):,} records")
    logger.info(f"Columns: {list(df.columns)}")

    # Rename columns to pipeline format
    df = df.rename(columns={
        'geography code': 'lsoa_code',
        'geography': 'lsoa_name',
        'Number of cars or vans: Total: All households': 'total_households',
        'Number of cars or vans: No cars or vans in household': 'households_no_car',
        'Number of cars or vans: 1 car or van in household': 'households_1_car',
        'Number of cars or vans: 2 cars or vans in household': 'households_2_cars',
        'Number of cars or vans: 3 or more cars or vans in household': 'households_3plus_cars'
    })

    # Calculate percentage with no car
    df['pct_no_car'] = (df['households_no_car'] / df['total_households']) * 100

    # Calculate percentage with 1+ cars (inverse)
    df['pct_with_car'] = 100 - df['pct_no_car']

    # Keep essential columns
    keep_cols = [
        'lsoa_code',
        'lsoa_name',
        'total_households',
        'households_no_car',
        'households_1_car',
        'households_2_cars',
        'households_3plus_cars',
        'pct_no_car',
        'pct_with_car'
    ]

    df = df[keep_cols]

    # Filter to England LSOAs only (E01 codes)
    before = len(df)
    df = df[df['lsoa_code'].str.startswith('E01', na=False)]
    logger.info(f"Filtered to England LSOAs: {before:,} → {len(df):,}")

    # Save processed file
    df.to_csv(OUTPUT_FILE, index=False)

    logger.success(f"✓ Saved to: {OUTPUT_FILE}")
    logger.success(f"✓ {len(df):,} LSOAs with {len(df.columns)} columns")

    # Display sample
    logger.info(f"\nSample data:\n{df.head(5)}")

    # Statistics
    stats = df['pct_no_car'].describe()
    logger.info(f"\nStatistics - % Households with No Car:")
    logger.info(f"  Count: {int(stats['count']):,} LSOAs")
    logger.info(f"  Mean: {stats['mean']:.1f}%")
    logger.info(f"  Median: {stats['50%']:.1f}%")
    logger.info(f"  Min: {stats['min']:.1f}%")
    logger.info(f"  Max: {stats['max']:.1f}%")
    logger.info(f"  Std Dev: {stats['std']:.1f}%")

    # High/low car ownership LSOAs
    logger.info(f"\nTop 5 LSOAs with lowest car ownership (highest % no car):")
    top_no_car = df.nlargest(5, 'pct_no_car')[['lsoa_name', 'pct_no_car', 'total_households']]
    logger.info(f"\n{top_no_car.to_string(index=False)}")

    logger.info(f"\nTop 5 LSOAs with highest car ownership (lowest % no car):")
    top_with_car = df.nsmallest(5, 'pct_no_car')[['lsoa_name', 'pct_no_car', 'total_households']]
    logger.info(f"\n{top_with_car.to_string(index=False)}")

    logger.info("\n" + "=" * 80)
    logger.success("CAR OWNERSHIP DATA READY FOR PIPELINE!")
    logger.info("=" * 80)
    logger.info(f"File: {OUTPUT_FILE}")
    logger.info(f"LSOAs: {len(df):,}")
    logger.info(f"Unlocks questions: A6, A7, B16, D27, D28")
    logger.info(f"\nNext step: Run 02_data_processing.py to merge with stops")

    return True


if __name__ == "__main__":
    try:
        if not INPUT_FILE.exists():
            logger.error(f"Input file not found: {INPUT_FILE}")
            logger.info("Run: cd data/raw/demographics && curl -L -o census2021-ts045.zip https://www.nomisweb.co.uk/output/census/2021/census2021-ts045.zip && unzip census2021-ts045.zip census2021-ts045-lsoa.csv")
            exit(1)

        success = process_car_ownership()

        if success:
            logger.success("✓ Processing complete!")
        else:
            logger.error("✗ Processing failed")
            exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        exit(1)
