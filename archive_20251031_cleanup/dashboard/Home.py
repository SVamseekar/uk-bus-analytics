"""
UK Bus Transport Intelligence Platform - Home Page
=================================================
Main dashboard entry point with navigation and overview

Client: UK Department for Transport (DfT) Policy Unit
Platform Type: Interactive Policy Intelligence & Decision Support System
Delivery Standard: Tier 1 Consulting (OECD/World Bank Style)
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.data_loader import load_lsoa_metrics, get_summary_statistics, load_spatial_answers
from dashboard.utils.ui_components import (
    apply_professional_config,
    render_dashboard_header,
    render_kpi_card,
    render_section_divider,
    render_insight_card,
    create_responsive_columns,
    load_professional_css,
    render_navigation_bar
)

# Page configuration
st.set_page_config(
    page_title="UK Bus Transport Intelligence Platform",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="auto"  # Changed from collapsed to auto to prevent flashing
)

# Load professional CSS design system
load_professional_css()
apply_professional_config()

# Navigation Bar
render_navigation_bar()

# Header
render_dashboard_header(
    title="UK Bus Transport Intelligence Platform",
    subtitle="AI-Powered Policy Intelligence & Decision Support System for Transport Planning",
    icon="🚌"
)

# Load data
try:
    lsoa_data = load_lsoa_metrics()
    stats = get_summary_statistics(lsoa_data)
    answers = load_spatial_answers()

    # Overview Section
    render_section_divider("National Overview", icon="📊")

    # KPI Metrics with professional cards
    col1, col2, col3, col4 = create_responsive_columns(4)

    with col1:
        render_kpi_card(
            label="Total Bus Stops",
            value=f"{stats['total_stops']:,}",
            unit="stops analyzed",
            icon="🚏",
            help_text="Total number of bus stops across all analyzed areas"
        )

    with col2:
        render_kpi_card(
            label="Coverage Areas",
            value=f"{stats['total_lsoas']:,}",
            unit="LSOAs",
            icon="📍",
            help_text="Lower Super Output Areas analyzed"
        )

    with col3:
        coverage_delta = stats['avg_coverage'] - 50
        render_kpi_card(
            label="Average Coverage Score",
            value=f"{stats['avg_coverage']:.1f}",
            unit="/100",
            trend=f"{coverage_delta:+.1f} vs target",
            trend_type="positive" if coverage_delta > 0 else "negative",
            icon="📊"
        )

    with col4:
        render_kpi_card(
            label="Average Equity Index",
            value=f"{stats['avg_equity']:.1f}",
            unit="/100",
            icon="⚖️",
            help_text="How well service aligns with community needs"
        )

    st.markdown("---")

    # Quick Insights with professional cards
    render_section_divider("Key Intelligence", icon="🎯")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_insight_card(
            title="Service Gap Analysis",
            content=f"""
            Our AI analysis has identified critical service gaps across the network:

            • **{stats['service_gaps']:,} areas** fall in the bottom 10% coverage decile
            • **{stats['underserved_areas']:,} areas** classified as significantly underserved
            • **{stats['underserved_population']:,} people** reside in these communities
            • **{stats['total_routes']:,} routes** estimated across the analyzed network

            These findings enable targeted interventions following DfT TAG guidance.
            """,
            icon="📉"
        )

    with col2:
        render_insight_card(
            title="Platform Capabilities",
            content="""
            This platform delivers consulting-grade transport intelligence:

            • **Service Coverage Analysis** - LSOA-level gap identification
            • **ML-Powered Detection** - AI identifies underserved communities
            • **Equity Intelligence** - Measure alignment with deprivation indices
            • **Economic Appraisal** - BCR calculation (HM Treasury Green Book)
            • **Policy Simulation** - Test interventions with dynamic impact modeling
            • **NLP Assistant** - Conversational data exploration
            """,
            icon="🚀"
        )

    st.markdown("---")

    # Navigation Guide
    st.markdown("## 🗺️ Navigation Guide")

    nav_col1, nav_col2, nav_col3 = st.columns(3)

    with nav_col1:
        st.markdown("### 📍 Analysis Modules")
        st.markdown("""
        - **Service Coverage** - Geographic distribution and accessibility
        - **Network Optimization** - Route clustering and efficiency
        - **Equity Intelligence** - Socio-economic service alignment
        """)

    with nav_col2:
        st.markdown("### 💼 Decision Support")
        st.markdown("""
        - **Investment Appraisal** - BCR calculation and economic impact
        - **Policy Scenarios** - Simulate fare caps, frequency changes
        - **Policy Assistant** - AI-powered Q&A system
        """)

    with nav_col3:
        st.markdown("### 📈 Data & Methodology")
        st.markdown(f"""
        - **Data Snapshot**: {answers['metadata']['data_snapshot']}
        - **LSOAs Analyzed**: {answers['metadata']['lsoa_count']:,}
        - **Standards**: UK Treasury Green Book, DfT TAG 2025
        - **Update Frequency**: Monthly automated refresh
        """)

    # Footer
    st.markdown("---")
    st.markdown("### 📘 About This Platform")
    st.info("""
    This platform provides **consulting-grade transport intelligence** for UK public transport authorities.
    Unlike traditional static reports, this system delivers:
    - **Real-time analytics** updated monthly
    - **Interactive exploration** from national to neighborhood level
    - **AI-powered insights** that identify hidden patterns
    - **Government-standard methodology** (Treasury Green Book, DfT TAG)
    - **Policy simulation** to test interventions before implementation

    Use the navigation bar above to access specific intelligence modules.
    """)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please ensure spatial metrics have been computed by running: `python3 analysis/spatial/01_compute_spatial_metrics_v2.py`")
