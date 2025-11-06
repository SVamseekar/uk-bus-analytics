#!/usr/bin/env python3
"""
Download ONLY Census 2021 TS021 Ethnicity data from Nomis API
Standalone script to avoid re-downloading other datasets
"""
import requests
import pandas as pd
import time
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DEMOGRAPHICS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'demographics'
DEMOGRAPHICS_DIR.mkdir(parents=True, exist_ok=True)

def download_census_ethnicity():
    """
    Download Census 2021 TS021 - Ethnic Group
    LSOA level for England and Wales
    """
    print("="*60)
    print("Downloading Census 2021 TS021 (Ethnic Group) at LSOA level...")
    print("="*60)

    # Nomis API endpoint for Census 2021 TS021
    # Dataset code: NM_2107_1
    url = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2107_1.bulk.csv"

    params = {
        'geography': '1249902593...1249936345',  # All England LSOAs
        'date': 'latest',
        'c2021_eth_20': '0...19',  # All ethnic groups (0=Total, 1-19=specific groups)
        'measures': '20100',  # Observation values
        'select': 'geography_code,geography_name,c2021_eth_20_name,obs_value'
    }

    try:
        print("\nRequesting ethnicity data from Nomis API...")
        print("This may take 3-5 minutes (large dataset with ~650,000 rows)...")
        print("Please wait...\n")

        response = requests.get(url, params=params, timeout=600)
        response.raise_for_status()

        # Save raw response
        output_file = DEMOGRAPHICS_DIR / 'census_2021_ethnicity_lsoa.csv'

        print(f"Saving to: {output_file}")
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Check file size
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"✓ Downloaded {file_size_mb:.2f} MB")

        # Load and verify
        df = pd.read_csv(output_file)
        print(f"✓ Downloaded {len(df):,} records")
        print(f"  LSOAs: {df['GEOGRAPHY_CODE'].nunique():,}")
        print(f"  Ethnic groups: {df['C2021_ETH_20_NAME'].nunique()}")

        # Show sample ethnic groups
        print("\nEthnic groups in dataset:")
        for i, group in enumerate(df['C2021_ETH_20_NAME'].unique()[:10], 1):
            print(f"  {i}. {group}")
        if df['C2021_ETH_20_NAME'].nunique() > 10:
            print(f"  ... and {df['C2021_ETH_20_NAME'].nunique() - 10} more")

        return output_file

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download Census ethnicity data: {e}")
        print("\nYou may need to download manually from:")
        print("https://www.nomisweb.co.uk/datasets/c2021ts021")
        print("\nOr try bulk download from:")
        print("https://www.nomisweb.co.uk/output/census/2021/census2021-ts021.zip")
        return None


