#!/usr/bin/env python3
"""
Generate regional summary statistics for dashboard
Reads all regional stops_processed.csv files and creates aggregated metrics
"""

import pandas as pd
import json
from pathlib import Path
from loguru import logger

# Regional mapping
REGIONS = {
    'yorkshire': 'Yorkshire and Humber',
    'west_midlands': 'West Midlands',
    'east_midlands': 'East Midlands',
    'north_east': 'North East England',
    'south_west': 'South West England',
    'london': 'Greater London',
    'south_east': 'South East England',
    'north_west': 'North West England',
    'east_england': 'East of England'
}

# ONS Official Region Codes (for GeoJSON joining)
ONS_REGION_CODES = {
    'yorkshire': 'E12000003',
    'west_midlands': 'E12000005',
    'east_midlands': 'E12000004',
    'north_east': 'E12000001',
    'south_west': 'E12000009',
    'london': 'E12000007',
    'south_east': 'E12000008',
    'north_west': 'E12000002',
    'east_england': 'E12000006'
}

def load_regional_data():
    """Load all regional processed data"""
    base_path = Path('data/processed/regions')
    regional_data = {}

    for region_code, region_name in REGIONS.items():
        file_path = base_path / region_code / 'stops_processed.csv'

        if file_path.exists():
            logger.info(f"Loading: {region_name} ({region_code})")
            try:
                # Read with low_memory=False to avoid dtype warnings
                df = pd.read_csv(file_path, low_memory=False)
                regional_data[region_code] = {
                    'name': region_name,
                    'data': df
                }
                logger.success(f"✓ {region_name}: {len(df):,} stops")
            except Exception as e:
                logger.error(f"✗ Failed to load {region_name}: {e}")
        else:
            logger.warning(f"⚠ File not found: {file_path}")

    return regional_data

def calculate_regional_metrics(regional_data):
    """Calculate summary metrics for each region"""
    summaries = []

    for region_code, region_info in regional_data.items():
        df = region_info['data']
        region_name = region_info['name']

        logger.info(f"Calculating metrics for {region_name}...")

        # Basic counts
        total_stops = len(df)
        unique_lsoas = df['lsoa_code'].nunique() if 'lsoa_code' in df.columns else 0

        # Population (from LSOA data if available)
        # Sum population across unique LSOAs to avoid double counting
        if 'lsoa_code' in df.columns:
            lsoa_df = df[['lsoa_code']].drop_duplicates()

            # Try to get population from various sources
            population = 0
            if 'population' in df.columns:
                pop_df = df[['lsoa_code', 'population']].drop_duplicates()
                population = pop_df['population'].sum()
            elif 'All Ages' in df.columns:
                pop_df = df[['lsoa_code', 'All Ages']].drop_duplicates()
                population = pop_df['All Ages'].sum()

            if population == 0:
                # Estimate based on LSOA count (avg LSOA ~1650 people)
                population = unique_lsoas * 1650
        else:
            population = 0

        # Calculate stops per 1000 population
        stops_per_1000 = (total_stops / population * 1000) if population > 0 else 0

        # Routes count (from processing summary if available)
        routes_count = 0
        routes_file = Path(f'data/processed/regions/{region_code}/routes_processed.csv')
        if routes_file.exists():
            try:
                routes_df = pd.read_csv(routes_file)
                routes_count = len(routes_df)
            except:
                pass

        # Routes per 100k population
        routes_per_100k = (routes_count / population * 100000) if population > 0 else 0

        # Demographic metrics (if available)
        avg_imd = df['Index of Multiple Deprivation (IMD) Score'].mean() if 'Index of Multiple Deprivation (IMD) Score' in df.columns else None

        # Calculate unemployment rate from claimants and working-age population
        avg_unemployment = None
        if 'lsoa_code' in df.columns and 'total_claimants' in df.columns and 'age_16_64' in df.columns:
            # Get unique LSOAs to avoid double counting
            lsoa_unemp_df = df[['lsoa_code', 'total_claimants', 'age_16_64']].drop_duplicates(subset=['lsoa_code'])
            lsoa_unemp_df = lsoa_unemp_df.dropna(subset=['total_claimants', 'age_16_64'])
            lsoa_unemp_df = lsoa_unemp_df[lsoa_unemp_df['age_16_64'] >= 100]  # Filter out very small populations

            if len(lsoa_unemp_df) > 0:
                total_claimants = lsoa_unemp_df['total_claimants'].sum()
                total_working_age = lsoa_unemp_df['age_16_64'].sum()
                avg_unemployment = (total_claimants / total_working_age) * 100 if total_working_age > 0 else None

        pct_no_car = df['pct_no_car'].mean() if 'pct_no_car' in df.columns else None

        # Create summary record
        summary = {
            'region_code': region_code,
            'ons_code': ONS_REGION_CODES.get(region_code),
            'region_name': region_name,
            'total_stops': int(total_stops),
            'unique_lsoas': int(unique_lsoas),
            'population': int(population),
            'stops_per_1000': round(stops_per_1000, 2),
            'routes_count': int(routes_count),
            'routes_per_100k': round(routes_per_100k, 2),
            'avg_imd_score': round(avg_imd, 2) if avg_imd else None,
            'avg_unemployment_rate': round(avg_unemployment, 2) if avg_unemployment else None,
            'pct_no_car': round(pct_no_car, 2) if pct_no_car else None
        }

        summaries.append(summary)

        logger.success(f"✓ {region_name}: {total_stops:,} stops, {population:,} pop, {stops_per_1000:.1f} stops/1000")

    return pd.DataFrame(summaries)

