"""
UK Bus Analytics Platform - Homepage
Professional consulting intelligence platform for UK bus transport analysis
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from dashboard.utils.data_loader import load_regional_summary, get_national_stats

# Page configuration
st.set_page_config(
    page_title="UK Bus Analytics Platform",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
national_stats = get_national_stats()
regional_summary = load_regional_summary()

# Header
st.title("🚌 UK Bus Analytics Platform")
st.markdown("**Professional intelligence for bus transport decision-makers**")
st.markdown("---")

# National overview metrics
if national_stats:
    st.markdown("## National Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Bus Stops",
            value=f"{national_stats['total_stops']:,}"
        )

    with col2:
        st.metric(
            label="Routes",
            value=f"{national_stats['total_routes']:,}"
        )

    with col3:
        st.metric(
            label="Regions",
            value=f"{national_stats['total_regions']}"
        )

    with col4:
        st.metric(
            label="Population Served",
            value=f"{national_stats['total_population']/1e6:.1f}M"
        )

    st.markdown("---")

# Regional comparison table
if not regional_summary.empty:
    st.markdown("## Regional Performance")

    # Display clean table
    display_cols = [
        'region_name',
        'total_stops',
        'population',
        'stops_per_1000',
        'routes_count',
        'routes_per_100k',
        'coverage_rank'
    ]

    # Rename columns for display
    display_df = regional_summary[display_cols].copy()
    display_df.columns = [
        'Region',
        'Bus Stops',
        'Population',
        'Stops/1000',
        'Routes',
        'Routes/100k',
        'Rank'
    ]

    # Format numbers
    display_df['Bus Stops'] = display_df['Bus Stops'].apply(lambda x: f"{x:,}")
    display_df['Population'] = display_df['Population'].apply(lambda x: f"{x:,}")
    display_df['Stops/1000'] = display_df['Stops/1000'].apply(lambda x: f"{x:.1f}")
    display_df['Routes'] = display_df['Routes'].apply(lambda x: f"{x:,}")
    display_df['Routes/100k'] = display_df['Routes/100k'].apply(lambda x: f"{x:.1f}")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    st.markdown("---")

# Navigation guide
st.markdown("## Analysis Categories")

st.markdown("""
Explore comprehensive analysis across 10 key areas:

**Service Provision**
- 🟢 **Coverage & Accessibility** - Network density, service gaps, walking distances
- 🔵 **Frequency & Reliability** - Service patterns, headways, operating hours

**Network Analysis**
- 🔴 **Route Characteristics** - Route lengths, overlaps, connectivity

**Equity & Impact**
- 👥 **Socio-Economic Correlations** - Deprivation, unemployment, demographics
- ⚖️ **Equity & Social Inclusion** - Service distribution, accessibility features

**Optimization & Economics**
- 🎯 **Route Optimization** - Network efficiency, gap filling opportunities
- 💷 **Economic Impact & BCR** - Benefit-cost analysis, investment appraisal

Use the sidebar to navigate to detailed analysis pages.
""")

st.markdown("---")

# Data sources footer
st.caption("""
**Data Sources:** BODS (October 2025), ONS Census 2021, NaPTAN, NOMIS
| **Coverage:** 779,262 stops, 2,749 routes, 9 regions
| **Last Updated:** November 2025
""")