def process_ethnicity_data(ethnicity_file):
    """
    Process Census 2021 ethnicity data into pipeline-compatible format
    """
    if ethnicity_file is None or not ethnicity_file.exists():
        print("✗ Ethnicity file not found, cannot process")
        return None

    print("\n" + "="*60)
    print("Processing Census ethnicity data...")
    print("="*60)

    try:
        df = pd.read_csv(ethnicity_file, low_memory=False)

        # Rename columns to standard format
        df = df.rename(columns={
            'GEOGRAPHY_CODE': 'lsoa_code',
            'GEOGRAPHY_NAME': 'lsoa_name',
            'C2021_ETH_20_NAME': 'ethnic_group',
            'OBS_VALUE': 'population'
        })

        print(f"Loaded {len(df):,} records")
        print(f"Pivoting to wide format (one row per LSOA)...")

        # Pivot to wide format
        df_wide = df.pivot_table(
            index=['lsoa_code', 'lsoa_name'],
            columns='ethnic_group',
            values='population',
            aggfunc='sum'
        ).reset_index()

        print(f"✓ Pivoted to {len(df_wide):,} LSOAs with {len(df_wide.columns)} columns")

        # Calculate aggregate categories
        print("\nCreating aggregate ethnic categories...")

        # Get total population
        total_col = [col for col in df_wide.columns if 'Total' in col and 'usual residents' in col.lower()]
        if total_col:
            df_wide['total_population_ethnic'] = df_wide[total_col[0]]
            print(f"  ✓ Total population from: {total_col[0]}")

        # White
        white_cols = [col for col in df_wide.columns if 'White' in col and 'Total' not in col and 'Mixed' not in col]
        if white_cols:
            df_wide['ethnic_white'] = df_wide[white_cols].sum(axis=1)
            print(f"  ✓ White: {len(white_cols)} subcategories")

        # Asian/Asian British
        asian_cols = [col for col in df_wide.columns if any(x in col for x in ['Asian', 'Indian', 'Pakistani', 'Bangladeshi', 'Chinese'])]
        asian_cols = [col for col in asian_cols if 'White and Asian' not in col and 'Total' not in col]
        if asian_cols:
            df_wide['ethnic_asian'] = df_wide[asian_cols].sum(axis=1)
            print(f"  ✓ Asian: {len(asian_cols)} subcategories")

        # Black/African/Caribbean
        black_cols = [col for col in df_wide.columns if any(x in col for x in ['Black', 'African', 'Caribbean'])]
        black_cols = [col for col in black_cols if 'White and Black' not in col and 'Total' not in col]
        if black_cols:
            df_wide['ethnic_black'] = df_wide[black_cols].sum(axis=1)
            print(f"  ✓ Black: {len(black_cols)} subcategories")

        # Mixed/Multiple
        mixed_cols = [col for col in df_wide.columns if 'Mixed' in col or 'Multiple' in col or ('White and' in col and any(x in col for x in ['Black', 'Asian']))]
        mixed_cols = [col for col in mixed_cols if 'Total' not in col]
        if mixed_cols:
            df_wide['ethnic_mixed'] = df_wide[mixed_cols].sum(axis=1)
            print(f"  ✓ Mixed: {len(mixed_cols)} subcategories")

        # Other (Arab, Any other)
        other_cols = [col for col in df_wide.columns if ('Other' in col or 'Arab' in col) and 'Total' not in col]
        other_cols = [col for col in other_cols if not any(x in col for x in ['White', 'Mixed', 'Asian', 'Black'])]
        if other_cols:
            df_wide['ethnic_other'] = df_wide[other_cols].sum(axis=1)
            print(f"  ✓ Other: {len(other_cols)} subcategories")

        # Calculate BME (Black and Minority Ethnic) = Total - White
        if 'total_population_ethnic' in df_wide.columns and 'ethnic_white' in df_wide.columns:
            df_wide['ethnic_bme'] = df_wide['total_population_ethnic'] - df_wide['ethnic_white']
            df_wide['pct_bme'] = (df_wide['ethnic_bme'] / df_wide['total_population_ethnic']) * 100
            df_wide['pct_white'] = (df_wide['ethnic_white'] / df_wide['total_population_ethnic']) * 100
            print("  ✓ BME calculated (Total - White)")

        # Calculate percentages for each group
        for group in ['asian', 'black', 'mixed', 'other']:
            col_name = f'ethnic_{group}'
            if col_name in df_wide.columns and 'total_population_ethnic' in df_wide.columns:
                df_wide[f'pct_{group}'] = (df_wide[col_name] / df_wide['total_population_ethnic']) * 100

        output_file = DEMOGRAPHICS_DIR / 'ethnicity_lsoa_processed.csv'
        df_wide.to_csv(output_file, index=False)

        print(f"\n✓ Processed ethnicity data: {len(df_wide):,} LSOAs")
        print(f"✓ Saved to: {output_file}")

        # Summary stats
        if 'pct_bme' in df_wide.columns:
            print(f"\nSummary Statistics:")
            print(f"  Average BME %: {df_wide['pct_bme'].mean():.1f}%")
            print(f"  Range: {df_wide['pct_bme'].min():.1f}% - {df_wide['pct_bme'].max():.1f}%")
            print(f"  Median: {df_wide['pct_bme'].median():.1f}%")

        return output_file

    except Exception as e:
        print(f"✗ Failed to process ethnicity data: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    ethnicity_file = download_census_ethnicity()
    if ethnicity_file:
        time.sleep(1)
        processed_file = process_ethnicity_data(ethnicity_file)

        if processed_file:
            print("\n" + "="*60)
            print("✓ SUCCESS: Ethnicity data ready for F37 implementation")
            print("="*60)
        else:
            print("\n✗ Processing failed")
    else:
        print("\n✗ Download failed")
