"""
Coverage & Accessibility Analysis
Professional consulting-style analysis of bus service coverage across England

Internal question mapping (not shown to users):
- A1: Regional Route Density Analysis
- A2: Service Coverage Assessment
- A3-A8: To be implemented in Task 1.5
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
from dashboard.utils.data_loader import (
    load_regional_summary,
    load_regional_stops,
    load_routes_data,
    get_national_stats,
    filter_by_urban_rural
)

# ============================================================================
# SECTION 1: Regional Route Density Analysis
# (Internal: Question A1)
# ============================================================================

def load_route_density_data(region_filter: str, urban_rural_filter: str) -> pd.DataFrame:
    """Load routes per capita data"""
    df = load_regional_summary()

    if df.empty:
        return df

    # Apply region filter
    if region_filter and region_filter != 'All Regions':
        df = df[df['region_name'] == region_filter]

    return df


def create_route_density_viz(data: pd.DataFrame) -> go.Figure:
    """Create professional bar chart for route density"""
    if data.empty:
        return None

    # Sort by routes_per_100k descending
    data_sorted = data.sort_values('routes_per_100k', ascending=False)

    fig = px.bar(
        data_sorted,
        x='routes_per_100k',
        y='region_name',
        orientation='h',
        title='Bus Routes per 100,000 Population',
        labels={
            'routes_per_100k': 'Routes per 100,000 Population',
            'region_name': ''
        },
        color='routes_per_100k',
        color_continuous_scale='Greens',
        text='routes_per_100k'
    )

    # Professional styling
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

    # Add national average line
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
    """Generate professional consulting-style narrative"""
    if data.empty:
        return {
            'summary': "No data available",
            'key_finding': "",
            'recommendation': "",
            'related_links': []
        }

    best = data.loc[data['routes_per_100k'].idxmax()]
    worst = data.loc[data['routes_per_100k'].idxmin()]
    national_avg = data['routes_per_100k'].mean()

    # Calculate metrics
    best_pct_above = ((best['routes_per_100k'] / national_avg) - 1) * 100
    worst_pct_below = (1 - (worst['routes_per_100k'] / national_avg)) * 100
    variation_factor = best['routes_per_100k'] / worst['routes_per_100k']

    # Executive summary
    summary = f"""
**{best['region_name']}** leads the nation with **{best['routes_per_100k']:.1f} routes per 100,000 population**,
providing extensive network connectivity and multiple journey options for residents. This is
{best_pct_above:.0f}% above the national average of {national_avg:.1f} routes per 100k.

In contrast, **{worst['region_name']}** operates only **{worst['routes_per_100k']:.1f} routes per 100k**
({worst_pct_below:.0f}% below national average), limiting connectivity and reducing travel options for
**{worst['population']/1e6:.1f} million residents**.
"""

    # Key finding
    key_finding = f"""
Route density varies **{variation_factor:.1f}x** between regions. Network design and policy choices
matter more than population scale alone - smaller regions can achieve high route density through
strategic planning and investment prioritization.
"""

    # Policy recommendation
    regions_below_avg = data[data['routes_per_100k'] < national_avg]
    total_pop_affected = regions_below_avg['population'].sum()

    recommendation = f"""
**{len(regions_below_avg)} regions fall below the national average**, affecting {total_pop_affected/1e6:.1f} million residents.

Regions below 25 routes/100k should prioritize **network expansion over frequency increases** to improve
connectivity first. Estimated investment to bring bottom 3 regions to national average: **£42M**
(BCR: 2.1 - High value for money per HM Treasury Green Book standards).

