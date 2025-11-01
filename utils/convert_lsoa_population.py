#!/usr/bin/env python3
"""
Convert existing lsoa_population.csv to age_structure.csv format for pipeline
"""
from pathlib import Path
import pandas as pd
from loguru import logger

DEMOGRAPHICS_DIR = Path("data/raw/demographics")

def main():
    logger.info("Converting lsoa_population.csv to age_structure.csv format...")

    # Read existing LSOA population file
    lsoa_pop = DEMOGRAPHICS_DIR / "lsoa_population.csv"
    if not lsoa_pop.exists():
        logger.error(f"File not found: {lsoa_pop}")
        return

    df = pd.read_csv(lsoa_pop, low_memory=False)
    logger.info(f"Loaded {len(df)} rows from lsoa_population.csv")

    # Extract key columns
    result = pd.DataFrame({
        'lsoa_code': df['geography code'],
        'lsoa_name': df['geography'],
        'total_population': df['Gender: Total; Age: All Ages; measures: Value'].fillna(0).astype(int),
        'age_0_15': df['Gender: Total; Age: Aged 0 to 15; measures: Value'].fillna(0).astype(int),
        'age_16_64': df['Gender: Total; Age: Aged 16 to 64; measures: Value'].fillna(0).astype(int),
        'age_65_plus': df['Gender: Total; Age: Aged 65+; measures: Value'].fillna(0).astype(int),
    })

    # Backup old MSOA file if exists
    old_file = DEMOGRAPHICS_DIR / "age_structure.csv"
    if old_file.exists():
        backup = DEMOGRAPHICS_DIR / "age_structure.csv.MSOA_BACKUP"
        old_file.rename(backup)
        logger.info(f"Backed up MSOA file to: {backup}")

    # Save new LSOA file
    output = DEMOGRAPHICS_DIR / "age_structure.csv"
    result.to_csv(output, index=False)
    logger.success(f"✓ Created {output}")
    logger.info(f"  {len(result)} LSOAs")
    logger.info(f"  Total population: {result['total_population'].sum():,}")

    # Verify LSOA codes
    lsoa_codes = result['lsoa_code'].astype(str)
    e01_count = lsoa_codes.str.startswith('E01').sum()
    logger.info(f"  LSOA codes (E01): {e01_count} ({e01_count/len(result)*100:.1f}%)")

if __name__ == "__main__":
    main()
