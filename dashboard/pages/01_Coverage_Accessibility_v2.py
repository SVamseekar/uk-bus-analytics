"""
Coverage & Accessibility Analysis (Insight Engine Version)
Professional consulting-style analysis powered by dynamic narrative generation

This version uses the InsightEngine for 100% dynamic, context-aware narratives
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.category_template import render_category_page
from dashboard.utils.data_loader import load_regional_summary
from dashboard.utils.insight_engine import InsightEngine, MetricConfig

# Initialize engine
ENGINE = InsightEngine()


# ============================================================================
# SECTION 1: Regional Route Density Analysis (A1)
# ============================================================================

def load_route_density_data(region_filter: str, urban_rural_filter: str) -> pd.DataFrame:
    """Load routes per capita data"""
    df = load_regional_summary()

    if df.empty:
        return df

    if region_filter and region_filter != 'All Regions':
        df = df[df['region_name'] == region_filter]

    return df


def create_route_density_viz(data: pd.DataFrame) -> go.Figure:
    """Create professional bar chart"""
    if data.empty:
        return None

    data_sorted = data.sort_values('routes_per_100k', ascending=False)

    fig = px.bar(
        data_sorted,
        x='routes_per_100k',
        y='region_name',
        orientation='h',
        title='Bus Routes per 100,000 Population',
        labels={'routes_per_100k': 'Routes per 100,000 Population', 'region_name': ''},
        color='routes_per_100k',
        color_continuous_scale='Greens',
        text='routes_per_100k'
    )

    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_title="Routes per 100,000 Population",
        yaxis_title="",
        font=dict(size=12, family="Inter, Segoe UI, Helvetica Neue, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    national_avg = data['routes_per_100k'].mean()
    fig.add_vline(
        x=national_avg,
        line_dash="dash",
        line_color="#6b7280",
        annotation_text=f"National Average: {national_avg:.1f}",
        annotation_position="top"
    )

    return fig


def generate_route_density_narrative(data: pd.DataFrame) -> dict:
    """Generate dynamic narrative using InsightEngine"""

    # Define metric configuration
    config = MetricConfig(
        id='routes_per_100k',
        groupby='region_name',
        value_col='routes_per_100k',
        unit='routes per 100,000 population',
        sources=['NaPTAN October 2025', 'BODS TransXChange', 'ONS Census 2021', 'TAG 2024'],
        rules=['ranking', 'single_region_positioning', 'variation', 'gap_to_investment'],
        min_n=1,
        min_groups=1
    )

    # Determine active filters
    filters = {}
    if len(data) == 1 and 'region_name' in data.columns:
        filters['region'] = data.iloc[0]['region_name']

    # Generate narrative
    result = ENGINE.run(data, config, filters)

    return {
        'summary': result['summary'],
        'key_finding': result['key_finding'],
        'recommendation': result['recommendation'],
        'investment': result['investment'],
        'related_links': [
            {'text': 'Route Optimization Scenarios', 'url': '/Route_Optimization'},
            {'text': 'Economic Impact & BCR Calculator', 'url': '/Economic_Impact_BCR'}
        ]
    }


# ============================================================================
# SECTION 2: Service Coverage Assessment (A2)
# ============================================================================

def load_coverage_assessment_data(region_filter: str, urban_rural_filter: str) -> pd.DataFrame:
    """Load stops per 1000 residents data"""
    df = load_regional_summary()

    if df.empty:
        return df

    if region_filter and region_filter != 'All Regions':
        df = df[df['region_name'] == region_filter]

    return df


def create_coverage_assessment_viz(data: pd.DataFrame) -> go.Figure:
    """Create professional chart"""
    if data.empty:
        return None

    data_sorted = data.sort_values('stops_per_1000', ascending=True)

    fig = px.bar(
        data_sorted,
        x='stops_per_1000',
        y='region_name',
        orientation='h',
        title='Bus Stops per 1,000 Residents',
        labels={'stops_per_1000': 'Stops per 1,000 Residents', 'region_name': ''},
        color='stops_per_1000',
        color_continuous_scale='RdYlGn',
        text='stops_per_1000'
    )

    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_title="Stops per 1,000 Residents",
        yaxis_title="",
        font=dict(size=12, family="Inter, Segoe UI, Helvetica Neue, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    national_avg = data['stops_per_1000'].mean()
    fig.add_vline(
        x=national_avg,
        line_dash="dash",
        line_color="#6b7280",
        annotation_text=f"National Average: {national_avg:.1f}",
        annotation_position="top"
    )

    return fig


def generate_coverage_assessment_narrative(data: pd.DataFrame) -> dict:
    """Generate dynamic narrative using InsightEngine"""

    config = MetricConfig(
        id='stops_per_1000',
        groupby='region_name',
        value_col='stops_per_1000',
        unit='stops per 1,000 residents',
        sources=['NaPTAN October 2025', 'BODS', 'ONS Census 2021'],
        rules=['ranking', 'single_region_positioning', 'variation', 'gap_to_investment'],
        min_n=1,
        min_groups=1
    )

    filters = {}
    if len(data) == 1 and 'region_name' in data.columns:
        filters['region'] = data.iloc[0]['region_name']

    result = ENGINE.run(data, config, filters)

    return {
        'summary': result['summary'],
        'key_finding': result['key_finding'],
        'recommendation': result['recommendation'],
        'investment': result['investment'],
        'related_links': [
            {'text': 'Service Gap Analysis', 'url': '/Coverage_Accessibility'},
            {'text': 'Equity Implications', 'url': '/Equity_Social_Inclusion'}
        ]
    }


# ============================================================================
# PLACEHOLDER SECTIONS (A3-A8)
# ============================================================================

def placeholder_data_function(region_filter, urban_rural_filter):
    return pd.DataFrame()

def placeholder_viz_function(data):
    return None

def placeholder_narrative_function(data):
    return {
        'summary': "*This section will be implemented in Task 1.5*",
        'key_finding': "Implementation pending",
        'recommendation': "Coming soon"
    }


# ============================================================================
# CATEGORY CONFIGURATION
# ============================================================================

COVERAGE_CONFIG = {
    'id': 'coverage',
    'title': 'Coverage & Accessibility',
    'icon': '🟢',
    'description': """
