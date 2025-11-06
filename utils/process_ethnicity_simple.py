#!/usr/bin/env python3
"""
Process Census 2021 TS021 ethnicity data
Data is already in wide format (one row per LSOA)
"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DEMOGRAPHICS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'demographics'

def process_ethnicity_wide_format():
    """Process ethnicity data that's already in wide format"""

    input_file = DEMOGRAPHICS_DIR / 'census_2021_ethnicity_lsoa.csv'
    if not input_file.exists():
        print(f"✗ File not found: {input_file}")
        return None

    print("="*60)
    print("Processing Census 2021 TS021 Ethnicity (Wide Format)")
    print("="*60)

    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df):,} LSOAs")

    # Rename geography columns
    df = df.rename(columns={
        'geography': 'lsoa_name',
        'geography code': 'lsoa_code'
    })

    # Extract total population
    total_col = 'Ethnic group: Total: All usual residents'
    df['total_population_ethnic'] = df[total_col]

    # White - all subcategories
    white_cols = [col for col in df.columns if col.startswith('Ethnic group: White:')]
    df['ethnic_white'] = df[white_cols].sum(axis=1)
    print(f"  ✓ White: {len(white_cols)} subcategories")

    # Asian - all subcategories
    asian_cols = [col for col in df.columns
                  if col.startswith('Ethnic group: Asian') and ':' in col]
    df['ethnic_asian'] = df[asian_cols].sum(axis=1)
    print(f"  ✓ Asian: {len(asian_cols)} subcategories")

    # Black - all subcategories
    black_cols = [col for col in df.columns
                  if col.startswith('Ethnic group: Black') and ':' in col]
    df['ethnic_black'] = df[black_cols].sum(axis=1)
    print(f"  ✓ Black: {len(black_cols)} subcategories")

    # Mixed - all subcategories
    mixed_cols = [col for col in df.columns
                  if col.startswith('Ethnic group: Mixed') and ':' in col]
    df['ethnic_mixed'] = df[mixed_cols].sum(axis=1)
    print(f"  ✓ Mixed: {len(mixed_cols)} subcategories")

    # Other - all subcategories
    other_cols = [col for col in df.columns
                  if col.startswith('Ethnic group: Other ethnic group:')]
    df['ethnic_other'] = df[other_cols].sum(axis=1)
    print(f"  ✓ Other: {len(other_cols)} subcategories")

    # Calculate BME (Total - White)
    df['ethnic_bme'] = df['total_population_ethnic'] - df['ethnic_white']

    # Calculate percentages
    df['pct_white'] = (df['ethnic_white'] / df['total_population_ethnic']) * 100
    df['pct_bme'] = (df['ethnic_bme'] / df['total_population_ethnic']) * 100
    df['pct_asian'] = (df['ethnic_asian'] / df['total_population_ethnic']) * 100
    df['pct_black'] = (df['ethnic_black'] / df['total_population_ethnic']) * 100
    df['pct_mixed'] = (df['ethnic_mixed'] / df['total_population_ethnic']) * 100
    df['pct_other'] = (df['ethnic_other'] / df['total_population_ethnic']) * 100

    # Keep only processed columns
    output_cols = [
        'lsoa_code', 'lsoa_name',
        'total_population_ethnic',
        'ethnic_white', 'ethnic_bme', 'ethnic_asian', 'ethnic_black', 'ethnic_mixed', 'ethnic_other',
        'pct_white', 'pct_bme', 'pct_asian', 'pct_black', 'pct_mixed', 'pct_other'
    ]

    df_out = df[output_cols].copy()

    output_file = DEMOGRAPHICS_DIR / 'ethnicity_lsoa_processed.csv'
    df_out.to_csv(output_file, index=False)

    print(f"\n✓ Saved to: {output_file}")
    print(f"  LSOAs: {len(df_out):,}")
    print(f"  Columns: {len(df_out.columns)}")

    print(f"\nSummary Statistics:")
    print(f"  Average BME %: {df_out['pct_bme'].mean():.1f}%")
    print(f"  Range: {df_out['pct_bme'].min():.1f}% - {df_out['pct_bme'].max():.1f}%")
    print(f"  Median: {df_out['pct_bme'].median():.1f}%")

    print(f"\nTop 5 highest BME %:")
    top_bme = df_out.nlargest(5, 'pct_bme')[['lsoa_name', 'pct_bme']]
    for idx, row in top_bme.iterrows():
        print(f"  {row['lsoa_name']}: {row['pct_bme']:.1f}%")

    return output_file


if __name__ == "__main__":
    result = process_ethnicity_wide_format()
    if result:
        print("\n" + "="*60)
        print("✓ SUCCESS: Ethnicity data ready for F37")
        print("="*60)
    else:
        print("\n✗ FAILED")
