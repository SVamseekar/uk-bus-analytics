#!/usr/bin/env python3
"""
Download Census 2021 TS021 Ethnicity data via bulk ZIP from ONS
Alternative to Nomis API (which may have rate limits)
"""
import requests
import pandas as pd
import zipfile
from pathlib import Path
import shutil

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DEMOGRAPHICS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'demographics'
DEMOGRAPHICS_DIR.mkdir(parents=True, exist_ok=True)

def download_bulk_zip():
    """Download bulk ZIP of TS021 from ONS"""
    print("="*60)
    print("Downloading Census 2021 TS021 (Ethnic Group) bulk ZIP...")
    print("="*60)

    # Direct download from ONS bulk data site
    url = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts021.zip"

    zip_file = DEMOGRAPHICS_DIR / 'census2021-ts021.zip'

    try:
        print(f"\nDownloading from: {url}")
        print("This may take 2-3 minutes (15-20 MB ZIP file)...\n")

        response = requests.get(url, timeout=300, stream=True)
        response.raise_for_status()

        with open(zip_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"✓ Downloaded {file_size_mb:.2f} MB to {zip_file}")

        return zip_file

    except requests.exceptions.RequestException as e:
        print(f"✗ Download failed: {e}")
        return None


def extract_lsoa_file(zip_file):
    """Extract LSOA-level data from ZIP"""
    if not zip_file.exists():
        print("✗ ZIP file not found")
        return None

    print("\nExtracting LSOA-level file from ZIP...")

    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # List contents
            file_list = zip_ref.namelist()
            print(f"ZIP contains {len(file_list)} files")

            # Find LSOA file (usually census2021-ts021-lsoa.csv)
            lsoa_files = [f for f in file_list if 'lsoa' in f.lower() and f.endswith('.csv')]

            if not lsoa_files:
                print("✗ No LSOA file found in ZIP")
                print("Files in ZIP:")
                for f in file_list[:10]:
                    print(f"  - {f}")
                return None

            lsoa_file = lsoa_files[0]
            print(f"Found LSOA file: {lsoa_file}")

            # Extract
            zip_ref.extract(lsoa_file, DEMOGRAPHICS_DIR)

            extracted_path = DEMOGRAPHICS_DIR / lsoa_file
            target_path = DEMOGRAPHICS_DIR / 'census_2021_ethnicity_lsoa.csv'

            # Move to standard name
            if extracted_path != target_path:
                shutil.move(str(extracted_path), str(target_path))

            file_size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"✓ Extracted {file_size_mb:.2f} MB to {target_path}")

            return target_path

    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_ethnicity_data(ethnicity_file):
    """Process Census 2021 ethnicity data"""
    if ethnicity_file is None or not ethnicity_file.exists():
        print("✗ Ethnicity file not found")
        return None

    print("\n" + "="*60)
    print("Processing Census ethnicity data...")
    print("="*60)

    try:
        # Read first few rows to check structure
        print("\nReading file (checking structure)...")
        df_sample = pd.read_csv(ethnicity_file, nrows=5)
        print(f"Columns: {list(df_sample.columns)}")

        # Read full file
        print(f"\nReading full dataset...")
        df = pd.read_csv(ethnicity_file, low_memory=False)
        print(f"✓ Loaded {len(df):,} records")

        # Column mapping (flexible to handle different naming conventions)
        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'geography' in col_lower and 'code' in col_lower:
                col_map['lsoa_code'] = col
            elif 'geography' in col_lower and ('name' in col_lower or col_lower == 'geography'):
                col_map['lsoa_name'] = col
            elif 'eth' in col_lower and 'name' in col_lower:
                col_map['ethnic_group'] = col
            elif col_lower in ['obs_value', 'observation']:
                col_map['population'] = col

        print(f"Column mapping: {col_map}")

        # Rename
        df = df.rename(columns={v: k for k, v in col_map.items()})

        # Check we have required columns
        required = ['lsoa_code', 'ethnic_group', 'population']
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"✗ Missing required columns: {missing}")
            print(f"Available columns: {list(df.columns)}")
            return None

        print(f"LSOAs: {df['lsoa_code'].nunique():,}")
        print(f"Ethnic groups: {df['ethnic_group'].nunique()}")

        # Show ethnic groups
        print("\nEthnic groups in dataset:")
        for i, group in enumerate(sorted(df['ethnic_group'].unique()), 1):
            print(f"  {i:2d}. {group}")

        # Pivot to wide format
        print(f"\nPivoting to wide format...")
        df_wide = df.pivot_table(
            index='lsoa_code',
            columns='ethnic_group',
            values='population',
            aggfunc='sum'
        ).reset_index()

        if 'lsoa_name' in df.columns:
            lsoa_names = df[['lsoa_code', 'lsoa_name']].drop_duplicates()
            df_wide = df_wide.merge(lsoa_names, on='lsoa_code', how='left')

        print(f"✓ Pivoted to {len(df_wide):,} LSOAs with {len(df_wide.columns)} columns")

        # Create aggregate categories
        print("\nCreating aggregate ethnic categories...")

        # Total population
        total_cols = [col for col in df_wide.columns if 'total' in col.lower() and 'usual' in col.lower()]
        if not total_cols:
            total_cols = [col for col in df_wide.columns if col.startswith('Total')]
        if total_cols:
            df_wide['total_population_ethnic'] = df_wide[total_cols[0]]
            print(f"  ✓ Total from: {total_cols[0]}")

        # White
        white_cols = [col for col in df_wide.columns
                      if 'white' in col.lower()
                      and 'total' not in col.lower()
                      and 'mixed' not in col.lower()
                      and 'and' not in col.lower()]
        if white_cols:
            df_wide['ethnic_white'] = df_wide[white_cols].sum(axis=1)
            print(f"  ✓ White: {len(white_cols)} categories")

        # Asian
        asian_cols = [col for col in df_wide.columns
                      if any(x in col.lower() for x in ['asian', 'indian', 'pakistani', 'bangladeshi', 'chinese'])
                      and 'white and asian' not in col.lower()
                      and 'total' not in col.lower()]
        if asian_cols:
            df_wide['ethnic_asian'] = df_wide[asian_cols].sum(axis=1)
            print(f"  ✓ Asian: {len(asian_cols)} categories")

        # Black
        black_cols = [col for col in df_wide.columns
                      if any(x in col.lower() for x in ['black', 'african', 'caribbean'])
                      and 'white and black' not in col.lower()
                      and 'total' not in col.lower()]
        if black_cols:
            df_wide['ethnic_black'] = df_wide[black_cols].sum(axis=1)
            print(f"  ✓ Black: {len(black_cols)} categories")

        # Mixed
        mixed_cols = [col for col in df_wide.columns
                      if 'mixed' in col.lower() or 'multiple' in col.lower()
                      or ('white and' in col.lower() and any(x in col.lower() for x in ['black', 'asian']))]
        mixed_cols = [col for col in mixed_cols if 'total' not in col.lower()]
        if mixed_cols:
            df_wide['ethnic_mixed'] = df_wide[mixed_cols].sum(axis=1)
            print(f"  ✓ Mixed: {len(mixed_cols)} categories")

        # Other
        other_cols = [col for col in df_wide.columns
                      if ('other' in col.lower() or 'arab' in col.lower())
                      and 'total' not in col.lower()
                      and not any(x in col.lower() for x in ['white', 'asian', 'black', 'mixed'])]
        if other_cols:
            df_wide['ethnic_other'] = df_wide[other_cols].sum(axis=1)
            print(f"  ✓ Other: {len(other_cols)} categories")

        # Calculate BME and percentages
        if 'total_population_ethnic' in df_wide.columns and 'ethnic_white' in df_wide.columns:
            df_wide['ethnic_bme'] = df_wide['total_population_ethnic'] - df_wide['ethnic_white']
            df_wide['pct_bme'] = (df_wide['ethnic_bme'] / df_wide['total_population_ethnic']) * 100
            df_wide['pct_white'] = (df_wide['ethnic_white'] / df_wide['total_population_ethnic']) * 100
            print("  ✓ BME calculated")

        for group in ['asian', 'black', 'mixed', 'other']:
            col_name = f'ethnic_{group}'
            if col_name in df_wide.columns and 'total_population_ethnic' in df_wide.columns:
                df_wide[f'pct_{group}'] = (df_wide[col_name] / df_wide['total_population_ethnic']) * 100

        output_file = DEMOGRAPHICS_DIR / 'ethnicity_lsoa_processed.csv'
        df_wide.to_csv(output_file, index=False)

        print(f"\n✓ Saved to: {output_file}")
        print(f"  LSOAs: {len(df_wide):,}")
        print(f"  Columns: {len(df_wide.columns)}")

        if 'pct_bme' in df_wide.columns:
            print(f"\nSummary:")
            print(f"  Average BME %: {df_wide['pct_bme'].mean():.1f}%")
            print(f"  Range: {df_wide['pct_bme'].min():.1f}% - {df_wide['pct_bme'].max():.1f}%")
            print(f"  Median: {df_wide['pct_bme'].median():.1f}%")

        return output_file

    except Exception as e:
        print(f"✗ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Check if already processed
    processed_file = DEMOGRAPHICS_DIR / 'ethnicity_lsoa_processed.csv'
    if processed_file.exists():
        print(f"✓ Processed file already exists: {processed_file}")
        print("Delete it if you want to re-download.\n")

    # Download
    zip_file = download_bulk_zip()

    if zip_file:
        # Extract
        ethnicity_file = extract_lsoa_file(zip_file)

        if ethnicity_file:
            # Process
            processed = process_ethnicity_data(ethnicity_file)

            if processed:
                print("\n" + "="*60)
                print("✓ SUCCESS: Ethnicity data ready for F37")
                print("="*60)
                print(f"\nProcessed file: {processed}")
            else:
                print("\n✗ Processing failed")
        else:
            print("\n✗ Extraction failed")
    else:
        print("\n✗ Download failed")
