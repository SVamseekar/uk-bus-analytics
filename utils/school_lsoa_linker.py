"""
School to LSOA Linker
Links school postcodes to LSOAs and creates aggregated school counts per LSOA
"""
import pandas as pd
import requests
from pathlib import Path
from loguru import logger
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import DATA_RAW

def download_postcode_lsoa_lookup():
    """
    Download ONS Postcode to LSOA lookup file
    """
    logger.info("Downloading ONS Postcode to LSOA lookup...")

    # ONS Postcode Directory - LSOA lookup
    url = "https://www.arcgis.com/sharing/rest/content/items/5b681a6c77d6429da0b73fb98e64db2f/data"

    output_path = DATA_RAW / 'demographics' / 'postcode_lsoa_lookup.zip'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=300, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.success(f"Downloaded postcode lookup: {output_path}")

            # Extract CSV
            import zipfile
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    zip_ref.extractall(DATA_RAW / 'demographics')
                    csv_path = DATA_RAW / 'demographics' / csv_files[0]
                    logger.success(f"Extracted: {csv_path}")
                    return csv_path
        else:
            logger.error(f"Failed to download: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None

def link_schools_to_lsoas(schools_file: Path, postcode_lookup_file: Path, output_file: Path):
    """
    Link schools to LSOAs using postcode lookup and create aggregated counts
    """
    logger.info(f"Loading schools data from {schools_file.name}...")

    # Load schools with key columns
    schools_df = pd.read_csv(
        schools_file,
        usecols=['URN', 'EstablishmentName', 'TypeOfEstablishment (name)',
                 'PhaseOfEducation (name)', 'Postcode', 'EstablishmentStatus (name)'],
        encoding='latin-1',
        on_bad_lines='skip'
    )

    logger.info(f"Loaded {len(schools_df)} schools")

    # Filter to open schools only
    schools_df = schools_df[schools_df['EstablishmentStatus (name)'] == 'Open']
    logger.info(f"Filtered to {len(schools_df)} open schools")

    # Clean postcodes
    schools_df['Postcode'] = schools_df['Postcode'].str.strip().str.upper().str.replace(' ', '')

    # Load postcode to LSOA lookup
    logger.info(f"Loading postcode lookup from {postcode_lookup_file.name}...")

    # Try different encodings
    postcode_df = None
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            postcode_df = pd.read_csv(
                postcode_lookup_file,
                usecols=lambda x: 'pcd' in x.lower() or 'lsoa' in x.lower(),
                encoding=encoding,
                low_memory=False
            )
            if len(postcode_df) > 0:
                logger.info(f"Loaded with encoding: {encoding}")
                break
        except Exception as e:
            continue

    if postcode_df is None:
        logger.error("Failed to load postcode lookup")
        return False

    logger.info(f"Loaded {len(postcode_df)} postcodes")
    logger.info(f"Columns: {list(postcode_df.columns)}")

    # Standardize column names
    postcode_col = [col for col in postcode_df.columns if 'pcds' in col.lower() or col.lower() == 'pcd'][0]
    lsoa_col = [col for col in postcode_df.columns if 'lsoa21cd' in col.lower() or 'lsoa11cd' in col.lower()][0]

    postcode_df = postcode_df.rename(columns={postcode_col: 'postcode', lsoa_col: 'lsoa_code'})
    postcode_df['postcode'] = postcode_df['postcode'].str.strip().str.upper().str.replace(' ', '')

    # Merge schools with LSOAs
    logger.info("Merging schools with LSOA codes...")
    schools_with_lsoa = schools_df.merge(
        postcode_df[['postcode', 'lsoa_code']],
        left_on='Postcode',
        right_on='postcode',
        how='left'
    )

    match_rate = schools_with_lsoa['lsoa_code'].notna().sum() / len(schools_with_lsoa)
    logger.info(f"Matched {match_rate:.1%} of schools to LSOAs")

    # Create aggregated LSOA-level metrics
    logger.info("Creating LSOA-level school aggregates...")

    # Group by LSOA
    lsoa_aggregates = schools_with_lsoa[schools_with_lsoa['lsoa_code'].notna()].groupby('lsoa_code').agg({
        'URN': 'count',  # Total schools
        'PhaseOfEducation (name)': lambda x: (x == 'Primary').sum(),  # Primary schools
    }).rename(columns={
        'URN': 'total_schools',
        'PhaseOfEducation (name)': 'primary_schools'
    })

    # Add secondary schools count
    lsoa_aggregates['secondary_schools'] = schools_with_lsoa[
        (schools_with_lsoa['lsoa_code'].notna()) &
        (schools_with_lsoa['PhaseOfEducation (name)'].isin(['Secondary', 'Middle deemed secondary']))
    ].groupby('lsoa_code').size()

    lsoa_aggregates['secondary_schools'] = lsoa_aggregates['secondary_schools'].fillna(0).astype(int)

    # Reset index to make lsoa_code a column
    lsoa_aggregates = lsoa_aggregates.reset_index()

    logger.info(f"Created aggregates for {len(lsoa_aggregates)} LSOAs")
    logger.info(f"Columns: {list(lsoa_aggregates.columns)}")

    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    lsoa_aggregates.to_csv(output_file, index=False)
    logger.success(f"Saved school aggregates to {output_file}")
    logger.info(f"Total LSOAs with schools: {len(lsoa_aggregates)}")
    logger.info(f"Total schools mapped: {lsoa_aggregates['total_schools'].sum()}")

    return True

def main():
    """
    Main execution: Download lookup and create school-LSOA aggregates
    """
    logger.info("="*60)
    logger.info("SCHOOL TO LSOA LINKER")
    logger.info("="*60)

    schools_file = DATA_RAW / 'demographics' / 'schools_2024.csv'

    if not schools_file.exists():
        logger.error(f"Schools file not found: {schools_file}")
        logger.info("Please download from: https://get-information-schools.service.gov.uk/Downloads")
        return False

    # Use existing postcode lookup from boundaries folder
    postcode_lookup = DATA_RAW / 'boundaries' / 'postcode_lookup.csv'

    if not postcode_lookup.exists():
        logger.error(f"Postcode lookup not found: {postcode_lookup}")
        logger.info("Expected file: data/raw/boundaries/postcode_lookup.csv")
        return False

    logger.info(f"Using postcode lookup: {postcode_lookup.name}")

    # Create school-LSOA aggregates
    output_file = DATA_RAW / 'demographics' / 'schools_by_lsoa.csv'

    success = link_schools_to_lsoas(schools_file, postcode_lookup, output_file)

    if success:
        logger.success("✓ School-LSOA linking complete!")
        return True
    else:
        logger.error("✗ School-LSOA linking failed")
        return False

if __name__ == "__main__":
    main()
