"""
Coverage & Accessibility Dashboard Module
UK Bus Transport Intelligence Platform

Professional implementation of the Service Coverage module
demonstrating integration of:
- Responsive grid layout
- Interactive visualizations (Folium maps, Plotly charts)
- KPI cards with trend indicators
- NLP assistant integration
- Real-time filtering and drill-down

Author: UK Bus Transport Intelligence Team
Version: 2.0
Classification: OFFICIAL
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CoverageMetrics:
    """Coverage performance metrics"""
    national_avg: float
    regional_avg: float
    underserved_count: int
    total_lsoas: int
    trend_vs_previous: float
    investment_required: float

    @property
    def underserved_percentage(self) -> float:
        return (self.underserved_count / self.total_lsoas) * 100

    @property
    def regional_gap(self) -> float:
        return ((self.regional_avg - self.national_avg) / self.national_avg) * 100


# ============================================================================
# STYLING & CONFIGURATION
# ============================================================================

def inject_custom_css():
    """Inject professional custom CSS aligned with design system"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Root variables */
    :root {
        --color-primary-1: #1E3A5F;
        --color-primary-2: #2E7D9A;
        --color-primary-3: #4CAF90;
        --color-success: #10B981;
        --color-warning: #F59E0B;
        --color-danger: #EF4444;
        --color-info: #3B82F6;
        --color-background: #FFFFFF;
        --color-surface: #F9FAFB;
        --color-border: #E5E7EB;
        --color-text-primary: #111827;
        --color-text-secondary: #6B7280;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Global typography */
    * {
        font-family: var(--font-sans);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Dashboard container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1920px;
    }

    /* KPI Card styling */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: box-shadow 0.2s ease;
        border: 1px solid var(--color-border);
    }

    .kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .kpi-card__label {
        font-size: 0.75rem;
        color: var(--color-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        font-weight: 500;
    }

    .kpi-card__value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--color-text-primary);
        line-height: 1.2;
        margin: 8px 0;
    }

    .kpi-card__unit {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-bottom: 12px;
    }

    .kpi-card__trend {
        font-size: 0.875rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .kpi-card__trend--positive {
        color: var(--color-success);
    }

    .kpi-card__trend--negative {
        color: var(--color-danger);
    }

    .kpi-card__trend--warning {
        color: var(--color-warning);
    }

    /* Chart card styling */
    .chart-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--color-border);
    }

    .chart-card__header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--color-border);
    }

    .chart-card__title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text-primary);
    }

    /* Filter bar */
    .filter-bar {
        background: var(--color-surface);
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        border: 1px solid var(--color-border);
    }

    /* Module header */
    .module-header {
        margin-bottom: 32px;
    }

    .module-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-primary-1);
        margin-bottom: 8px;
    }

    .module-subtitle {
        font-size: 1rem;
        color: var(--color-text-secondary);
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }

        .kpi-card__value {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=3600)
def load_coverage_data(time_period: str, region: str = "All") -> gpd.GeoDataFrame:
    """
    Load coverage data for specified time period and region
    Cached for 1 hour for performance
    """
    # In production, this would query PostgreSQL/PostGIS
    # For demonstration, return mock data structure

    # Mock query
    query = f"""
        SELECT
            lsoa_code,
            lsoa_name,
            region,
            stops_per_1000,
            total_stops,
            population,
            imd_decile,
            urban_rural,
            geometry
        FROM coverage_summary
        WHERE time_period = '{time_period}'
        {f"AND region = '{region}'" if region != "All" else ""}
    """

    # For demonstration, generate synthetic data
    from shapely.geometry import Point

    n_lsoas = 100
    data = {
        'lsoa_code': [f'E0100{i:04d}' for i in range(n_lsoas)],
        'lsoa_name': [f'LSOA_{i}' for i in range(n_lsoas)],
        'region': np.random.choice(['North East', 'South West', 'London', 'West Midlands'], n_lsoas),
        'stops_per_1000': np.random.uniform(1.0, 12.0, n_lsoas),
        'total_stops': np.random.randint(5, 50, n_lsoas),
        'population': np.random.randint(1000, 5000, n_lsoas),
        'imd_decile': np.random.randint(1, 11, n_lsoas),
        'urban_rural': np.random.choice(['Urban', 'Rural'], n_lsoas, p=[0.7, 0.3]),
        'geometry': [Point(np.random.uniform(-5, 2), np.random.uniform(50, 55)) for _ in range(n_lsoas)]
    }

    gdf = gpd.GeoDataFrame(data, geometry='geometry', crs='EPSG:4326')
    return gdf


