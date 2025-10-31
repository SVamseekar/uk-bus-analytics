"""
Data Loader Utilities for UK Bus Analytics Dashboard
====================================================
Efficient data loading with caching for Streamlit dashboard

Author: UK Bus Analytics Platform
Date: 2025-10-29
"""

import pandas as pd
import streamlit as st
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'analytics' / 'outputs' / 'spatial'


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_lsoa_metrics():
    """
    Load LSOA-level metrics (comprehensive dataset)

    Returns:
        pd.DataFrame: LSOA metrics with demographics and coverage scores
    """
    file_path = DATA_DIR / 'lsoa_metrics.csv'
    df = pd.read_csv(file_path)
    return df


@st.cache_data(ttl=3600)
def load_spatial_answers():
    """
    Load pre-computed spatial analysis answers

    Returns:
        dict: Question answers with metadata
    """
    import json
    file_path = DATA_DIR / 'spatial_answers.json'
    with open(file_path, 'r') as f:
        answers = json.load(f)
    return answers


@st.cache_data
def get_summary_statistics(df: pd.DataFrame) -> dict:
    """
    Calculate summary statistics for dashboard KPIs

    Args:
        df: LSOA metrics dataframe

    Returns:
        dict: Summary statistics
    """
    return {
        'total_lsoas': len(df),
        'total_stops': int(df['bus_stops_count'].sum()),
        'total_routes': int(df['routes_count'].sum()),
        'avg_coverage': round(df['coverage_score'].mean(), 2),
        'avg_equity': round(df['equity_index'].mean(), 2),
        'service_gaps': int(df['service_gap'].sum()),
        'underserved_areas': int(df['underserved'].sum()),
        'underserved_population': int(df[df['underserved'] == 1]['population'].sum())
    }


def filter_lsoa_by_criteria(df: pd.DataFrame,
                             coverage_min: float = 0,
                             coverage_max: float = 100,
                             imd_deciles: list = None) -> pd.DataFrame:
    """
    Filter LSOA data by coverage and deprivation criteria

    Args:
        df: LSOA metrics dataframe
        coverage_min: Minimum coverage score
        coverage_max: Maximum coverage score
        imd_deciles: List of IMD deciles to include (1-10)

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    filtered = df.copy()

    # Coverage filter
    filtered = filtered[
        (filtered['coverage_score'] >= coverage_min) &
        (filtered['coverage_score'] <= coverage_max)
    ]

    # IMD filter
    if imd_deciles:
        filtered = filtered[filtered['imd_decile'].isin(imd_deciles)]

    return filtered