def add_rankings(summary_df):
    """Add ranking columns for key metrics"""
    # Rank by stops per 1000 (higher is better)
    summary_df['coverage_rank'] = summary_df['stops_per_1000'].rank(ascending=False, method='min').astype(int)

    # Rank by routes per 100k (higher is better)
    summary_df['routes_rank'] = summary_df['routes_per_100k'].rank(ascending=False, method='min').astype(int)

    return summary_df

def main():
    logger.info("=" * 60)
    logger.info("CREATING REGIONAL SUMMARY FOR DASHBOARD")
    logger.info("=" * 60)

    # Load regional data
    regional_data = load_regional_data()

    if not regional_data:
        logger.error("No regional data loaded! Check file paths.")
        return

    # Calculate metrics
    summary_df = calculate_regional_metrics(regional_data)

    # Add rankings
    summary_df = add_rankings(summary_df)

    # Calculate national averages
    national_avg_coverage = summary_df['stops_per_1000'].mean()
    national_avg_routes = summary_df['routes_per_100k'].mean()

    logger.info("")
    logger.info("=" * 60)
    logger.info("NATIONAL STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total Regions: {len(summary_df)}")
    logger.info(f"Total Stops: {summary_df['total_stops'].sum():,}")
    logger.info(f"Total Population: {summary_df['population'].sum():,}")
    logger.info(f"Total Routes: {summary_df['routes_count'].sum():,}")
    logger.info(f"Avg Coverage: {national_avg_coverage:.2f} stops per 1,000 population")
    logger.info(f"Avg Routes: {national_avg_routes:.2f} routes per 100,000 population")

    # Save summary
    output_path = Path('data/processed/outputs/regional_summary.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)

    logger.success(f"✓ Saved regional summary: {output_path}")

    # Display summary table
    logger.info("")
    logger.info("=" * 60)
    logger.info("REGIONAL SUMMARY TABLE")
    logger.info("=" * 60)
    print(summary_df[['region_name', 'total_stops', 'population', 'stops_per_1000',
                      'routes_count', 'routes_per_100k', 'coverage_rank']].to_string(index=False))

    return summary_df

if __name__ == '__main__':
    main()
