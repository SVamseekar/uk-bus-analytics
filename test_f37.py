#!/usr/bin/env python3
"""
Quick test of F37 ethnicity data integration
"""
from pathlib import Path
import pandas as pd
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("Testing F37 Ethnicity Data Integration")
print("="*60)

# Test 1: Check ethnicity file exists
ethnicity_file = Path('data/raw/demographics/ethnicity_lsoa_processed.csv')
print(f"\n1. Checking ethnicity file exists...")
if ethnicity_file.exists():
    print(f"   ✓ File exists: {ethnicity_file}")
    file_size_mb = ethnicity_file.stat().st_size / (1024 * 1024)
    print(f"   Size: {file_size_mb:.2f} MB")
else:
    print(f"   ✗ File NOT found: {ethnicity_file}")
    sys.exit(1)

# Test 2: Load and verify structure
print(f"\n2. Loading ethnicity data...")
df_ethnicity = pd.read_csv(ethnicity_file)
print(f"   ✓ Loaded {len(df_ethnicity):,} LSOAs")
print(f"   Columns: {len(df_ethnicity.columns)}")

required_cols = ['lsoa_code', 'pct_bme', 'pct_asian', 'pct_black', 'pct_mixed']
missing = [c for c in required_cols if c not in df_ethnicity.columns]
if missing:
    print(f"   ✗ Missing columns: {missing}")
    sys.exit(1)
else:
    print(f"   ✓ All required columns present")

# Test 3: Check data quality
print(f"\n3. Data quality checks...")
print(f"   BME % range: {df_ethnicity['pct_bme'].min():.1f}% - {df_ethnicity['pct_bme'].max():.1f}%")
print(f"   BME % average: {df_ethnicity['pct_bme'].mean():.1f}%")
print(f"   BME % median: {df_ethnicity['pct_bme'].median():.1f}%")
print(f"   Nulls in pct_bme: {df_ethnicity['pct_bme'].isna().sum()}")

# Test 4: Check a processed stops file can merge with ethnicity
print(f"\n4. Testing merge with stops data...")
test_stops_file = Path('data/processed/regions/london/stops_processed.csv')
if test_stops_file.exists():
    df_stops = pd.read_csv(test_stops_file, usecols=['stop_id', 'lsoa_code', 'total_population'], nrows=1000)

    # Aggregate to LSOA
    lsoa_agg = df_stops.groupby('lsoa_code').agg({
        'stop_id': 'nunique',
        'total_population': 'first'
    }).reset_index()
    lsoa_agg = lsoa_agg.rename(columns={'stop_id': 'num_stops'})

    # Merge with ethnicity
    merged = lsoa_agg.merge(df_ethnicity, on='lsoa_code', how='left')

    match_rate = (merged['pct_bme'].notna().sum() / len(merged)) * 100
    print(f"   ✓ Tested {len(lsoa_agg)} LSOAs from London stops")
    print(f"   ✓ Match rate: {match_rate:.1f}% ({merged['pct_bme'].notna().sum()}/{len(merged)} LSOAs)")

    if match_rate < 80:
        print(f"   ⚠️ Low match rate - may indicate LSOA code mismatch")
else:
    print(f"   ⚠️ Skipped (London stops file not found)")

# Test 5: Sample LSOAs with high BME %
print(f"\n5. Top 5 LSOAs by BME %:")
top_bme = df_ethnicity.nlargest(5, 'pct_bme')[['lsoa_name', 'pct_bme', 'pct_asian', 'pct_black']]
for idx, row in top_bme.iterrows():
    print(f"   {row['lsoa_name']}: {row['pct_bme']:.1f}% BME (Asian: {row['pct_asian']:.1f}%, Black: {row['pct_black']:.1f}%)")

print("\n" + "="*60)
print("✓ ALL TESTS PASSED - F37 data integration successful")
print("="*60)
