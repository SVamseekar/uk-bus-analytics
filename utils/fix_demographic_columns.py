#!/usr/bin/env python3
"""
Fix column names in demographic files to match pipeline expectations
"""
from pathlib import Path
import pandas as pd
from loguru import logger

DEMOGRAPHICS_DIR = Path("data/raw/demographics")

def fix_imd_2019():
    """Fix IMD 2019 column names"""
    logger.info("Fixing imd_2019.csv column names...")

    file = DEMOGRAPHICS_DIR / "imd_2019.csv"
    if not file.exists():
        logger.error(f"File not found: {file}")
        return False

    df = pd.read_csv(file, low_memory=False)
    logger.info(f"Loaded {len(df)} records")

    # Rename columns
    df = df.rename(columns={
        'LSOA code (2011)': 'lsoa_code',
        'LSOA name (2011)': 'lsoa_name'
    })

    # Backup original
    backup = DEMOGRAPHICS_DIR / "imd_2019.csv.ORIGINAL_BACKUP"
    if not backup.exists():
        file.rename(backup)
        logger.info(f"Backed up to: {backup}")

    # Save fixed version
    df.to_csv(file, index=False)
    logger.success(f"✓ Fixed {file}")
    logger.info(f"  Renamed: 'LSOA code (2011)' -> 'lsoa_code'")
    logger.info(f"  Sample codes: {df['lsoa_code'].head(3).tolist()}")
    return True

def fix_schools_2024():
    """Fix schools_2024.csv - add lsoa_code column"""
    logger.info("Fixing schools_2024.csv...")

    file = DEMOGRAPHICS_DIR / "schools_2024.csv"
    if not file.exists():
        logger.error(f"File not found: {file}")
        return False

    try:
        df = pd.read_csv(file, low_memory=False, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, low_memory=False, encoding='latin-1')
        except Exception as e:
            logger.warning(f"Could not read schools_2024.csv: {e}")
            logger.warning("Skipping - file has encoding issues or is duplicate")
            return False

    logger.info(f"Loaded {len(df)} records")
    logger.info(f"Current columns: {list(df.columns[:5])}...")

    # Check if it has LSOA column with different name
    potential_lsoa_cols = [col for col in df.columns if 'lsoa' in col.lower()]

    if potential_lsoa_cols:
        logger.info(f"Found potential LSOA columns: {potential_lsoa_cols}")
        # Use the first one and rename it
        df['lsoa_code'] = df[potential_lsoa_cols[0]]
        logger.info(f"Using column: {potential_lsoa_cols[0]} as lsoa_code")
    else:
        logger.warning("No LSOA column found - checking if we can use postcode...")
        # This file might need geo-matching, skip for now
        logger.warning("Skipping schools_2024 - needs geospatial matching")
        return False

    # Backup original
    backup = DEMOGRAPHICS_DIR / "schools_2024.csv.ORIGINAL_BACKUP"
    if not backup.exists():
        file.rename(backup)
        logger.info(f"Backed up to: {backup}")

    # Save fixed version
    df.to_csv(file, index=False)
    logger.success(f"✓ Fixed {file}")
    return True

def fix_edubase():
    """Fix edubasealldata20251028.csv - add lsoa_code column"""
    logger.info("Fixing edubasealldata20251028.csv...")

    file = DEMOGRAPHICS_DIR / "edubasealldata20251028.csv"
    if not file.exists():
        logger.error(f"File not found: {file}")
        return False

    try:
        df = pd.read_csv(file, low_memory=False, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, low_memory=False, encoding='latin-1')
        except Exception as e:
            logger.warning(f"Could not read edubase: {e}")
            logger.warning("Skipping - file has encoding issues or is duplicate")
            return False

    logger.info(f"Loaded {len(df)} records")
    logger.info(f"Current columns: {list(df.columns[:10])}...")

    # Check for LSOA column
    potential_lsoa_cols = [col for col in df.columns if 'lsoa' in col.lower() or 'LSOA' in col]

    if potential_lsoa_cols:
        logger.info(f"Found potential LSOA columns: {potential_lsoa_cols}")
        # Use the first one and rename it
        df['lsoa_code'] = df[potential_lsoa_cols[0]]
        logger.info(f"Using column: {potential_lsoa_cols[0]} as lsoa_code")
    else:
        logger.warning("No LSOA column found - this file might need geospatial matching")
        logger.warning("Skipping edubase - needs geospatial matching or is duplicate of schools_2024")
        return False

    # Backup original
    backup = DEMOGRAPHICS_DIR / "edubasealldata20251028.csv.ORIGINAL_BACKUP"
    if not backup.exists():
        file.rename(backup)
        logger.info(f"Backed up to: {backup}")

    # Save fixed version
    df.to_csv(file, index=False)
    logger.success(f"✓ Fixed {file}")
    return True

def main():
    logger.info("="*60)
    logger.info("FIXING DEMOGRAPHIC COLUMN NAMES")
    logger.info("="*60)

    results = {
        'imd_2019': fix_imd_2019(),
        'schools_2024': fix_schools_2024(),
        'edubase': fix_edubase()
    }

    logger.info("\n" + "="*60)
    logger.info("RESULTS")
    logger.info("="*60)
    for name, success in results.items():
        status = "✓ FIXED" if success else "⚠ SKIPPED"
        logger.info(f"{status}: {name}")

if __name__ == "__main__":
    main()
