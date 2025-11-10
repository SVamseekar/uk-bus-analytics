"""
Prepare aggregated datasets for ML models (Week 4)

Creates:
1. LSOA-level aggregated metrics for anomaly detection & coverage prediction
2. Route-level feature dataset for route clustering

Author: Week 4 ML Pipeline
Date: November 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Paths
DATA_BASE = Path('data/processed')
OUTPUTS_PATH = DATA_BASE / 'outputs'
ML_DATA_PATH = Path('data/ml_ready')
ML_DATA_PATH.mkdir(exist_ok=True)


def create_lsoa_aggregated_metrics():
    """
    Aggregate stops data to LSOA level for ML models

    Output columns:
    - lsoa_code, lsoa_name, region_code
    - stops_count, routes_count (unique)
    - population, imd_score, imd_decile
    - unemployment_rate, elderly_pct, car_ownership_pct
    - urban_rural_code, population_density
    - stops_per_1000, routes_per_100k
    """
    print("="*60)
    print("TASK 1: Creating LSOA-level aggregated metrics")
    print("="*60)

    # Load deduplicated stops
    print("\n[1/4] Loading stops data...")
    stops_file = OUTPUTS_PATH / 'all_stops_deduplicated.csv'
    stops = pd.read_csv(stops_file, low_memory=False)
    print(f"   Loaded {len(stops):,} stops")

    # Select relevant columns
    agg_columns = {
        'stop_id': 'count',  # Count stops
        'latitude': 'mean',  # Average location
        'longitude': 'mean',
        'total_population': 'first',  # Demographics (same within LSOA)
        'Index of Multiple Deprivation (IMD) Score': 'first',
        'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)': 'first',
        'UrbanRural (code)': 'first',
        'UrbanRural (name)': 'first',
        'pct_no_car': 'first',
        'age_0_15': 'first',
        'age_16_64': 'first',
        'age_65_plus': 'first',
        'region_code': 'first'
    }

    # Filter to columns that exist
    available_agg = {k: v for k, v in agg_columns.items() if k in stops.columns}

    print(f"\n[2/4] Aggregating to LSOA level...")
    print(f"   Using {len(available_agg)} aggregation columns")

    # Group by LSOA
    lsoa_metrics = stops.groupby('lsoa_code').agg(available_agg).reset_index()

    # Rename columns
    lsoa_metrics.rename(columns={
        'stop_id': 'stops_count',
        'Index of Multiple Deprivation (IMD) Score': 'imd_score',
        'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)': 'imd_decile',
        'UrbanRural (code)': 'urban_rural_code',
        'UrbanRural (name)': 'urban_rural_name',
        'pct_no_car': 'car_ownership_pct'
    }, inplace=True)

    # Calculate derived metrics
    print("\n[3/4] Computing derived metrics...")

    # Population density (approximate - would need LSOA area for accuracy)
    # For now, use relative density based on population
    lsoa_metrics['population_density_relative'] = lsoa_metrics['total_population'] / lsoa_metrics['total_population'].median()

    # Elderly percentage
    if 'age_65_plus' in lsoa_metrics.columns and 'total_population' in lsoa_metrics.columns:
        lsoa_metrics['elderly_pct'] = (lsoa_metrics['age_65_plus'] / lsoa_metrics['total_population']) * 100

    # Coverage metrics
    lsoa_metrics['stops_per_1000'] = (lsoa_metrics['stops_count'] / lsoa_metrics['total_population']) * 1000

    # Handle infinite/NaN values
    lsoa_metrics.replace([np.inf, -np.inf], np.nan, inplace=True)

    print(f"   Created {len(lsoa_metrics)} LSOA records")
    print(f"   Columns: {lsoa_metrics.columns.tolist()}")

    # Save
    output_file = ML_DATA_PATH / 'lsoa_metrics_for_ml.csv'
    lsoa_metrics.to_csv(output_file, index=False)
    print(f"\n[4/4] Saved to: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

    # Summary statistics
    print("\n" + "="*60)
    print("LSOA METRICS SUMMARY")
    print("="*60)
    print(f"Total LSOAs: {len(lsoa_metrics):,}")
    print(f"Total population: {lsoa_metrics['total_population'].sum():,.0f}")
    print(f"Total stops: {lsoa_metrics['stops_count'].sum():,.0f}")
    print(f"\nCoverage statistics:")
    print(f"  Mean stops/1000: {lsoa_metrics['stops_per_1000'].mean():.2f}")
    print(f"  Median stops/1000: {lsoa_metrics['stops_per_1000'].median():.2f}")
    print(f"  Min stops/1000: {lsoa_metrics['stops_per_1000'].min():.2f}")
    print(f"  Max stops/1000: {lsoa_metrics['stops_per_1000'].max():.2f}")

    return lsoa_metrics


def create_route_feature_dataset():
    """
    Create route-level features for route clustering

    Output columns:
    - route_id (pattern_id), line_name, operator (from source_file)
    - route_length_km, num_stops, trips_per_day, mileage_per_day
    - num_regions, regions_served, num_las
    - avg_imd_decile, avg_population, urban_rural_mix (from stops on route)
    """
    print("\n" + "="*60)
    print("TASK 2: Creating route-level feature dataset")
    print("="*60)

    print("\n[1/4] Loading route metrics...")
    routes_file = OUTPUTS_PATH / 'route_metrics.csv'
    routes = pd.read_csv(routes_file)
    print(f"   Loaded {len(routes):,} route patterns")

    print("\n[2/4] Loading stops data for route demographics...")
    stops_file = OUTPUTS_PATH / 'all_stops_deduplicated.csv'
    stops = pd.read_csv(stops_file, low_memory=False)

    # Create route_id from pattern_id + source_file
    routes['route_id'] = routes['source_file'].str.replace('.zip', '') + '_' + routes['pattern_id']

    # Extract operator name from source_file
    routes['operator'] = routes['source_file'].str.replace('.zip', '').str.replace('_', ' ')

    print(f"\n[3/4] Computing route statistics...")
    print(f"   Routes: {len(routes):,}")
    print(f"   Unique operators: {routes['operator'].nunique():,}")

    # Basic route metrics already in routes df:
    # - route_length_km, num_stops, trips_per_day, mileage_per_day
    # - num_regions, regions_served, num_las, las_served

    # Add frequency category
    routes['frequency_per_hour'] = routes['trips_per_day'] / 16  # Assume 16 hour service day
    routes['frequency_category'] = pd.cut(
        routes['frequency_per_hour'],
        bins=[0, 1, 2, 4, float('inf')],
        labels=['Low (<1/hr)', 'Moderate (1-2/hr)', 'Good (2-4/hr)', 'High (>4/hr)']
    )

    # Add length category
    routes['length_category'] = pd.cut(
        routes['route_length_km'],
        bins=[0, 5, 15, 30, float('inf')],
        labels=['Short (<5km)', 'Medium (5-15km)', 'Long (15-30km)', 'Very Long (>30km)']
    )

    print(f"\n[4/4] Route characteristics distribution:")
    print(f"\nFrequency categories:")
    print(routes['frequency_category'].value_counts().sort_index())
    print(f"\nLength categories:")
    print(routes['length_category'].value_counts().sort_index())

    # Save
    output_file = ML_DATA_PATH / 'routes_for_ml.csv'
    routes.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

    return routes


def main():
    """Run all ML data preparation tasks"""
    print("\n" + "="*70)
    print(" "*20 + "ML DATA PREPARATION PIPELINE")
    print(" "*25 + "Week 4 - Day 16")
    print("="*70)

    # Task 1: LSOA aggregation
    lsoa_data = create_lsoa_aggregated_metrics()

    # Task 2: Route features
    route_data = create_route_feature_dataset()

    print("\n" + "="*70)
    print("✅ ML DATA PREPARATION COMPLETE")
    print("="*70)
    print(f"\nOutputs saved to: {ML_DATA_PATH}/")
    print(f"  1. lsoa_metrics_for_ml.csv ({len(lsoa_data):,} rows)")
    print(f"  2. routes_for_ml.csv ({len(route_data):,} rows)")
    print("\nReady for ML model training!")
    print("="*70)


if __name__ == '__main__':
    main()
