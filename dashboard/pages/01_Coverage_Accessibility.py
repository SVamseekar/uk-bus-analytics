"""
Category A: Coverage & Accessibility Analysis
Professional consulting-style dashboard with dynamic narratives and adaptive visualizations

Sections A1-A2 use InsightEngine for context-aware narratives
Sections A3-A8 use conditional logic for context-specific analysis
All sections adapt to hierarchical filter selections (region + urban/rural)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils.data_loader import load_regional_summary, load_regional_stops, REGION_CODES
from dashboard.utils.insight_engine import InsightEngine, MetricConfig

# Initialize engine
ENGINE = InsightEngine()

# Page config
st.set_page_config(
    page_title="Coverage & Accessibility | UK Bus Analytics",
    page_icon="🟢",
    layout="wide"
)

# ============================================================================
# HEADER & FILTERS
# ============================================================================

st.title("🟢 Coverage & Accessibility Analysis")
st.markdown("""
Comprehensive analysis of bus service coverage across England's regions, examining
stop density, route availability, walking distances, and service accessibility standards.
""")

st.markdown("---")

# Global filters - HIERARCHICAL DESIGN
st.markdown("### 🔍 Analysis Filters")

col1, col2 = st.columns([3, 2])

with col1:
    region_options = ['All Regions'] + sorted(list(REGION_CODES.keys()))
    region_filter = st.selectbox(
        "Geographic Scope:",
        region_options,
        key='region_filter',
        help="Select a specific region or compare all regions"
    )

with col2:
    urban_rural_filter = st.selectbox(
        "Urban/Rural:",
        ['All', 'Urban Only', 'Rural Only'],
        key='urban_rural_filter',
        help="Filter by urban or rural classification within selected geographic scope"
    )

# Parse filters into mode and value
if region_filter == 'All Regions':
    if urban_rural_filter == 'All':
        filter_mode = 'all_regions'
        filter_value = None
        filter_display = "📊 All Regions"
    elif urban_rural_filter == 'Urban Only':
        filter_mode = 'all_urban'
        filter_value = 'urban'
        filter_display = "🏙️ All Regions - Urban Areas"
    else:  # Rural Only
        filter_mode = 'all_rural'
        filter_value = 'rural'
        filter_display = "🌾 All Regions - Rural Areas"
else:
    # Specific region selected
    if urban_rural_filter == 'All':
        filter_mode = 'region'
        filter_value = region_filter
        filter_display = f"📍 {region_filter}"
    elif urban_rural_filter == 'Urban Only':
        filter_mode = 'region_urban'
        filter_value = region_filter
        filter_display = f"🏙️ {region_filter} - Urban"
    else:  # Rural Only
        filter_mode = 'region_rural'
        filter_value = region_filter
        filter_display = f"🌾 {region_filter} - Rural"

# Display active filter
st.info(f"**Active Filter:** {filter_display}")

st.markdown("---")


# ============================================================================
# SECTION A1: Regional Route Density Analysis
# ============================================================================

st.header("📊 A1: Regional Route Density Analysis")
st.markdown("*Which regions have the highest number of bus routes per capita?*")

def load_filtered_data(filter_mode, filter_value):
    """
    Load data based on filter mode
    Filter modes:
    - all_regions: All 9 regions comparison
    - all_urban: All urban areas nationwide
    - all_rural: All rural areas nationwide
    - region: Single region (all areas)
    - region_urban: Single region urban only
    - region_rural: Single region rural only
    """
    if filter_mode == 'all_regions':
        # Show all 9 regional data
        return load_regional_summary()

    elif filter_mode == 'region':
        # Show single region
        df = load_regional_summary()
        return df[df['region_name'] == filter_value]

    elif filter_mode in ['all_urban', 'all_rural', 'region_urban', 'region_rural']:
        # Need to aggregate from stops data
        if filter_mode.startswith('region_'):
            # Load specific region's stops
            stops_data = load_regional_stops(filter_value)
        else:
            # Load all stops
            stops_data = load_regional_stops()

        if stops_data.empty or 'UrbanRural (name)' not in stops_data.columns:
            return pd.DataFrame()

        # Get unique LSOAs with their classification
        lsoa_data = stops_data[['lsoa_code', 'UrbanRural (name)', 'total_population']].drop_duplicates('lsoa_code')

        # Filter by urban or rural
        if 'urban' in filter_mode:
            lsoa_data = lsoa_data[lsoa_data['UrbanRural (name)'].str.contains('Urban', case=False, na=False)]
            display_name = f"🏙️ {filter_value} - Urban" if filter_mode == 'region_urban' else '🏙️ All Urban Areas'
        else:  # rural
            lsoa_data = lsoa_data[lsoa_data['UrbanRural (name)'].str.contains('Rural', case=False, na=False)]
            display_name = f"🌾 {filter_value} - Rural" if filter_mode == 'region_rural' else '🌾 All Rural Areas'

        # Count stops in these LSOAs
        stops_in_filter = stops_data[stops_data['lsoa_code'].isin(lsoa_data['lsoa_code'])]

        # Count unique routes (from source files)
        routes_count = stops_in_filter['source_file'].nunique()

        # Aggregate metrics
        aggregated = pd.DataFrame([{
            'region_code': filter_mode,
            'region_name': display_name,
            'total_stops': stops_in_filter['stop_id'].nunique(),
            'unique_lsoas': lsoa_data['lsoa_code'].nunique(),
            'population': lsoa_data['total_population'].sum(),
            'routes_count': routes_count
        }])

        # Calculate per-capita metrics
        if aggregated['population'].iloc[0] > 0:
            aggregated['stops_per_1000'] = (aggregated['total_stops'] / aggregated['population']) * 1000
            aggregated['routes_per_100k'] = (aggregated['routes_count'] / aggregated['population']) * 100000
        else:
            aggregated['stops_per_1000'] = 0
            aggregated['routes_per_100k'] = 0

        return aggregated

    return pd.DataFrame()

def create_route_density_viz(data):
    """Create professional horizontal bar chart"""
    if data.empty:
        return None

    data_sorted = data.sort_values('routes_per_100k', ascending=False)

    fig = px.bar(
        data_sorted,
        x='routes_per_100k',
        y='region_name',
        orientation='h',
        title='Bus Routes per 100,000 Population by Region',
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
        font=dict(size=12, family="Inter, sans-serif"),
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

# Load and visualize
with st.spinner("Loading route density data..."):
    route_data = load_filtered_data(filter_mode, filter_value)

    if not route_data.empty:
        # Show different views based on filter mode
        if filter_mode != 'all_regions':
            # Single entity: show metrics + gauge chart
            region = route_data.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Routes per 100k", f"{region['routes_per_100k']:.1f}")
            with col2:
                st.metric("Total Routes", f"{int(region['routes_count']):,}")
            with col3:
                st.metric("Population", f"{int(region['population']):,}")
            with col4:
                # Calculate national average for comparison
                all_data = load_regional_summary()
                nat_avg = all_data['routes_per_100k'].mean()
                delta = region['routes_per_100k'] - nat_avg
                st.metric("vs National Avg", f"{delta:+.1f}", delta=f"{delta:+.1f}")

            # Add gauge chart for single entity
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=region['routes_per_100k'],
                delta={'reference': nat_avg, 'valueformat': '.1f'},
                title={'text': f"Routes per 100k Population<br><sub>National Average: {nat_avg:.1f}</sub>"},
                gauge={
                    'axis': {'range': [None, max(nat_avg * 2, region['routes_per_100k'] * 1.2)]},
                    'bar': {'color': "#16a34a"},
                    'steps': [
                        {'range': [0, nat_avg * 0.5], 'color': "#fee2e2"},
                        {'range': [nat_avg * 0.5, nat_avg], 'color': "#fef3c7"},
                        {'range': [nat_avg, nat_avg * 1.5], 'color': "#d9f99d"},
                        {'range': [nat_avg * 1.5, nat_avg * 2], 'color': "#86efac"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': nat_avg
                    }
                }
            ))
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Multiple regions: show comparison bar chart
            fig = create_route_density_viz(route_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        # Generate narrative using InsightEngine
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

        # Pass appropriate filter context based on mode
        insight_filters = {}
        if filter_mode == 'region':
            insight_filters['region'] = filter_value
        elif filter_mode in ['region_urban', 'region_rural']:
            insight_filters['region'] = filter_value
            insight_filters['urban_rural'] = 'Urban' if 'urban' in filter_mode else 'Rural'
        elif filter_mode == 'all_urban':
            insight_filters['urban_rural'] = 'Urban'
        elif filter_mode == 'all_rural':
            insight_filters['urban_rural'] = 'Rural'

        narrative = ENGINE.run(route_data, config, insight_filters)

        # Display insights
        st.markdown("### Key Findings")
        st.info(narrative['summary'])

        if narrative.get('key_finding'):
            st.success(f"**Critical Insight:** {narrative['key_finding']}")

        if narrative.get('recommendation'):
            st.warning(f"**Policy Recommendation:** {narrative['recommendation']}")

        # Data sources
        with st.expander("📚 Data Sources & Methodology"):
            st.markdown("**Data Sources:**")
            for source in narrative['sources']:
                st.markdown(f"- {source}")
            st.markdown(f"\n**Sample Size:** {narrative['evidence']['n']} analyzed")
    else:
        st.error("No route density data available")

st.markdown("---")


# ============================================================================
# SECTION A2: Regional Stop Coverage
# ============================================================================

st.header("📊 A2: Regional Stop Coverage Analysis")
st.markdown("*Which regions have the lowest number of bus stops per 1,000 residents?*")

def create_stop_coverage_viz(data):
    """Create professional bar chart for stops per 1000"""
    if data.empty:
        return None

    data_sorted = data.sort_values('stops_per_1000', ascending=True)

    # Color scale: red for low, green for high
    colors = ['#dc2626' if x < 20 else '#16a34a' if x > 23 else '#eab308'
              for x in data_sorted['stops_per_1000']]

    fig = go.Figure(data=[go.Bar(
        y=data_sorted['region_name'],
        x=data_sorted['stops_per_1000'],
        orientation='h',
        text=data_sorted['stops_per_1000'].round(1),
        textposition='outside',
        marker_color=colors,
        hovertemplate='<b>%{y}</b><br>' +
                      'Stops per 1,000: %{x:.1f}<br>' +
                      '<extra></extra>'
    )])

    fig.update_layout(
        title='Bus Stops per 1,000 Population by Region',
        xaxis_title="Bus Stops per 1,000 Residents",
        yaxis_title="",
        height=500,
        font=dict(size=12, family="Inter, sans-serif"),
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

# Load and visualize
with st.spinner("Loading stop coverage data..."):
    stop_data = load_filtered_data(filter_mode, filter_value)

    if not stop_data.empty:
        # Show different views based on filter mode
        if filter_mode != 'all_regions':
            # Single entity: show metrics + gauge
            region = stop_data.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Stops per 1,000", f"{region['stops_per_1000']:.1f}")
            with col2:
                st.metric("Total Stops", f"{int(region['total_stops']):,}")
            with col3:
                st.metric("Population", f"{int(region['population']):,}")
            with col4:
                # Calculate national average for comparison
                all_data = load_regional_summary()
                nat_avg = all_data['stops_per_1000'].mean()
                delta = region['stops_per_1000'] - nat_avg
                st.metric("vs National Avg", f"{delta:+.1f}", delta=f"{delta:+.1f}")

            # Add radial/polar bar chart for single entity - distinct from A1's gauge
            # Calculate percentile position
            all_data_full = load_regional_summary()
            sorted_values = all_data_full['stops_per_1000'].sort_values()
            percentile = (sorted_values < region['stops_per_1000']).sum() / len(sorted_values) * 100

            # Create polar bar chart
            categories = ['National\nAverage', 'This\nSelection', 'Top\nPerformer']
            values = [
                nat_avg,
                region['stops_per_1000'],
                all_data_full['stops_per_1000'].max()
            ]
            colors = ['#94a3b8', '#3b82f6', '#10b981']

            fig = go.Figure()

            fig.add_trace(go.Barpolar(
                r=values,
                theta=categories,
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=2)
                ),
                text=[f"{v:.1f}" for v in values],
                textposition='outside',
                textfont=dict(size=14, color='black'),
                hovertemplate='%{theta}<br>%{r:.1f} stops/1000<extra></extra>'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(values) * 1.2],
                        showticklabels=False,
                        ticks=''
                    ),
                    angularaxis=dict(
                        direction='clockwise',
                        rotation=90
                    )
                ),
                title=dict(
                    text=f"Stop Coverage Benchmark<br><sub>Percentile: {percentile:.0f}th (among all regions)</sub>",
                    x=0.5,
                    xanchor='center'
                ),
                height=350,
                margin=dict(l=80, r=80, t=80, b=60),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            # Multiple regions: show comparison chart
            fig = create_stop_coverage_viz(stop_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        # Generate narrative
        config = MetricConfig(
            id='stops_per_1000',
            groupby='region_name',
            value_col='stops_per_1000',
            unit='stops per 1,000 population',
            sources=['NaPTAN October 2025', 'BODS TransXChange', 'ONS Census 2021'],
            rules=['ranking', 'single_region_positioning', 'variation', 'gap_to_investment'],
            min_n=1,
            min_groups=1
        )

        # Pass appropriate filter context
        insight_filters = {}
        if filter_mode == 'region':
            insight_filters['region'] = filter_value
        elif filter_mode in ['region_urban', 'region_rural']:
            insight_filters['region'] = filter_value
            insight_filters['urban_rural'] = 'Urban' if 'urban' in filter_mode else 'Rural'
        elif filter_mode == 'all_urban':
            insight_filters['urban_rural'] = 'Urban'
        elif filter_mode == 'all_rural':
            insight_filters['urban_rural'] = 'Rural'

        narrative = ENGINE.run(stop_data, config, insight_filters)

        st.markdown("### Key Findings")
        st.info(narrative['summary'])

        if narrative.get('key_finding'):
            st.success(f"**Critical Insight:** {narrative['key_finding']}")

        if narrative.get('recommendation'):
            st.warning(f"**Policy Recommendation:** {narrative['recommendation']}")
    else:
        st.error("No stop coverage data available")

st.markdown("---")


# ============================================================================
# SECTION A3: High-Density Underserved Areas
# ============================================================================

st.header("📊 A3: High-Density Underserved Areas")
st.markdown("*Are there regions where bus stop density is low relative to population density?*")

def create_density_scatter(data):
    """Scatter plot: population density vs stops density"""
    if data.empty:
        return None

    # Calculate density metrics
    # Assuming we have population and area data
    fig = px.scatter(
        data,
        x='population',
        y='stops_per_1000',
        size='total_stops',
        color='region_name',
        title='Population vs Bus Stop Coverage',
        labels={
            'population': 'Total Population',
            'stops_per_1000': 'Bus Stops per 1,000 Residents',
            'total_stops': 'Total Stops'
        },
        hover_data=['region_name', 'total_stops', 'routes_count'],
        size_max=60
    )

    fig.update_layout(
        height=500,
        font=dict(size=12, family="Inter, sans-serif"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    # Add trend line
    if len(data) > 2:
        z = np.polyfit(data['population'], data['stops_per_1000'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(data['population'].min(), data['population'].max(), 100)
        fig.add_scatter(
            x=x_trend,
            y=p(x_trend),
            mode='lines',
            name='Trend',
            line=dict(dash='dash', color='gray')
        )

    return fig

with st.spinner("Analyzing population-service mismatch..."):
    density_data = load_filtered_data(filter_mode, filter_value)

    if not density_data.empty and filter_mode == 'all_regions':
        fig = create_density_scatter(density_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # Calculate correlation
        if len(density_data) > 2:
            corr = density_data[['population', 'stops_per_1000']].corr().iloc[0, 1]

            st.markdown("### Analysis")
            if abs(corr) > 0.7:
                st.success(f"**Strong correlation detected:** r = {corr:.3f}. Bus stop provision generally matches population size.")
            elif abs(corr) > 0.4:
                st.warning(f"**Moderate correlation:** r = {corr:.3f}. Some regions may be under or over-served relative to population.")
            else:
                st.error(f"**Weak correlation:** r = {corr:.3f}. Service provision does not consistently match population density across regions.")

            # Identify outliers
            data_with_residuals = density_data.copy()
            if len(data_with_residuals) > 2:
                z = np.polyfit(data_with_residuals['population'], data_with_residuals['stops_per_1000'], 1)
                p = np.poly1d(z)
                data_with_residuals['expected_stops'] = p(data_with_residuals['population'])
                data_with_residuals['residual'] = data_with_residuals['stops_per_1000'] - data_with_residuals['expected_stops']

                underserved = data_with_residuals[data_with_residuals['residual'] < -2].sort_values('residual')
                if not underserved.empty:
                    st.markdown("**Underserved Regions (below trend line):**")
                    for _, row in underserved.iterrows():
                        st.markdown(f"- **{row['region_name']}**: {row['stops_per_1000']:.1f} stops/1000 (expected: {row['expected_stops']:.1f})")
    elif not density_data.empty:
        st.info("📊 **Note:** Population-service mismatch analysis is only available in 'All Regions' comparison mode. This section requires multiple regions for correlation analysis.")
    else:
        st.error("Insufficient data for density analysis")

st.markdown("---")


# ============================================================================
# SECTION A4: Service Desert Identification
# ============================================================================

st.header("📊 A4: Stop Coverage Distribution")
st.markdown("*How are bus stops distributed across local areas (LSOAs)?*")

def analyze_stop_distribution(filter_mode, filter_value):
    """Analyze distribution of stops across LSOAs in our dataset"""
    # Load stops data based on filter mode
    if filter_mode == 'all_regions':
        stops_data = load_regional_stops()
    elif filter_mode == 'region':
        stops_data = load_regional_stops(filter_value)
    elif filter_mode in ['all_urban', 'all_rural']:
        # All urban or all rural across all regions
        stops_data = load_regional_stops()
        if not stops_data.empty and 'UrbanRural (name)' in stops_data.columns:
            if 'urban' in filter_mode:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Urban', case=False, na=False)]['lsoa_code'].unique()
            else:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Rural', case=False, na=False)]['lsoa_code'].unique()
            stops_data = stops_data[stops_data['lsoa_code'].isin(lsoa_list)]
    elif filter_mode in ['region_urban', 'region_rural']:
        # Specific region's urban or rural
        stops_data = load_regional_stops(filter_value)
        if not stops_data.empty and 'UrbanRural (name)' in stops_data.columns:
            if 'urban' in filter_mode:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Urban', case=False, na=False)]['lsoa_code'].unique()
            else:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Rural', case=False, na=False)]['lsoa_code'].unique()
            stops_data = stops_data[stops_data['lsoa_code'].isin(lsoa_list)]
    else:
        stops_data = pd.DataFrame()

    if stops_data.empty:
        return pd.DataFrame(), {}

    # Get unique LSOAs with their population
    lsoa_info = stops_data[['lsoa_code', 'total_population', 'region_code']].drop_duplicates('lsoa_code')

    # Count stops per LSOA
    stops_per_lsoa = stops_data.groupby('lsoa_code').size().reset_index(name='stop_count')

    # Merge to get LSOAs with stop counts
    lsoa_coverage = lsoa_info.merge(stops_per_lsoa, on='lsoa_code', how='left')
    lsoa_coverage['stop_count'] = lsoa_coverage['stop_count'].fillna(0).astype(int)

    # Calculate statistics
    total_lsoas = len(lsoa_coverage)
    lsoas_with_stops = (lsoa_coverage['stop_count'] > 0).sum()
    lsoas_no_stops = (lsoa_coverage['stop_count'] == 0).sum()

    # Low coverage = 1-3 stops
    low_coverage = ((lsoa_coverage['stop_count'] >= 1) & (lsoa_coverage['stop_count'] <= 3)).sum()

    # Good coverage = 4+ stops
    good_coverage = (lsoa_coverage['stop_count'] >= 4).sum()

    stats = {
        'total_lsoas': total_lsoas,
        'lsoas_with_stops': lsoas_with_stops,
        'lsoas_no_stops': lsoas_no_stops,
        'low_coverage_lsoas': low_coverage,
        'good_coverage_lsoas': good_coverage,
        'pct_with_stops': (lsoas_with_stops / total_lsoas * 100) if total_lsoas > 0 else 0,
        'pct_no_stops': (lsoas_no_stops / total_lsoas * 100) if total_lsoas > 0 else 0,
        'avg_stops_per_lsoa': lsoa_coverage['stop_count'].mean(),
        'median_stops_per_lsoa': lsoa_coverage['stop_count'].median(),
        'total_population': lsoa_coverage['total_population'].sum(),
        'pop_no_stops': lsoa_coverage[lsoa_coverage['stop_count'] == 0]['total_population'].sum()
    }

    return lsoa_coverage, stats

with st.spinner("Analyzing stop coverage distribution..."):
    lsoa_data, coverage_stats = analyze_stop_distribution(filter_mode, filter_value)

    if not lsoa_data.empty:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total LSOAs Analyzed", f"{coverage_stats['total_lsoas']:,}")
        with col2:
            st.metric("LSOAs with Zero Stops", f"{coverage_stats['lsoas_no_stops']:,}",
                     delta=f"{coverage_stats['pct_no_stops']:.1f}%")
        with col3:
            st.metric("Avg Stops per LSOA", f"{coverage_stats['avg_stops_per_lsoa']:.1f}")
        with col4:
            st.metric("Population in Zero-Stop LSOAs", f"{coverage_stats['pop_no_stops']:,.0f}")

        # Coverage breakdown
        st.markdown("### Coverage Categories")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("No Coverage (0 stops)",
                     f"{coverage_stats['lsoas_no_stops']:,}",
                     delta=f"{coverage_stats['pct_no_stops']:.1f}%")
        with col2:
            st.metric("Low Coverage (1-3 stops)",
                     f"{coverage_stats['low_coverage_lsoas']:,}")
        with col3:
            st.metric("Good Coverage (4+ stops)",
                     f"{coverage_stats['good_coverage_lsoas']:,}")

        # Visualize distribution
        fig = px.histogram(
            lsoa_data[lsoa_data['stop_count'] <= 30],  # Cap for readability
            x='stop_count',
            nbins=30,
            title='Distribution of Bus Stops per LSOA',
            labels={'stop_count': 'Number of Bus Stops per LSOA', 'count': 'Number of LSOAs'},
            color_discrete_sequence=['#16a34a']
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            font=dict(size=12, family="Inter, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Analysis
        st.markdown("### Analysis")
        if coverage_stats['pct_no_stops'] > 5:
            st.error(f"**Significant coverage gaps:** {coverage_stats['pct_no_stops']:.1f}% of analyzed LSOAs have zero bus stops, affecting {coverage_stats['pop_no_stops']:,.0f} residents.")
        elif coverage_stats['pct_no_stops'] > 1:
            st.warning(f"**Some coverage gaps:** {coverage_stats['pct_no_stops']:.1f}% of LSOAs have no stops, affecting {coverage_stats['pop_no_stops']:,.0f} people.")
        else:
            st.success(f"**Excellent coverage:** Only {coverage_stats['pct_no_stops']:.1f}% of LSOAs have zero stops.")

        st.info(f"""
        **Interpretation:**
        - This analysis covers **{coverage_stats['total_lsoas']:,} LSOAs** with demographic data in our regional dataset
        - **{coverage_stats['pct_with_stops']:.1f}%** of these LSOAs have at least one bus stop
        - Average: {coverage_stats['avg_stops_per_lsoa']:.1f} stops per LSOA | Median: {coverage_stats['median_stops_per_lsoa']:.0f} stops
        - Total population analyzed: {coverage_stats['total_population']:,.0f}
        """)
    else:
        st.error("Unable to load LSOA-level data")

st.markdown("---")


# ============================================================================
# SECTION A5: Walking Distance Analysis
# ============================================================================

st.header("📊 A5: Walking Distance Analysis")
st.markdown("*What is the average distance from a household to the nearest bus stop in each region?*")

def calculate_lsoa_to_nearest_stop_distance(filter_mode, filter_value):
    """Calculate actual distance from each LSOA centroid to nearest bus stop"""
    from scipy.spatial import cKDTree

    # Load stops based on filter mode
    if filter_mode == 'all_regions':
        stops_data = load_regional_stops()
    elif filter_mode == 'region':
        stops_data = load_regional_stops(filter_value)
    elif filter_mode in ['all_urban', 'all_rural']:
        # All urban or all rural across all regions
        stops_data = load_regional_stops()
        if not stops_data.empty and 'UrbanRural (name)' in stops_data.columns:
            if 'urban' in filter_mode:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Urban', case=False, na=False)]['lsoa_code'].unique()
            else:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Rural', case=False, na=False)]['lsoa_code'].unique()
            stops_data = stops_data[stops_data['lsoa_code'].isin(lsoa_list)]
    elif filter_mode in ['region_urban', 'region_rural']:
        # Specific region's urban or rural
        stops_data = load_regional_stops(filter_value)
        if not stops_data.empty and 'UrbanRural (name)' in stops_data.columns:
            if 'urban' in filter_mode:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Urban', case=False, na=False)]['lsoa_code'].unique()
            else:
                lsoa_list = stops_data[stops_data['UrbanRural (name)'].str.contains('Rural', case=False, na=False)]['lsoa_code'].unique()
            stops_data = stops_data[stops_data['lsoa_code'].isin(lsoa_list)]
    else:
        stops_data = pd.DataFrame()

    if stops_data.empty:
        return pd.DataFrame()

    # Load LSOA centroids
    lsoa_centroids_raw = pd.read_csv('data/raw/boundaries/lsoa_names_codes.csv')
    lsoa_centroids = lsoa_centroids_raw[['LSOA21CD', 'LAT', 'LONG']].rename(columns={
        'LSOA21CD': 'lsoa_code',
        'LAT': 'lat',
        'LONG': 'lon'
    })

    # Filter to only LSOAs in our stops data
    unique_lsoas = stops_data['lsoa_code'].unique()
    lsoa_centroids = lsoa_centroids[lsoa_centroids['lsoa_code'].isin(unique_lsoas)]

    if lsoa_centroids.empty:
        return pd.DataFrame()

    # Get unique stops with coordinates
    stops_coords = stops_data[['stop_id', 'latitude', 'longitude', 'region_code']].drop_duplicates('stop_id')
    stops_coords = stops_coords.dropna(subset=['latitude', 'longitude'])

    if len(stops_coords) == 0:
        return pd.DataFrame()

    # Build KDTree for efficient nearest-neighbor search
    # Convert lat/lon to approximate meters (1 degree ~= 111km)
    stop_coords_array = stops_coords[['latitude', 'longitude']].values * 111000  # Convert to meters

    tree = cKDTree(stop_coords_array)

    # Calculate distance from each LSOA centroid to nearest stop
    lsoa_distances = []

    for _, lsoa in lsoa_centroids.iterrows():
        lsoa_coord = np.array([lsoa['lat'], lsoa['lon']]) * 111000  # Convert to meters
        distance, _ = tree.query(lsoa_coord)

        lsoa_distances.append({
            'lsoa_code': lsoa['lsoa_code'],
            'nearest_stop_distance_m': distance
        })

    distance_df = pd.DataFrame(lsoa_distances)

    # Get region info and urban/rural classification from stops
    lsoa_info = stops_data[['lsoa_code', 'region_code', 'total_population', 'UrbanRural (name)']].drop_duplicates('lsoa_code')
    distance_df = distance_df.merge(lsoa_info, on='lsoa_code', how='left')

    return distance_df

with st.spinner("Calculating actual walking distances using coordinates..."):
    lsoa_distances = calculate_lsoa_to_nearest_stop_distance(filter_mode, filter_value)

    if not lsoa_distances.empty:
        # Calculate regional averages
        regional_avg = lsoa_distances.groupby('region_code').agg({
            'nearest_stop_distance_m': 'mean',
            'total_population': 'sum'
        }).reset_index()

        # Map region codes to names
        region_name_map = dict(zip(REGION_CODES.values(), REGION_CODES.keys()))
        regional_avg['region_name'] = regional_avg['region_code'].map(region_name_map)
        regional_avg = regional_avg.dropna(subset=['region_name'])

        # Visualize
        regional_avg_sorted = regional_avg.sort_values('nearest_stop_distance_m', ascending=False)

        fig = px.bar(
            regional_avg_sorted,
            y='region_name',
            x='nearest_stop_distance_m',
            orientation='h',
            title='Average Distance from LSOA Centroid to Nearest Bus Stop',
            labels={'nearest_stop_distance_m': 'Average Distance (meters)', 'region_name': ''},
            color='nearest_stop_distance_m',
            color_continuous_scale='RdYlGn_r',
            text='nearest_stop_distance_m'
        )

        fig.update_traces(texttemplate='%{text:.0f}m', textposition='outside')
        fig.update_layout(
            height=500,
            showlegend=False,
            font=dict(size=12, family="Inter, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        # Add 400m DfT accessibility standard
        fig.add_vline(
            x=400,
            line_dash="dash",
            line_color="red",
            annotation_text="400m DfT Standard",
            annotation_position="top"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Analysis")

        regions_above_400 = regional_avg_sorted[regional_avg_sorted['nearest_stop_distance_m'] > 400]

        if len(regions_above_400) > 0:
            st.warning(f"**{len(regions_above_400)} regions exceed the 400m DfT accessibility standard** (average LSOA-to-stop distance).")
            for _, row in regions_above_400.iterrows():
                st.markdown(f"- **{row['region_name']}**: {row['nearest_stop_distance_m']:.0f}m average")
        else:
            st.success("✅ All regions meet the 400m walking distance standard on average.")

        # Show distribution
        st.markdown("### Distance Distribution")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            within_400 = (lsoa_distances['nearest_stop_distance_m'] <= 400).sum()
            pct_400 = (within_400 / len(lsoa_distances) * 100)
            st.metric("LSOAs within 400m", f"{pct_400:.1f}%")
        with col2:
            within_800 = (lsoa_distances['nearest_stop_distance_m'] <= 800).sum()
            pct_800 = (within_800 / len(lsoa_distances) * 100)
            st.metric("LSOAs within 800m", f"{pct_800:.1f}%")
        with col3:
            median_dist = lsoa_distances['nearest_stop_distance_m'].median()
            st.metric("Median Distance", f"{median_dist:.0f}m")
        with col4:
            max_dist = lsoa_distances['nearest_stop_distance_m'].max()
            st.metric("Maximum Distance", f"{max_dist:.0f}m")
    else:
        st.error("Unable to calculate walking distances - coordinate data unavailable")

st.markdown("---")


# ============================================================================
# SECTION A6: Accessibility Standard Compliance
# ============================================================================

st.header("📊 A6: Accessibility Standard Compliance")
st.markdown("*Which regions fail the DfT 400m accessibility standard?*")

st.info("""
**DfT Accessibility Standard:** Residents should live within 400m of a bus stop with at least hourly service.

