"""
Data loading utilities for UK Bus Analytics Dashboard
Provides cached data loading functions for efficient dashboard performance
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List

# Data paths
DATA_BASE = Path('data/processed')
OUTPUTS_PATH = DATA_BASE / 'outputs'
REGIONS_PATH = DATA_BASE / 'regions'

# Regional mapping
REGION_CODES = {
    'Yorkshire and Humber': 'yorkshire',
    'West Midlands': 'west_midlands',
    'East Midlands': 'east_midlands',
    'North East England': 'north_east',
    'South West England': 'south_west',
    'Greater London': 'london',
    'South East England': 'south_east',
    'North West England': 'north_west',
    'East of England': 'east_england'
}


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_regional_summary() -> pd.DataFrame:
    """
    Load regional summary statistics

    Returns:
        DataFrame with regional metrics
    """
    file_path = OUTPUTS_PATH / 'regional_summary.csv'

    if not file_path.exists():
        st.error(f"Regional summary not found: {file_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading regional summary: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_regional_stops(region_name: str = None) -> pd.DataFrame:
    """
    Load stops data for a specific region or all regions

    Args:
        region_name: Name of region (e.g., 'Greater London') or None for all

    Returns:
        DataFrame with stops data
    """
    if region_name and region_name != 'All Regions':
        # Load specific region
        region_code = REGION_CODES.get(region_name)
        if not region_code:
            st.error(f"Unknown region: {region_name}")
            return pd.DataFrame()

        file_path = REGIONS_PATH / region_code / 'stops_processed.csv'

        if not file_path.exists():
            st.error(f"Region data not found: {file_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_path, low_memory=False)
            return df
        except Exception as e:
            st.error(f"Error loading region {region_name}: {e}")
            return pd.DataFrame()
    else:
        # Load all regions (use deduplicated file)
        file_path = OUTPUTS_PATH / 'all_stops_deduplicated.csv'

        if not file_path.exists():
            st.warning("All stops file not found, loading regions individually...")
            # Fallback: load and combine all regions
            all_stops = []
            for region_name, region_code in REGION_CODES.items():
                region_file = REGIONS_PATH / region_code / 'stops_processed.csv'
                if region_file.exists():
                    try:
                        df = pd.read_csv(region_file, low_memory=False)
                        df['region_name'] = region_name
                        df['region_code'] = region_code
                        all_stops.append(df)
                    except Exception as e:
                        st.warning(f"Could not load {region_name}: {e}")

            if all_stops:
                return pd.concat(all_stops, ignore_index=True)
            else:
                return pd.DataFrame()

        try:
            df = pd.read_csv(file_path, low_memory=False)
            return df
        except Exception as e:
            st.error(f"Error loading all stops: {e}")
            return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_routes_data(region_name: str = None) -> pd.DataFrame:
    """
    Load routes data for a specific region or all regions

    Args:
        region_name: Name of region or None for all

    Returns:
        DataFrame with routes data
    """
    all_routes = []

    if region_name and region_name != 'All Regions':
        region_code = REGION_CODES.get(region_name)
        if region_code:
            file_path = REGIONS_PATH / region_code / 'routes_processed.csv'
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    df['region_name'] = region_name
                    df['region_code'] = region_code
                    return df
                except Exception as e:
                    st.error(f"Error loading routes for {region_name}: {e}")
    else:
        # Load all regions
        for region_name, region_code in REGION_CODES.items():
            file_path = REGIONS_PATH / region_code / 'routes_processed.csv'
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    df['region_name'] = region_name
                    df['region_code'] = region_code
                    all_routes.append(df)
                except Exception as e:
                    st.warning(f"Could not load routes for {region_name}: {e}")

        if all_routes:
            return pd.concat(all_routes, ignore_index=True)

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_national_stats() -> Dict[str, any]:
    """
    Get national-level statistics

    Returns:
        Dict with national metrics
    """
    summary = load_regional_summary()

    if summary.empty:
        return {}

    stats = {
        'total_regions': len(summary),
        'total_stops': summary['total_stops'].sum(),
        'total_population': summary['population'].sum(),
        'total_routes': summary['routes_count'].sum(),
        'avg_coverage': summary['stops_per_1000'].mean(),
        'avg_routes_density': summary['routes_per_100k'].mean(),
        'best_coverage_region': summary.loc[summary['stops_per_1000'].idxmax(), 'region_name'],
        'worst_coverage_region': summary.loc[summary['stops_per_1000'].idxmin(), 'region_name']
    }

    return stats


def filter_by_urban_rural(df: pd.DataFrame, filter_value: str) -> pd.DataFrame:
    """
    Filter DataFrame by urban/rural classification

    Args:
        df: DataFrame with 'UrbanRural (name)' column
        filter_value: 'All', 'Urban', or 'Rural'

    Returns:
        Filtered DataFrame
    """
    if filter_value == 'All' or 'UrbanRural (name)' not in df.columns:
        return df

    if filter_value == 'Urban':
        # Filter for urban classifications
        urban_keywords = ['Urban', 'City', 'Town']
        mask = df['UrbanRural (name)'].str.contains('|'.join(urban_keywords), case=False, na=False)
        return df[mask]
    elif filter_value == 'Rural':
        # Filter for rural classifications
        rural_keywords = ['Rural', 'Village', 'Hamlet']
        mask = df['UrbanRural (name)'].str.contains('|'.join(rural_keywords), case=False, na=False)
        return df[mask]

    return df


def get_demographic_column_name(column_type: str) -> Optional[str]:
    """
    Get the actual column name for demographic data (handles variations)

    Args:
        column_type: Type of column ('imd', 'unemployment', 'car_ownership', etc.)

    Returns:
        Actual column name or None
    """
    column_mappings = {
        'imd': 'Index of Multiple Deprivation (IMD) Score',
        'unemployment': 'Unemployment rate - aged 16+',
        'car_ownership': 'pct_no_car',
        'population': 'All Ages',
        'elderly': 'Age 70+'
    }

    return column_mappings.get(column_type)


@st.cache_data(ttl=3600)
def load_route_geometries() -> pd.DataFrame:
    """
    Load route geometries (TransXChange data)

    Returns:
        DataFrame with route links
    """
    file_path = OUTPUTS_PATH / 'route_geometries.csv'

    if not file_path.exists():
        st.warning("Route geometries not found")
        return pd.DataFrame()

    try:
        # Only load first 100k rows for dashboard performance
        df = pd.read_csv(file_path, nrows=100000)
        return df
    except Exception as e:
        st.error(f"Error loading route geometries: {e}")
        return pd.DataFrame()