@st.cache_data(ttl=3600)
def calculate_coverage_metrics(data: gpd.GeoDataFrame, region: str = "All") -> CoverageMetrics:
    """Calculate KPI metrics from coverage data"""

    if region != "All":
        regional_data = data[data['region'] == region]
    else:
        regional_data = data

    national_avg = data['stops_per_1000'].mean()
    regional_avg = regional_data['stops_per_1000'].mean()
    underserved_count = len(regional_data[regional_data['stops_per_1000'] < 3.0])
    total_lsoas = len(regional_data)

    # Mock trend calculation (in production, compare with previous period)
    trend_vs_previous = np.random.uniform(-5, 8)

    # Mock investment calculation
    investment_required = underserved_count * 0.5  # £0.5M per underserved LSOA

    return CoverageMetrics(
        national_avg=national_avg,
        regional_avg=regional_avg,
        underserved_count=underserved_count,
        total_lsoas=total_lsoas,
        trend_vs_previous=trend_vs_previous,
        investment_required=investment_required
    )


# ============================================================================
# VISUALIZATION COMPONENTS
# ============================================================================

def render_kpi_card(label: str, value: str, unit: str, trend: str, trend_type: str):
    """Render a professional KPI card"""

    trend_class = f"kpi-card__trend--{trend_type}"
    trend_icon = "↑" if "+" in trend else "↓" if "-" in trend else "→"

    html = f"""
    <div class="kpi-card">
        <div class="kpi-card__label">{label}</div>
        <div class="kpi-card__value">{value}</div>
        <div class="kpi-card__unit">{unit}</div>
        <div class="kpi-card__trend {trend_class}">
            {trend_icon} {trend}
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_coverage_map(data: gpd.GeoDataFrame, metric: str = "stops_per_1000") -> Dict:
    """
    Render interactive choropleth map using Folium
    Returns map interaction data for drill-down functionality
    """

    # Create base map centered on UK
    m = folium.Map(
        location=[54.5, -2.5],
        zoom_start=6,
        tiles=None,
        prefer_canvas=True,
        control_scale=True
    )

    # Add custom CartoDB Positron basemap for clean look
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='Light Map',
        overlay=False,
        control=True
    ).add_to(m)

    # Create choropleth layer
    choropleth = folium.Choropleth(
        geo_data=data.__geo_interface__,
        name='Coverage',
        data=data,
        columns=['lsoa_code', metric],
        key_on='feature.properties.lsoa_code',
        fill_color='RdYlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f'Stops per 1,000 Population',
        bins=[0, 2, 4, 6, 8, 12],
        reset=True,
        nan_fill_color='lightgray',
        nan_fill_opacity=0.3
    ).add_to(m)

    # Add interactive tooltips
    folium.GeoJsonTooltip(
        fields=['lsoa_name', metric, 'region', 'imd_decile', 'urban_rural'],
        aliases=['LSOA:', 'Coverage:', 'Region:', 'IMD Decile:', 'Type:'],
        style="""
            background-color: white;
            color: #333333;
            font-family: Inter, sans-serif;
            font-size: 12px;
            padding: 10px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        """,
        sticky=True
    ).add_to(choropleth.geojson)

    # Add click popup with more details
    folium.GeoJsonPopup(
        fields=['lsoa_name', metric, 'population', 'total_stops', 'imd_decile'],
        aliases=['LSOA:', 'Coverage:', 'Population:', 'Total Stops:', 'Deprivation Decile:'],
        labels=True,
        style='font-size: 14px; font-family: Inter, sans-serif;'
    ).add_to(choropleth.geojson)

    # Add layer control
    folium.LayerControl(position='topright').add_to(m)

    # Render in Streamlit
    map_data = st_folium(
        m,
        width=None,  # Full width
        height=600,
        returned_objects=["last_object_clicked", "last_active_drawing"]
    )

    return map_data


def render_distribution_chart(data: gpd.GeoDataFrame, metric: str = "stops_per_1000"):
    """Render coverage distribution histogram"""

    fig = px.histogram(
        data,
        x=metric,
        nbins=30,
        title="Coverage Distribution",
        labels={metric: "Stops per 1,000 Population", "count": "Number of LSOAs"},
        template="plotly_white",
        color_discrete_sequence=['#2E7D9A']
    )

    # Add mean line
    mean_value = data[metric].mean()
    fig.add_vline(
        x=mean_value,
        line_dash="dash",
        line_color="#1E3A5F",
        annotation_text=f"Mean: {mean_value:.1f}",
        annotation_position="top"
    )

    # Add underserved threshold line
    fig.add_vline(
        x=3.0,
        line_dash="dot",
        line_color="#EF4444",
        annotation_text="Underserved Threshold",
        annotation_position="bottom"
    )

    # Styling
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12, color="#111827"),
        title=dict(font=dict(size=16, weight=600), x=0, xanchor="left"),
        xaxis=dict(title="Coverage (stops/1000)", gridcolor="#E5E7EB"),
        yaxis=dict(title="Number of LSOAs", gridcolor="#E5E7EB"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_trend_chart(region: str = "All"):
    """Render coverage trend over time"""

    # Mock time series data
    years = list(range(2020, 2025))

    if region == "All":
        regions = ['National Average', 'North East', 'South West', 'London', 'West Midlands']
    else:
        regions = ['National Average', region]

    data = []
    for r in regions:
        base = 6.2 if r == 'National Average' else np.random.uniform(4, 8)
        trend = np.random.uniform(-0.2, 0.4)
        values = [base + trend * i + np.random.normal(0, 0.2) for i in range(len(years))]

        for year, value in zip(years, values):
            data.append({'Year': year, 'Region': r, 'Coverage': value})

    df = pd.DataFrame(data)

    # Create line chart
    fig = px.line(
        df,
        x='Year',
        y='Coverage',
        color='Region',
        title="Coverage Evolution 2020-2024",
        labels={'Coverage': 'Stops per 1,000 Population'},
        template="plotly_white"
    )

    # Emphasize national average
    fig.update_traces(
        selector=dict(name='National Average'),
        line=dict(width=3, dash='dash')
    )

    # Styling
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12, color="#111827"),
        title=dict(font=dict(size=16, weight=600), x=0, xanchor="left"),
        xaxis=dict(title="Year", gridcolor="#E5E7EB", dtick=1),
        yaxis=dict(title="Coverage", gridcolor="#E5E7EB"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_data_table(data: gpd.GeoDataFrame, bottom_n: int = 10):
    """Render bottom N underserved LSOAs table"""

    # Sort and select bottom N
    bottom_lsoas = data.nsmallest(bottom_n, 'stops_per_1000')[
        ['lsoa_name', 'region', 'stops_per_1000', 'population', 'imd_decile']
    ].copy()

    bottom_lsoas.columns = ['LSOA', 'Region', 'Coverage', 'Population', 'IMD Decile']
    bottom_lsoas['Coverage'] = bottom_lsoas['Coverage'].round(1)

    # Display with formatting
    st.dataframe(
        bottom_lsoas,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Coverage": st.column_config.NumberColumn(
                "Coverage",
                help="Stops per 1,000 population",
                format="%.1f"
            ),
            "IMD Decile": st.column_config.NumberColumn(
                "IMD Decile",
                help="1 = most deprived, 10 = least deprived",
                format="%d"
            )
        }
    )


# ============================================================================
# AI INSIGHTS COMPONENT
# ============================================================================

def generate_ai_insights(data: gpd.GeoDataFrame, metrics: CoverageMetrics, region: str) -> List[str]:
    """
    Generate AI-powered insights from data
    In production, this would call the NLP engine
    """

    insights = []

    # Coverage trend insight
    if metrics.trend_vs_previous > 0:
        insights.append(
            f"✅ Coverage in {region} improved by {metrics.trend_vs_previous:.1f}% vs 2023 — positive trajectory"
        )
    else:
        insights.append(
            f"⚠️ Coverage in {region} declined by {abs(metrics.trend_vs_previous):.1f}% vs 2023 — investigate causes"
        )

    # Regional performance insight
    if metrics.regional_gap < -10:
        insights.append(
            f"🔴 {region} performs {abs(metrics.regional_gap):.1f}% below national average — priority intervention area"
        )
    elif metrics.regional_gap > 10:
        insights.append(
            f"🟢 {region} exceeds national average by {metrics.regional_gap:.1f}% — benchmark for other regions"
        )

    # Underserved LSOAs insight
    if metrics.underserved_percentage > 15:
        insights.append(
            f"⚠️ {metrics.underserved_count} LSOAs ({metrics.underserved_percentage:.1f}%) are underserved — requires £{metrics.investment_required:.1f}M investment"
        )

    # Rural/urban disparity
    urban_avg = data[data['urban_rural'] == 'Urban']['stops_per_1000'].mean()
    rural_avg = data[data['urban_rural'] == 'Rural']['stops_per_1000'].mean()
    disparity_ratio = urban_avg / rural_avg

    if disparity_ratio > 2.5:
        insights.append(
            f"🔴 Urban-rural disparity: {disparity_ratio:.1f}× gap (urban: {urban_avg:.1f}, rural: {rural_avg:.1f}) — rural mobility fund opportunity"
        )

    # Deprivation correlation
    correlation = data[['stops_per_1000', 'imd_decile']].corr().iloc[0, 1]
    if abs(correlation) > 0.4:
        direction = "positive" if correlation > 0 else "negative"
        insights.append(
            f"📊 {direction.capitalize()} correlation (r={correlation:.2f}) between coverage and deprivation — equity implications"
        )

    return insights


# ============================================================================
# MAIN DASHBOARD FUNCTION
# ============================================================================

def render_coverage_dashboard():
    """
    Main function to render the Coverage & Accessibility Dashboard
    This is the entry point called from the main app
    """

    # Apply custom styling
    inject_custom_css()

    # Module header
    st.markdown("""
    <div class="module-header">
        <h1 class="module-title">📊 Service Coverage & Accessibility</h1>
        <p class="module-subtitle">
            Geographic distribution of bus services with equity and accessibility analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ========================================================================
    # FILTERS
    # ========================================================================

    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        time_period = st.selectbox(
            "📅 Time Period",
            options=["2024_Q3", "2024_Q2", "2024_Q1", "2023_Q4"],
            index=0
        )

    with col2:
        region = st.selectbox(
            "🗺️ Region",
            options=["All", "North East", "South West", "London", "West Midlands", "Yorkshire"],
            index=0
        )

    with col3:
        metric = st.selectbox(
            "📊 Metric",
            options=["stops_per_1000", "frequency_per_capita", "accessibility_score"],
            format_func=lambda x: {
                "stops_per_1000": "Stops per 1,000 Pop",
                "frequency_per_capita": "Daily Frequency",
                "accessibility_score": "Accessibility Index"
            }[x],
            index=0
        )

    with col4:
        show_imd = st.checkbox("Show Deprivation Overlay", value=False)

    st.markdown('</div>', unsafe_allow_html=True)

    # ========================================================================
    # LOAD DATA
    # ========================================================================

    with st.spinner("Loading coverage data..."):
        data = load_coverage_data(time_period, region)
        metrics = calculate_coverage_metrics(data, region)

    # ========================================================================
    # KPI CARDS
    # ========================================================================

    st.markdown("### Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        trend_str = f"+{metrics.trend_vs_previous:.1f}%" if metrics.trend_vs_previous > 0 else f"{metrics.trend_vs_previous:.1f}%"
        trend_type = "positive" if metrics.trend_vs_previous > 0 else "negative"
        render_kpi_card(
            label="Regional Average Coverage",
            value=f"{metrics.regional_avg:.1f}",
            unit="stops per 1,000 population",
            trend=f"{trend_str} vs 2023",
            trend_type=trend_type
        )

    with col2:
        severity = "warning" if metrics.underserved_percentage > 10 else "positive"
        render_kpi_card(
            label="Underserved LSOAs",
            value=f"{metrics.underserved_count:,}",
            unit=f"{metrics.underserved_percentage:.1f}% of total",
            trend="⚠️ High" if metrics.underserved_percentage > 15 else "✓ Moderate",
            trend_type=severity
        )

    with col3:
        gap_str = f"{metrics.regional_gap:+.1f}%"
        gap_type = "positive" if metrics.regional_gap > 0 else "negative"
        render_kpi_card(
            label="Regional Gap",
            value=gap_str,
            unit="vs national average",
            trend=f"Target: 0% gap",
            trend_type=gap_type
        )

    with col4:
        render_kpi_card(
            label="Investment Required",
            value=f"£{metrics.investment_required:.1f}M",
            unit="over 5 years",
            trend="To reach baseline",
            trend_type="warning"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================================================================
    # MAIN VISUALIZATIONS
    # ========================================================================

    # Primary map and distribution chart
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(f"#### 🗺️ Geographic Coverage Distribution")

        map_data = render_coverage_map(data, metric)

        # Handle map clicks for drill-down
        if map_data and map_data.get("last_object_clicked"):
            clicked_lsoa = map_data["last_object_clicked"]
            if clicked_lsoa:
                st.info(f"📍 Selected LSOA: {clicked_lsoa.get('properties', {}).get('lsoa_name', 'Unknown')}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(f"#### 📊 Coverage Distribution")
        render_distribution_chart(data, metric)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Trend chart and data table
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(f"#### 📈 Coverage Evolution")
        render_trend_chart(region)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(f"#### 📋 Bottom 10 Underserved LSOAs")
        render_data_table(data, bottom_n=10)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================================================================
    # AI INSIGHTS & RECOMMENDATIONS
    # ========================================================================

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### 🤖 AI-Generated Insights & Recommendations")

    insights = generate_ai_insights(data, metrics, region if region != "All" else "UK")

    for insight in insights:
        st.markdown(f"- {insight}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📄 Generate Report", use_container_width=True):
            st.info("Report generation feature - connects to report_generator module")

    with col2:
        if st.button("📥 Export Data", use_container_width=True):
            # Convert to CSV and offer download
            csv = data.drop(columns=['geometry']).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"coverage_{region}_{time_period}.csv",
                mime="text/csv"
            )

    with col3:
        if st.button("🎯 Create Scenario", use_container_width=True):
            st.info("Scenario creation - navigates to Policy Scenarios module")

    with col4:
        if st.button("💬 Ask AI Assistant", use_container_width=True):
            st.info("Opens AI Assistant panel with context pre-loaded")

    st.markdown('</div>', unsafe_allow_html=True)

    # ========================================================================
    # FOOTER
    # ========================================================================

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #6B7280; font-size: 0.875rem; padding: 20px 0; border-top: 1px solid #E5E7EB;">
        <strong>UK Bus Transport Intelligence Platform</strong> |
        Data: BODS Q3 2024, ONS 2021 Census |
        Methodology: DfT TAG Compliant |
        <a href="#" style="color: #2E7D9A;">Documentation</a>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(
        page_title="Coverage Dashboard - UK Bus Intelligence",
        page_icon="🚌",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    render_coverage_dashboard()