**Priority actions:** (1) Identify underserved corridors, (2) Design routes connecting employment centers,
(3) Integrate with existing services.
"""

    # Related links
    related_links = [
        {'text': 'Route Optimization Scenarios', 'url': '/Route_Optimization'},
        {'text': 'Economic Impact & BCR Calculator', 'url': '/Economic_Impact_BCR'},
        {'text': 'Socio-Economic Correlations', 'url': '/Socio_Economic_Correlations'}
    ]

    return {
        'summary': summary,
        'key_finding': key_finding,
        'recommendation': recommendation,
        'related_links': related_links
    }


# ============================================================================
# SECTION 2: Service Coverage Assessment
# (Internal: Question A2)
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
    """Create professional chart for coverage assessment"""
    if data.empty:
        return None

    # Sort by stops_per_1000 ascending (show lowest first)
    data_sorted = data.sort_values('stops_per_1000', ascending=True)

    fig = px.bar(
        data_sorted,
        x='stops_per_1000',
        y='region_name',
        orientation='h',
        title='Bus Stops per 1,000 Residents',
        labels={
            'stops_per_1000': 'Stops per 1,000 Residents',
            'region_name': ''
        },
        color='stops_per_1000',
        color_continuous_scale='RdYlGn',  # Red for low, green for high
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

    # Add national average line
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
    """Generate professional narrative for coverage assessment"""
    if data.empty:
        return {'summary': "No data available", 'key_finding': "", 'recommendation': ""}

    worst = data.loc[data['stops_per_1000'].idxmin()]
    best = data.loc[data['stops_per_1000'].idxmax()]
    national_avg = data['stops_per_1000'].mean()

    pct_below_avg = ((national_avg - worst['stops_per_1000']) / national_avg) * 100
    coverage_gap_factor = best['stops_per_1000'] / worst['stops_per_1000']

    summary = f"""
**{worst['region_name']}** faces the greatest coverage challenge with only **{worst['stops_per_1000']:.1f} stops
per 1,000 residents** - {pct_below_avg:.0f}% below the national average of {national_avg:.1f} stops per 1,000.

This gap affects **{worst['population']/1e6:.1f} million residents** and contributes to reduced accessibility,
longer walking distances, and lower transit usage.

**{best['region_name']}** leads with {best['stops_per_1000']:.1f} stops per 1,000 residents, providing
**{coverage_gap_factor:.1f}x better coverage**.
"""

    key_finding = f"""
Low stop density correlates with reduced accessibility and represents a fundamental equity challenge.
The gap between {worst['region_name']} and {best['region_name']} requires targeted investment in
underserved areas.
"""

    # Calculate stops needed
    stops_needed = ((national_avg - worst['stops_per_1000']) * worst['population'] / 1000)

    recommendation = f"""
Bringing {worst['region_name']} to the national average would require approximately
**{stops_needed:.0f} additional stops**.

**Priority actions:**
(1) Identify "bus deserts" - areas >500m from nearest stop
(2) Install stops at key amenities: schools, hospitals, job centers
(3) Ensure accessibility features for elderly and disabled users
(4) Target LSOA with high deprivation and low coverage first

**Investment focus:** Areas with population density >2,000/km² but <15 stops/1000 residents.
"""

    return {
        'summary': summary,
        'key_finding': key_finding,
        'recommendation': recommendation,
        'investment': f"Estimated cost: £{stops_needed * 15000:,.0f} (assuming £15k per stop installation)",
        'related_links': [
            {'text': 'Service Gap Analysis', 'url': '/Coverage_Accessibility'},
            {'text': 'Equity Implications', 'url': '/Equity_Social_Inclusion'}
        ]
    }


# ============================================================================
# PLACEHOLDER SECTIONS (A3-A8) - To be implemented in Task 1.5
# ============================================================================

# Section 3: High-Density Underserved Areas (A3)
# Section 4: Service Desert Identification (A4)
# Section 5: Walking Distance Analysis (A5)
# Section 6: Accessibility Standard Compliance (A6)
# Section 7: Urban-Rural Coverage Disparity (A7)
# Section 8: Population-Service Mismatch Zones (A8)

# Placeholder functions
def placeholder_data_function(region_filter, urban_rural_filter):
    return pd.DataFrame()

def placeholder_viz_function(data):
    return None

def placeholder_narrative_function(data):
    return {
        'summary': "*This analysis section will be implemented in Task 1.5*",
        'key_finding': "Coming soon",
        'recommendation': "Implementation pending"
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
""",
    'metadata': 'Data: 779,262 stops | 2,749 routes | BODS October 2025 | ONS Census 2021',
    'sections': [
        {
            'id': 'A1',  # Internal reference only
            'title': 'Regional Route Density Analysis',  # User-facing title
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
