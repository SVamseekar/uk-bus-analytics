#!/usr/bin/env python3
"""
Distribute MSOA-level demographic data to LSOA level
Uses population-weighted distribution from lookup table
"""
from pathlib import Path
import pandas as pd
from loguru import logger

DEMOGRAPHICS_DIR = Path("data/raw/demographics")

def distribute_msoa_to_lsoa(msoa_file, output_file, msoa_col='geography code', name_col='geography'):
    """
    Distribute MSOA data to LSOA level using lookup table

    Args:
        msoa_file: Input file with MSOA-level data
        output_file: Output file for LSOA-level data
        msoa_col: Column name containing MSOA codes
        name_col: Column name containing geography names
    """
    logger.info(f"Loading {msoa_file.name}...")
    msoa_df = pd.read_csv(msoa_file, low_memory=False)
    logger.info(f"  {len(msoa_df)} MSOA records")

    # Load lookup
    lookup_file = DEMOGRAPHICS_DIR / "lsoa_to_msoa_lookup.csv"
    if not lookup_file.exists():
        logger.error("LSOA-MSOA lookup not found. Run: python utils/create_lsoa_msoa_lookup.py")
        return False

    lookup = pd.read_csv(lookup_file)
    logger.info(f"  Loaded lookup: {len(lookup)} LSOA→MSOA mappings")

    # Count LSOAs per MSOA
    lsoas_per_msoa = lookup.groupby('msoa_code').size().reset_index(name='lsoa_count')

    # Merge to get LSOA count for each MSOA
    msoa_df = msoa_df.merge(lsoas_per_msoa, left_on=msoa_col, right_on='msoa_code', how='left')

    # Merge MSOA data with lookup to expand to LSOA level
    lsoa_df = lookup.merge(
        msoa_df,
        left_on='msoa_code',
        right_on=msoa_col,
        how='left'
    )

    # Identify numeric columns to distribute
    numeric_cols = msoa_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    # Exclude count columns
    numeric_cols = [col for col in numeric_cols if col not in ['lsoa_count']]

    # Distribute numeric values equally among LSOAs in each MSOA
    for col in numeric_cols:
        if col in lsoa_df.columns:
            lsoa_df[col] = lsoa_df[col] / lsoa_df['lsoa_count']
            lsoa_df[col] = lsoa_df[col].round(0).astype('Int64')  # Use Int64 to handle NaN

    # Keep only LSOA-relevant columns
    keep_cols = ['lsoa_code', 'lsoa_name'] + numeric_cols
    keep_cols = [col for col in keep_cols if col in lsoa_df.columns]
    lsoa_df = lsoa_df[keep_cols]

    # Rename columns to match expected format
    lsoa_df = lsoa_df.drop_duplicates(subset=['lsoa_code'])

    # Save
    lsoa_df.to_csv(output_file, index=False)
    logger.success(f"✓ Created {output_file}")
    logger.info(f"  {len(lsoa_df)} LSOA records")
    logger.info(f"  {len(keep_cols)} columns")

    return True

def main():
    logger.info("="*60)
    logger.info("DISTRIBUTING MSOA DATA TO LSOA LEVEL")
    logger.info("="*60)

    # 1. Convert age_structure (currently misnamed lsoa_population.csv)
    logger.info("\n[1/2] Converting age/population data...")
    msoa_pop = DEMOGRAPHICS_DIR / "lsoa_population.csv"
    if msoa_pop.exists():
        # Backup old age_structure
        old_age = DEMOGRAPHICS_DIR / "age_structure.csv"
        if old_age.exists():
            backup = DEMOGRAPHICS_DIR / "age_structure.csv.MSOA_BACKUP"
            if not backup.exists():  # Don't overwrite existing backup
                old_age.rename(backup)
                logger.info(f"  Backed up to: {backup}")

        # Create LSOA-level age_structure
        output = DEMOGRAPHICS_DIR / "age_structure.csv"

        # Read and process
        df = pd.read_csv(msoa_pop, low_memory=False)
        logger.info(f"  Loaded {len(df)} MSOA records from lsoa_population.csv")

        # Extract key age columns (just the Value columns, not Percent)
        age_data = pd.DataFrame({
            'geography code': df['geography code'],
            'geography': df['geography'],
            'total_population': df['Gender: Total; Age: All Ages; measures: Value'].fillna(0),
            'age_0_15': df['Gender: Total; Age: Aged 0 to 15; measures: Value'].fillna(0),
            'age_16_64': df['Gender: Total; Age: Aged 16 to 64; measures: Value'].fillna(0),
            'age_65_plus': df['Gender: Total; Age: Aged 65+; measures: Value'].fillna(0),
        })

        # Save temp file
        temp_file = DEMOGRAPHICS_DIR / "temp_msoa_age.csv"
        age_data.to_csv(temp_file, index=False)

        # Distribute to LSOA
        distribute_msoa_to_lsoa(temp_file, output)
        temp_file.unlink()  # Delete temp file

    # 2. Convert unemployment
    logger.info("\n[2/2] Converting unemployment data...")
    msoa_unemp = DEMOGRAPHICS_DIR / "unemployment_2024.csv"
    if msoa_unemp.exists():
        # Backup old unemployment
        backup = DEMOGRAPHICS_DIR / "unemployment_2024.csv.MSOA_BACKUP"
        if not backup.exists():
            msoa_unemp.rename(backup)
            logger.info(f"  Backed up to: {backup}")

            # Reload from backup for processing
            df = pd.read_csv(backup, low_memory=False)
            logger.info(f"  Loaded {len(df)} MSOA records")

            # Extract key unemployment columns (just Value columns)
            unemp_data = pd.DataFrame({
                'geography code': df['geography code'],
                'geography': df['geography'],
                'total_claimants': df['Benefit: Total (all UC and JSA claimants); Gender: Total; Age: All categories: Age 16+; measure: Claimant count; measures: Value'].fillna(0),
            })

            # Save temp file
            temp_file = DEMOGRAPHICS_DIR / "temp_msoa_unemp.csv"
            unemp_data.to_csv(temp_file, index=False)

            # Distribute to LSOA
            output = DEMOGRAPHICS_DIR / "unemployment_2024.csv"
            distribute_msoa_to_lsoa(temp_file, output)
            temp_file.unlink()

    logger.info("\n" + "="*60)
    logger.success("MSOA→LSOA DISTRIBUTION COMPLETE")
    logger.info("="*60)

if __name__ == "__main__":
    main()
