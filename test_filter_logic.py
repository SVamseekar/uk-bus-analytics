"""Test Category C filter logic"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import streamlit as st

# Suppress streamlit warnings
import warnings
warnings.filterwarnings('ignore')

from dashboard.utils.data_loader import load_route_metrics, load_regional_stops, REGION_CODES

print("Loading route metrics...")
routes_df = load_route_metrics()
print(f"Loaded {len(routes_df)} routes")
print(f"Columns: {list(routes_df.columns)}")

# Check for list columns
list_cols = [col for col in routes_df.columns if col.endswith('_list')]
print(f"\nList columns found: {list_cols}")

# Drop them
if list_cols:
    routes_df = routes_df.drop(columns=list_cols)
    print(f"Dropped list columns. Remaining: {list(routes_df.columns)}")

# Test creating route_regions_df
print("\nCreating route_regions_df...")
route_region_pairs = []
for idx, row in routes_df.head(10).iterrows():  # Just first 10 for testing
    if pd.notna(row['regions_served']) and row['regions_served']:
        regions = row['regions_served'].split(',')
        for region_code in regions:
            route_region_pairs.append({
                'pattern_id': row['pattern_id'],
                'region_code': region_code.strip(),
            })

route_regions_df = pd.DataFrame(route_region_pairs)
print(f"Created {len(route_regions_df)} route-region pairs")

# Map codes to names
code_to_name = {v: k for k, v in REGION_CODES.items()}
print(f"\nCode to name mapping: {code_to_name}")

route_regions_df['region_name'] = route_regions_df['region_code'].map(code_to_name)
print(f"\nSample route_regions_df:")
print(route_regions_df.head())

# Check for unmapped regions
unmapped = route_regions_df[route_regions_df['region_name'].isna()]
if len(unmapped) > 0:
    print(f"\n⚠️ WARNING: {len(unmapped)} unmapped region codes:")
    print(unmapped['region_code'].unique())

print("\n✅ Test complete")