Understanding how well bus networks serve communities across England's 9 regions. This analysis examines
service provision patterns, identifies coverage gaps, and assesses accessibility for 34.8 million residents.

**Powered by dynamic Insight Engine** - All narratives adapt intelligently to your filter selections.
""",
    'metadata': 'Data: 779,262 stops | 2,749 routes | BODS October 2025 | ONS Census 2021 | TAG 2024',
    'sections': [
        {
            'id': 'A1',
            'title': 'Regional Route Density Analysis',
            'data_function': load_route_density_data,
            'viz_function': create_route_density_viz,
            'narrative_function': generate_route_density_narrative
        },
        {
            'id': 'A2',
            'title': 'Service Coverage Assessment',
            'data_function': load_coverage_assessment_data,
            'viz_function': create_coverage_assessment_viz,
            'narrative_function': generate_coverage_assessment_narrative
        },
        {
            'id': 'A3',
            'title': 'High-Density Underserved Areas',
            'data_function': placeholder_data_function,
            'viz_function': placeholder_viz_function,
            'narrative_function': placeholder_narrative_function
        },
        {
            'id': 'A4',
            'title': 'Service Desert Identification',
            'data_function': placeholder_data_function,
            'viz_function': placeholder_viz_function,
            'narrative_function': placeholder_narrative_function
        },
        {
            'id': 'A5',
            'title': 'Walking Distance Analysis',
            'data_function': placeholder_data_function,
            'viz_function': placeholder_viz_function,
            'narrative_function': placeholder_narrative_function
        },
        {
            'id': 'A6',
            'title': 'Accessibility Standard Compliance',
            'data_function': placeholder_data_function,
            'viz_function': placeholder_viz_function,
            'narrative_function': placeholder_narrative_function
        },
        {
            'id': 'A7',
            'title': 'Urban-Rural Coverage Disparity',
            'data_function': placeholder_data_function,
            'viz_function': placeholder_viz_function,
            'narrative_function': placeholder_narrative_function
        },
        {
            'id': 'A8',
            'title': 'Population-Service Mismatch Zones',
            'data_function': placeholder_data_function,
            'viz_function': placeholder_viz_function,
            'narrative_function': placeholder_narrative_function
        }
    ]
}


# ============================================================================
# RENDER PAGE
# ============================================================================

if __name__ == "__main__":
    render_category_page(COVERAGE_CONFIG)