This analysis uses LSOA centroid distances as a proxy for population accessibility.
""")

with st.spinner("Analyzing accessibility standard compliance..."):
    # Reuse A5's distance calculations
    lsoa_distances_a6 = calculate_lsoa_to_nearest_stop_distance(filter_mode, filter_value)

    if not lsoa_distances_a6.empty:
        # Classify LSOAs by compliance (using 400m and 500m thresholds)
        lsoa_distances_a6['compliant_400m'] = lsoa_distances_a6['nearest_stop_distance_m'] <= 400
        lsoa_distances_a6['compliant_500m'] = lsoa_distances_a6['nearest_stop_distance_m'] <= 500

        # Group by region
        compliance_by_region = lsoa_distances_a6.groupby('region_code').agg({
            'compliant_400m': 'mean',  # % compliant
            'compliant_500m': 'mean',
            'total_population': 'sum',
            'lsoa_code': 'count'  # Total LSOAs
        }).reset_index()

        compliance_by_region.columns = ['region_code', 'pct_within_400m', 'pct_within_500m', 'population', 'n_lsoas']
        compliance_by_region['pct_within_400m'] *= 100
        compliance_by_region['pct_within_500m'] *= 100

        # Map to region names
        region_name_map = dict(zip(REGION_CODES.values(), REGION_CODES.keys()))
        compliance_by_region['region_name'] = compliance_by_region['region_code'].map(region_name_map)
        compliance_by_region = compliance_by_region.dropna(subset=['region_name'])

        # Visualize
        compliance_sorted = compliance_by_region.sort_values('pct_within_400m', ascending=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=compliance_sorted['region_name'],
            x=compliance_sorted['pct_within_400m'],
            name='Within 400m (DfT Standard)',
            orientation='h',
            marker_color='#16a34a',
            text=compliance_sorted['pct_within_400m'].round(1),
            texttemplate='%{text}%',
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            y=compliance_sorted['region_name'],
            x=compliance_sorted['pct_within_500m'],
            name='Within 500m',
            orientation='h',
            marker_color='#eab308',
            text=compliance_sorted['pct_within_500m'].round(1),
            texttemplate='%{text}%',
            textposition='outside',
            visible='legendonly'  # Hidden by default
        ))

        fig.update_layout(
            title='Accessibility Standard Compliance by Region',
            xaxis_title="% of LSOAs Meeting Standard",
            yaxis_title="",
            height=500,
            barmode='group',
            font=dict(size=12, family="Inter, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True
        )

        # Add 50% compliance threshold line
        fig.add_vline(
            x=50,
            line_dash="dash",
            line_color="red",
            annotation_text="50% Threshold",
            annotation_position="top"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Compliance Summary")

        # Identify non-compliant regions
        non_compliant = compliance_sorted[compliance_sorted['pct_within_400m'] < 50]

        if len(non_compliant) > 0:
            st.error(f"**{len(non_compliant)} regions fail the 50% compliance threshold** (less than half of LSOAs within 400m of a bus stop):")
            for _, row in non_compliant.iterrows():
                st.markdown(f"- **{row['region_name']}**: Only {row['pct_within_400m']:.1f}% of LSOAs within 400m ({row['n_lsoas']} LSOAs analyzed)")
        else:
            st.success("✅ All regions meet the minimum 50% compliance threshold for the 400m DfT standard.")

        # National summary
        st.markdown("### National Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            national_400 = (lsoa_distances_a6['compliant_400m'].sum() / len(lsoa_distances_a6) * 100)
            st.metric("National: Within 400m", f"{national_400:.1f}%")
        with col2:
            national_500 = (lsoa_distances_a6['compliant_500m'].sum() / len(lsoa_distances_a6) * 100)
            st.metric("National: Within 500m", f"{national_500:.1f}%")
        with col3:
            total_analyzed = len(lsoa_distances_a6)
            st.metric("LSOAs Analyzed", f"{total_analyzed:,}")
    else:
        st.error("Unable to calculate accessibility compliance - distance data unavailable")

st.markdown("---")


# ============================================================================
# SECTION A7: Urban-Rural Coverage Disparity
# ============================================================================

st.header("📊 A7: Urban-Rural Coverage Disparity")
st.markdown("*How does bus coverage vary between urban and rural areas?*")

def analyze_urban_rural_coverage(filter_mode, filter_value):
    """Analyze coverage by urban/rural classification using ONS RUC data"""
    # Load stops based on filter (only makes sense for all_regions or single region)
    if filter_mode == 'all_regions':
        stops_data = load_regional_stops()
    elif filter_mode == 'region':
        stops_data = load_regional_stops(filter_value)
    else:
        # For urban/rural specific filters, this analysis is redundant
        return None, None

    if stops_data.empty or 'UrbanRural (name)' not in stops_data.columns:
        return None, None

    # Get unique LSOAs to avoid double-counting
    lsoa_classification = stops_data[['lsoa_code', 'UrbanRural (name)', 'total_population']].drop_duplicates('lsoa_code')

    # Count stops per LSOA
    stops_per_lsoa = stops_data.groupby('lsoa_code').agg({
        'stop_id': 'count'
    }).reset_index()
    stops_per_lsoa.columns = ['lsoa_code', 'stop_count']

    # Merge
    lsoa_with_stops = lsoa_classification.merge(stops_per_lsoa, on='lsoa_code', how='left')
    lsoa_with_stops['stop_count'] = lsoa_with_stops['stop_count'].fillna(0)

    # Group by urban/rural classification
    ur_analysis = lsoa_with_stops.groupby('UrbanRural (name)').agg({
        'stop_count': 'sum',
        'total_population': 'sum',
        'lsoa_code': 'count'
    }).reset_index()

    ur_analysis.columns = ['classification', 'stop_count', 'population', 'n_lsoas']
    ur_analysis['stops_per_1000'] = (ur_analysis['stop_count'] / ur_analysis['population']) * 1000

    # Also get LSOA-level data for detailed metrics
    return ur_analysis, lsoa_with_stops

with st.spinner("Analyzing urban-rural disparities..."):
    ur_data, lsoa_detail = analyze_urban_rural_coverage(filter_mode, filter_value)

    if filter_mode in ['all_urban', 'all_rural', 'region_urban', 'region_rural']:
        st.info(f"📊 **Note:** Urban-Rural disparity analysis is not available when viewing '{filter_display}'. This section compares urban vs rural areas, so it requires either 'All Regions' or a specific region (with 'All' urban/rural) to be selected.")
    elif ur_data is not None and not ur_data.empty:
        # Visualization
        ur_sorted = ur_data.sort_values('stops_per_1000', ascending=False)

        fig = px.bar(
            ur_sorted,
            x='classification',
            y='stops_per_1000',
            title='Bus Stops per 1,000 Population by ONS Urban-Rural Classification',
            labels={'stops_per_1000': 'Stops per 1,000 Population', 'classification': ''},
            color='stops_per_1000',
            color_continuous_scale='Greens',
            text='stops_per_1000',
            hover_data=['stop_count', 'population', 'n_lsoas']
        )

        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(
            height=500,
            showlegend=False,
            font=dict(size=12, family="Inter, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)

        # Analysis
        st.markdown("### Disparity Analysis")

        # Calculate urban vs rural average
        urban_mask = ur_data['classification'].str.contains('Urban', case=False, na=False)
        rural_mask = ur_data['classification'].str.contains('Rural', case=False, na=False)

        urban_avg = ur_data[urban_mask]['stops_per_1000'].mean()
        rural_avg = ur_data[rural_mask]['stops_per_1000'].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Urban Average", f"{urban_avg:.1f} stops/1000")
        with col2:
            st.metric("Rural Average", f"{rural_avg:.1f} stops/1000")
        with col3:
            if urban_avg > 0 and rural_avg > 0:
                disparity_ratio = urban_avg / rural_avg
                st.metric("Disparity Ratio", f"{disparity_ratio:.2f}x")

        if urban_avg > 0 and rural_avg > 0:
            st.markdown("---")
            disparity_ratio = urban_avg / rural_avg

            if disparity_ratio > 3:
                st.error(f"**Significant rural service gap identified.** Urban areas have {disparity_ratio:.1f}x more stops per capita than rural areas. This indicates severe accessibility challenges in rural communities.")
                st.markdown("""
                **Policy Recommendations:**
                - Implement demand-responsive transport (DRT) schemes in rural areas
                - Invest in community transport and dial-a-ride services
                - Integrate rural bus services with rail networks
                - Explore digital booking platforms for flexible rural services
                """)
            elif disparity_ratio > 2:
                st.warning(f"**Moderate rural service gap.** Urban areas have {disparity_ratio:.1f}x more stops per capita. Rural areas are underserved relative to urban centers.")
            else:
                st.success(f"**Relatively balanced urban-rural coverage** (disparity ratio: {disparity_ratio:.2f}x)")

        # Show detailed table
        with st.expander("📊 Detailed Classification Breakdown"):
            display_df = ur_sorted[['classification', 'stops_per_1000', 'stop_count', 'population', 'n_lsoas']].copy()
            display_df.columns = ['Classification', 'Stops per 1,000', 'Total Stops', 'Population', 'LSOAs']
            display_df['Population'] = display_df['Population'].apply(lambda x: f"{x:,.0f}")
            display_df['Total Stops'] = display_df['Total Stops'].apply(lambda x: f"{x:,.0f}")
            display_df['Stops per 1,000'] = display_df['Stops per 1,000'].apply(lambda x: f"{x:.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ **Urban-Rural classification data not available** in the current dataset. Ensure ONS Rural-Urban Classification has been linked to stops data during preprocessing.")

st.markdown("---")


# ============================================================================
# SECTION A8: Population-Service Mismatch Zones
# ============================================================================

st.header("📊 A8: Population-Service Mismatch Zones")
st.markdown("*Are there regions with high population but minimal bus services?*")

def identify_mismatch_zones(data):
    """Identify regions with high population but low service"""
    if data.empty:
        return None

    data_calc = data.copy()

    # Calculate mismatch score (high population, low stops)
    # Normalize both metrics to 0-1 scale
    data_calc['pop_normalized'] = (data_calc['population'] - data_calc['population'].min()) / (data_calc['population'].max() - data_calc['population'].min())
    data_calc['stops_normalized'] = (data_calc['stops_per_1000'] - data_calc['stops_per_1000'].min()) / (data_calc['stops_per_1000'].max() - data_calc['stops_per_1000'].min())

    # Mismatch score: high when population is high but stops are low
    data_calc['mismatch_score'] = data_calc['pop_normalized'] - data_calc['stops_normalized']

    return data_calc

with st.spinner("Identifying population-service mismatch zones..."):
    mismatch_data = load_filtered_data(filter_mode, filter_value)

    if filter_mode != 'all_regions':
        st.info("📊 **Note:** Population-service mismatch analysis is only available in 'All Regions' comparison mode. This section requires multiple regions for mismatch scoring.")
    elif not mismatch_data.empty:
        mismatch_analysis = identify_mismatch_zones(mismatch_data)

        if mismatch_analysis is not None:
            # Create bubble chart
            fig = px.scatter(
                mismatch_analysis,
                x='population',
                y='stops_per_1000',
                size='total_stops',
                color='mismatch_score',
                hover_data=['region_name', 'routes_count'],
                title='Population vs Service Provision (bubble size = total stops)',
                labels={
                    'population': 'Total Population',
                    'stops_per_1000': 'Stops per 1,000 Residents',
                    'mismatch_score': 'Mismatch Score'
                },
                color_continuous_scale='RdYlGn_r',
                size_max=60
            )

            fig.update_layout(
                height=500,
                font=dict(size=12, family="Inter, sans-serif"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Identify priority zones (high mismatch score)
            priority_zones = mismatch_analysis.nlargest(3, 'mismatch_score')

            st.markdown("### Priority Investment Zones")
            st.markdown("*Regions with high population but low service provision:*")

            for _, row in priority_zones.iterrows():
                st.markdown(f"""
                **{row['region_name']}**
                - Population: {row['population']:,.0f}
                - Stops per 1,000: {row['stops_per_1000']:.1f}
                - Mismatch Score: {row['mismatch_score']:.2f}
                - **Recommendation:** Increase stop density and route coverage to match population demand
                """)

st.markdown("---")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("### 📚 About This Analysis")
st.markdown("""
This Coverage & Accessibility dashboard analyzes 767,011 bus stops across 9 English regions,
integrating NaPTAN, BODS, and ONS demographic data. All narratives are dynamically generated
using the InsightEngine with TAG 2024 economic values and HM Treasury Green Book methodology.

**Data Scope:**
- **Geographic coverage**: England only (9 regions)
- **Bus stops analyzed**: 767,011 (October 2025 BODS snapshot)
- **LSOAs analyzed**: 33,755 England LSOAs (ONS 2021 boundaries)
- **Population scope**: 34.8M people living in LSOAs with bus service (61.7% of England's 56.5M population)
  - Note: The remaining 21.7M people live in LSOAs with zero bus stops (service deserts)
- **Demographic integration**: 97-99% match rate for LSOAs with stops

**Methodology:**
- TAG 2024 time values and carbon pricing (DfT WebTAG)
- HM Treasury Green Book BCR methodology
- ONS Census 2021 population data
- Statistical significance testing (p < 0.05)
- Evidence-gated insights (only data-supported findings shown)
- All per-capita metrics use population in LSOAs with bus service (not total England population)

**Data Sources:**
- Bus stops: BODS (Bus Open Data Service) TransXChange files, October 2025
- Demographics: ONS Census 2021 LSOA-level data
- Boundaries: ONS 2021 LSOA boundaries (England E-codes only)
- Standards: DfT Accessibility Guidelines, TAG 2024, HM Treasury Green Book
""")
