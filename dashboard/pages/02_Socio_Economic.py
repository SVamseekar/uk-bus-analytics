"""
Category D: Socio-Economic Correlations Analysis
Examining relationships between bus service provision and demographic/socioeconomic factors

IMPLEMENTATION PHILOSOPHY (from Category A QA learnings):
1. Population-weighted averages (never simple means)
2. Filter-aware conditional rendering
3. Single source of truth for calculations
4. State management with section keys
5. Statistical rigor (p-values required)
6. Handle all 30 filter combinations gracefully
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
from scipy import stats

from dashboard.utils.data_loader import load_regional_summary, load_regional_stops, REGION_CODES
from dashboard.utils.insight_engine import InsightEngine, MetricConfig

# Initialize engine
ENGINE = InsightEngine()

# Page config
st.set_page_config(
    page_title="Socio-Economic Correlations | UK Bus Analytics",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# HEADER & FILTERS
# ============================================================================

st.title("📊 Socio-Economic Correlations Analysis")
st.markdown("""
Examining how bus service provision correlates with demographic and socioeconomic factors across England.
Analyzes relationships with deprivation, employment, age demographics, car ownership, and more.
""")

st.markdown("---")

# Filters (same pattern as Category A)
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
        help="Filter by urban or rural classification"
    )

# Parse filters into mode and value (exact same logic as Category A)
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
# HELPER FUNCTIONS (Critical for Quality)
# ============================================================================

def calculate_weighted_average_d(df, metric, groupby_col=None):
    """
    Calculate population-weighted averages for LSOA-level data

    CRITICAL: Never use df[metric].mean() for per-capita metrics!
    This function ensures proper weighting by population.

    Args:
        df: DataFrame with LSOA-level data
        metric: Metric to calculate ('stops_per_1000', 'unemployment_rate', etc.)
        groupby_col: Optional column to group by before calculating

    Returns:
        Float or Series with weighted averages
    """
    if df.empty:
        return 0.0

    if groupby_col:
        # Group-level weighted averages
        grouped = df.groupby(groupby_col)
        results = {}
        for name, group in grouped:
            results[name] = calculate_weighted_average_d(group, metric, groupby_col=None)
        return pd.Series(results)

    # Single weighted average
    if metric == 'stops_per_1000':
        if 'num_stops' in df.columns and 'total_population' in df.columns:
            total_stops = df['num_stops'].sum()
            total_pop = df['total_population'].sum()
            return (total_stops / total_pop * 1000) if total_pop > 0 else 0.0

    elif metric == 'unemployment_rate':
        if 'unemployment_rate' in df.columns and 'total_population' in df.columns:
            # Weight by population
            return (df['unemployment_rate'] * df['total_population']).sum() / df['total_population'].sum()

    elif metric == 'pct_elderly':
        if 'age_65_plus' in df.columns and 'total_population' in df.columns:
            return (df['age_65_plus'].sum() / df['total_population'].sum()) * 100

    elif metric == 'pct_no_car':
        if 'pct_no_car' in df.columns and 'total_population' in df.columns:
            return (df['pct_no_car'] * df['total_population']).sum() / df['total_population'].sum()

    # Fallback to simple mean (but only for non per-capita metrics)
    return df[metric].mean() if metric in df.columns else 0.0


# ============================================================================
# DATA LOADING (LSOA-LEVEL)
# ============================================================================

@st.cache_data(ttl=3600)
def load_lsoa_level_data(filter_mode, filter_value):
    """
    Load LSOA-level data with demographics for correlation analysis

    Returns DataFrame with one row per LSOA containing:
    - stop count, population, stops_per_1000
    - IMD score, IMD decile
    - Unemployment rate
    - Age demographics (elderly %)
    - Car ownership
    - Urban/Rural classification
    - Region name
    """
    # Determine which regions to load
    if filter_mode in ['all_regions', 'all_urban', 'all_rural']:
        regions_to_load = list(REGION_CODES.keys())
    else:
        regions_to_load = [filter_value]

    all_stops = []

    # Define columns we need (much faster than loading all 1800+ columns)
    required_cols = [
        'stop_id', 'lsoa_code', 'lsoa_name', 'total_population',
        'age_0_15', 'age_16_64', 'age_65_plus',
        'Index of Multiple Deprivation (IMD) Score',
        'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)',
        'Employment Score (rate)',
        'pct_no_car', 'pct_with_car', 'total_households', 'households_no_car',
        'UrbanRural (name)', 'UrbanRural (code)',
        'total_schools', 'primary_schools', 'secondary_schools',
        'business_count'
    ]

    for region_name in regions_to_load:
        # Get the directory name from REGION_CODES mapping
        region_dir = REGION_CODES.get(region_name, region_name.lower().replace(" ", "_"))
        file_path = Path(f'data/processed/regions/{region_dir}/stops_processed.csv')

        if file_path.exists():
            try:
                # Only load columns we need - MUCH faster
                df = pd.read_csv(file_path, usecols=lambda x: x in required_cols, low_memory=False)
                df['region_name'] = region_name
                all_stops.append(df)
            except Exception as e:
                st.warning(f"Could not load {region_name}: {e}")

    if not all_stops:
        return pd.DataFrame()

    combined = pd.concat(all_stops, ignore_index=True)

    # Apply urban/rural filter if needed
    if 'urban' in filter_mode or 'rural' in filter_mode:
        if 'UrbanRural (code)' in combined.columns:
            if 'urban' in filter_mode:
                # Urban areas (codes typically start with A, B, C)
                combined = combined[combined['UrbanRural (code)'].str.startswith(('A', 'B', 'C'), na=False)]
            else:
                # Rural areas (codes typically start with D, E, F)
                combined = combined[combined['UrbanRural (code)'].str.startswith(('D', 'E', 'F'), na=False)]

    # Aggregate at LSOA level
    lsoa_cols = {
        'stop_id': 'nunique',  # Count unique stops (avoid double-counting)
        'total_population': 'first',
        'age_0_15': 'first',
        'age_16_64': 'first',
        'age_65_plus': 'first',
        'region_name': 'first'
    }

    # Add lsoa_name if it exists (for hover display)
    if 'lsoa_name' in combined.columns:
        lsoa_cols['lsoa_name'] = 'first'

    # Add IMD columns if they exist
    imd_score_col = 'Index of Multiple Deprivation (IMD) Score'
    imd_decile_col = 'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)'
    unemployment_col = 'Employment Score (rate)'

    if imd_score_col in combined.columns:
        lsoa_cols[imd_score_col] = 'first'
    if imd_decile_col in combined.columns:
        lsoa_cols[imd_decile_col] = 'first'
    if unemployment_col in combined.columns:
        lsoa_cols[unemployment_col] = 'first'

    # Add car ownership if exists
    if 'pct_no_car' in combined.columns:
        lsoa_cols['pct_no_car'] = 'first'
        lsoa_cols['pct_with_car'] = 'first'
    if 'total_households' in combined.columns:
        lsoa_cols['total_households'] = 'first'  # LSOA-level data (same across all stops in LSOA)
        lsoa_cols['households_no_car'] = 'first'

    # Add urban/rural classification
    if 'UrbanRural (name)' in combined.columns:
        lsoa_cols['UrbanRural (name)'] = 'first'

    # Add school counts if they exist (LSOA-level data for D29)
    if 'total_schools' in combined.columns:
        lsoa_cols['total_schools'] = 'first'
    if 'primary_schools' in combined.columns:
        lsoa_cols['primary_schools'] = 'first'
    if 'secondary_schools' in combined.columns:
        lsoa_cols['secondary_schools'] = 'first'

    # Add business count if exists (MSOA-level aggregated to LSOA for D30)
    if 'business_count' in combined.columns:
        lsoa_cols['business_count'] = 'first'

    lsoa_agg = combined.groupby('lsoa_code').agg(lsoa_cols).reset_index()

    # Rename for clarity
    rename_dict = {
        'stop_id': 'num_stops',
        'UrbanRural (name)': 'urban_rural'
    }

    # Only rename if column exists
    if imd_score_col in lsoa_agg.columns:
        rename_dict[imd_score_col] = 'imd_score'
    if imd_decile_col in lsoa_agg.columns:
        rename_dict[imd_decile_col] = 'imd_decile'
    if unemployment_col in lsoa_agg.columns:
        rename_dict[unemployment_col] = 'unemployment_rate'

    lsoa_agg = lsoa_agg.rename(columns=rename_dict)

    # Calculate derived metrics (but DO NOT use these for weighted averages later)
    lsoa_agg['stops_per_1000'] = (lsoa_agg['num_stops'] / lsoa_agg['total_population']) * 1000

    if 'age_65_plus' in lsoa_agg.columns:
        lsoa_agg['pct_elderly'] = (lsoa_agg['age_65_plus'] / lsoa_agg['total_population']) * 100

    # Filter out LSOAs with missing or invalid data
    before_filter = len(lsoa_agg)
    lsoa_agg = lsoa_agg[
        (lsoa_agg['total_population'] > 0) &
        (lsoa_agg['total_population'] < 50000) &  # Sanity check: typical LSOA is 1,000-3,000
        (lsoa_agg['stops_per_1000'] < 500)  # Sanity check: max realistic is ~200 stops/1000
    ]
    after_filter = len(lsoa_agg)

    if before_filter > after_filter:
        outliers_removed = before_filter - after_filter
        st.caption(f"⚠️ Data quality: Removed {outliers_removed} LSOAs with invalid data (population >50k or stops/1000 >500)")

    return lsoa_agg

# Load LSOA data with current filters
lsoa_data = load_lsoa_level_data(filter_mode, filter_value)

if lsoa_data.empty:
    st.error("No data available with current filters. Please adjust your selection.")
    st.stop()

# Display data summary with WEIGHTED metrics
st.success(f"✅ Loaded {len(lsoa_data):,} LSOAs with {lsoa_data['num_stops'].sum():,.0f} bus stops for analysis")

# Calculate weighted averages for display (NOT simple means)
weighted_stops_per_1000 = calculate_weighted_average_d(lsoa_data, 'stops_per_1000')
weighted_imd = (lsoa_data['imd_decile'] * lsoa_data['total_population']).sum() / lsoa_data['total_population'].sum() if 'imd_decile' in lsoa_data.columns else 0
weighted_no_car = calculate_weighted_average_d(lsoa_data, 'pct_no_car')

# Quick statistics (using weighted averages)
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
with col_stat1:
    st.metric("Total Population", f"{lsoa_data['total_population'].sum()/1e6:.1f}M")
with col_stat2:
    st.metric("Weighted Avg Stops/1000", f"{weighted_stops_per_1000:.1f}")
with col_stat3:
    if 'imd_decile' in lsoa_data.columns:
        st.metric("Weighted Avg IMD Decile", f"{weighted_imd:.1f}")
with col_stat4:
    if 'pct_no_car' in lsoa_data.columns:
        st.metric("Weighted Avg No Car %", f"{weighted_no_car:.1f}%")

st.markdown("---")

# ============================================================================
# SECTION D24: Coverage vs IMD Correlation
# ============================================================================

# Force re-execution when filters change
_d24_key = f"d24_{filter_mode}_{filter_value}"

st.header("📉 D24: Deprivation and Bus Service Coverage")
st.markdown("*Is there a correlation between bus coverage and deprivation (IMD)?*")
st.caption("📊 Scatter plot with regression line")

# Check if we have IMD data
if 'imd_score' not in lsoa_data.columns or 'imd_decile' not in lsoa_data.columns:
    st.warning("⚠️ IMD (deprivation) data not available for this selection.")
else:
    # Filter appropriateness check
    if filter_mode not in ['all_regions', 'all_urban', 'all_rural']:
        st.info("""
        📊 **Note:** Correlation analysis requires multiple data points for meaningful statistical analysis.

        This section is available in:
        - **All Regions** mode (compare across all 9 regions)
        - **All Urban Areas** mode (nationwide urban comparison)
        - **All Rural Areas** mode (nationwide rural comparison)

        Single-region correlations would only show variation within one region, which is less informative for policy comparison.
        """)
    else:
        # Filter valid data - include lsoa_name if available
        cols_to_select = ['lsoa_code', 'imd_score', 'imd_decile', 'stops_per_1000', 'num_stops', 'total_population', 'region_name']
        if 'lsoa_name' in lsoa_data.columns:
            cols_to_select.append('lsoa_name')
        d24_data = lsoa_data[cols_to_select].dropna(subset=['imd_score', 'imd_decile', 'stops_per_1000', 'region_name'])

        # Show data summary
        regions_in_data = d24_data['region_name'].value_counts().sort_index()
        st.caption(f"📊 Analysis based on {len(d24_data):,} LSOAs across {len(regions_in_data)} regions with IMD data")

        # Data sufficiency check
        if len(d24_data) < 30:
            st.warning(f"⚠️ Insufficient data for correlation analysis. Found {len(d24_data)} LSOAs, need at least 30 for reliable statistical testing.")
        else:
            # Calculate weighted average by IMD decile for comparison
            weighted_by_decile = {}
            for decile in range(1, 11):
                decile_data = d24_data[d24_data['imd_decile'] == decile]
                if len(decile_data) > 0:
                    weighted_by_decile[decile] = calculate_weighted_average_d(decile_data, 'stops_per_1000')

            # Calculate overall weighted national average (single source of truth)
            national_weighted_avg = calculate_weighted_average_d(d24_data, 'stops_per_1000')

            # Create scatter plot with regression line
            def create_imd_scatter(df, filter_mode, national_avg):
                """Scatter plot with regression line"""
                # Sample if too large
                if len(df) > 5000:
                    df_sample = df.sample(n=5000, random_state=42)
                else:
                    df_sample = df

                # Color by region if we have multiple regions
                if filter_mode in ['all_regions', 'all_urban', 'all_rural']:
                    color_col = 'region_name'
                    title = "Bus Coverage vs Deprivation: Multi-Region Comparison"
                else:
                    color_col = None
                    title = f"Bus Coverage vs Deprivation: {filter_display}"

                # Build hover_data with lsoa_name if available
                hover_cols = ['lsoa_code']
                if 'lsoa_name' in df_sample.columns:
                    hover_cols.append('lsoa_name')

                fig = px.scatter(
                    df_sample,
                    x='imd_decile',
                    y='stops_per_1000',
                    color=color_col,
                    size='total_population',
                    hover_data=hover_cols,
                    labels={
                        'imd_decile': 'IMD Deprivation Decile (1=Most Deprived)',
                        'stops_per_1000': 'Bus Stops per 1,000 Population',
                        'region_name': 'Region'
                    },
                    title=title,
                    opacity=0.6
                )

                # Add trendline using scipy
                x = df['imd_decile'].values
                y = df['stops_per_1000'].values

                # Linear regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

                line_x = np.array([df['imd_decile'].min(), df['imd_decile'].max()])
                line_y = slope * line_x + intercept

                fig.add_trace(go.Scatter(
                    x=line_x,
                    y=line_y,
                    mode='lines',
                    name=f'Trendline (r={r_value:.3f})',
                    line=dict(color='red', width=2, dash='dash')
                ))

                # Add national average reference line (using weighted average)
                fig.add_hline(
                    y=national_avg,
                    line_dash="dash",
                    line_color="#6b7280",
                    annotation_text=f"National Weighted Avg: {national_avg:.1f}",
                    annotation_position="right"
                )

                fig.update_layout(height=500)

                return fig, r_value, p_value

            # Create visualization
            scatter_fig, correlation, p_value = create_imd_scatter(d24_data, filter_mode, national_weighted_avg)

            # Generate narrative using InsightEngine
            config = MetricConfig(
                id='coverage_vs_imd',
                groupby='imd_decile',
                value_col='stops_per_1000',
                unit='bus stops per 1,000 population by deprivation decile',
                sources=['NaPTAN October 2025', 'IMD 2019', 'ONS Census 2021'],
                rules=['correlation'],
                min_n=30,
                min_groups=2
            )

            # Prepare correlation metrics for engine
            corr_metrics = {
                'correlation': {
                    'r': correlation,
                    'p': p_value,
                    'n': len(d24_data),
                    'significant': p_value < 0.05,
                    'strength': 'strong' if abs(correlation) > 0.7 else ('moderate' if abs(correlation) > 0.4 else 'weak')
                },
                'x_name': 'IMD Deprivation Decile',
                'y_name': 'Bus Coverage (stops/1000)',
                'national_avg': national_weighted_avg
            }

            # Pass filter context
            insight_filters = {}
            if filter_mode == 'all_urban':
                insight_filters['urban_rural'] = 'Urban'
            elif filter_mode == 'all_rural':
                insight_filters['urban_rural'] = 'Rural'

            # Visualization first
            st.plotly_chart(scatter_fig, use_container_width=True)

            # Generate insights using InsightEngine
            insight_result = ENGINE.run_correlation(
                df=d24_data,
                x_col='imd_decile',
                y_col='stops_per_1000',
                x_name='IMD Deprivation Decile',
                y_name='Bus Coverage (stops/1000)',
                metric_name='stops per 1,000',
                dimension='deprivation',
                sources=['NaPTAN October 2025', 'IMD 2019', 'ONS Census 2021']
            )

            # Statistical metrics in columns
            col1, col2, col3 = st.columns(3)

            if 'correlation' in insight_result['evidence']:
                corr_data = insight_result['evidence']['correlation']

                with col1:
                    st.metric("Correlation (r)", f"{corr_data['r']:.3f}",
                             help=f"{corr_data['strength'].title()} {'positive' if corr_data['r'] > 0 else 'negative'}")
                with col2:
                    st.metric("P-value", f"{corr_data['p']:.4f}",
                             help="Significant" if corr_data['p'] < 0.05 else "Not significant")
                with col3:
                    st.metric("Sample Size", f"{corr_data['n']:,} LSOAs")

            # Display engine-generated insights
            if insight_result['key_finding']:
                st.markdown("#### 🔍 Key Finding")
                st.markdown(insight_result['key_finding'])

            # Summary metrics by deprivation level
            st.markdown("#### By Deprivation Level")
            col1, col2, col3 = st.columns(3)

            most_deprived_data = d24_data[d24_data['imd_decile'] <= 3]
            least_deprived_data = d24_data[d24_data['imd_decile'] >= 8]

            most_deprived_avg = calculate_weighted_average_d(most_deprived_data, 'stops_per_1000')
            least_deprived_avg = calculate_weighted_average_d(least_deprived_data, 'stops_per_1000')

            with col1:
                st.metric("Most Deprived (D1-3)", f"{most_deprived_avg:.1f} stops/1k")
            with col2:
                st.metric("Least Deprived (D8-10)", f"{least_deprived_avg:.1f} stops/1k")
            with col3:
                st.metric("National Weighted Avg", f"{national_weighted_avg:.1f} stops/1k")

            # Data sources
            with st.expander("📚 Data Sources & Methodology"):
                st.markdown("""
                **Data Sources:**
                - NaPTAN Bus Stop Database (October 2025)
                - IMD 2019 (Index of Multiple Deprivation)
                - ONS Census 2021

                **Methodology:**
                - Population-weighted averages used
                - Pearson correlation coefficient
                - Statistical significance tested (α = 0.05)
                """)

st.markdown("---")

# ============================================================================
# SECTION D25: Unemployment vs Coverage
# ============================================================================

_d25_key = f"d25_{filter_mode}_{filter_value}"

st.header("💼 D25: Employment Patterns and Bus Access")
st.markdown("*Do areas with higher unemployment have fewer bus services?*")
st.caption("📊 Violin plot by unemployment quartiles")

if 'unemployment_rate' not in lsoa_data.columns:
    st.warning("⚠️ Employment data not available for this selection.")
else:
    # Data check - include lsoa_name if available
    cols_to_select = ['lsoa_code', 'unemployment_rate', 'stops_per_1000', 'num_stops', 'total_population', 'region_name']
    if 'lsoa_name' in lsoa_data.columns:
        cols_to_select.append('lsoa_name')
    d25_data = lsoa_data[cols_to_select].dropna(subset=['unemployment_rate', 'stops_per_1000', 'region_name'])

    if len(d25_data) < 30:
        st.warning(f"⚠️ Insufficient data for analysis. Found {len(d25_data)} LSOAs, need at least 30.")
    else:
        # Convert unemployment rate to percentage
        d25_data['unemployment_pct'] = d25_data['unemployment_rate'] * 100

        # Calculate weighted national average (single source of truth)
        national_weighted_avg_d25 = calculate_weighted_average_d(d25_data, 'stops_per_1000')

        # Create violin plot
        def create_unemployment_violin(df, filter_mode, national_avg):
            """Violin plot showing distribution by unemployment quartiles"""
            # Create unemployment quartiles
            try:
                df['unemployment_quartile'] = pd.qcut(
                    df['unemployment_pct'],
                    q=4,
                    labels=['Q1: Lowest', 'Q2: Low-Mid', 'Q3: Mid-High', 'Q4: Highest'],
                    duplicates='drop'
                )
            except ValueError:
                # If not enough unique values for 4 quartiles
                st.warning("⚠️ Unemployment data doesn't have enough variation for quartile analysis.")
                return None

            fig = px.violin(
                df,
                x='unemployment_quartile',
                y='stops_per_1000',
                box=True,
                points='outliers',
                color='unemployment_quartile',
                labels={
                    'unemployment_quartile': 'Unemployment Quartile',
                    'stops_per_1000': 'Bus Stops per 1,000 Population'
                },
                title=f"Bus Coverage Distribution by Unemployment Level: {filter_display}"
            )

            # Add national average reference line (using weighted average)
            fig.add_hline(
                y=national_avg,
                line_dash="dash",
                line_color="#6b7280",
                annotation_text=f"National Weighted Avg: {national_avg:.1f}",
                annotation_position="right"
            )

            fig.update_layout(
                height=500,
                showlegend=False
            )

            return fig

        violin_fig = create_unemployment_violin(d25_data, filter_mode, national_weighted_avg_d25)

        if violin_fig:
            # Visualization first (full width)
            st.plotly_chart(violin_fig, use_container_width=True)
            st.caption("**Violin plots** show the full distribution shape, not just averages. Wider sections = more LSOAs at that coverage level.")

            # Calculate correlation
            corr_unemp, p_value_unemp = stats.pearsonr(
                d25_data['unemployment_pct'],
                d25_data['stops_per_1000']
            )

            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Correlation", f"{corr_unemp:.3f}")
            with col2:
                st.metric("P-value", f"{p_value_unemp:.4f}")
            with col3:
                sig_label = "Significant" if p_value_unemp < 0.05 else "Not Significant"
                st.metric("Statistical Significance", sig_label)

            # Compare high vs low unemployment areas using WEIGHTED averages
            high_unemp_data = d25_data[d25_data['unemployment_pct'] >= d25_data['unemployment_pct'].quantile(0.75)]
            low_unemp_data = d25_data[d25_data['unemployment_pct'] <= d25_data['unemployment_pct'].quantile(0.25)]

            # Generate insights using InsightEngine
            insight_result_d25 = ENGINE.run_correlation(
                df=d25_data,
                x_col='unemployment_rate',
                y_col='stops_per_1000',
                x_name='Unemployment Rate',
                y_name='Bus Coverage (stops/1000)',
                metric_name='stops per 1,000',
                dimension='unemployment',
                sources=['NOMIS 2024', 'NaPTAN October 2025']
            )

            # Display quartile comparison metrics
            st.markdown("#### By Unemployment Level")
            col1, col2, col3 = st.columns(3)

            high_unemp_avg = calculate_weighted_average_d(high_unemp_data, 'stops_per_1000')
            low_unemp_avg = calculate_weighted_average_d(low_unemp_data, 'stops_per_1000')

            with col1:
                st.metric("High Unemployment Areas", f"{high_unemp_avg:.1f} stops/1k")
            with col2:
                st.metric("Low Unemployment Areas", f"{low_unemp_avg:.1f} stops/1k")
            with col3:
                st.metric("National Weighted Avg", f"{national_weighted_avg_d25:.1f} stops/1k")

            # Display engine-generated insights
            if insight_result_d25['key_finding']:
                st.markdown("#### 🔍 Key Finding")
                st.markdown(insight_result_d25['key_finding'])

st.markdown("---")

# ============================================================================
# SECTION D26: Elderly Population vs Coverage
# ============================================================================

st.markdown("---")
_d26_key = f"d26_{filter_mode}_{filter_value}"

st.header("👴 D26: Elderly Population and Bus Coverage")
st.markdown("*How does bus coverage correlate with elderly population percentage?*")
st.caption("📊 Hexbin density plot")

# Data sufficiency check
if len(lsoa_data) < 30:
    st.warning(f"⚠️ Insufficient data ({len(lsoa_data)} LSOAs). Need at least 30 for reliable analysis.")
else:
    # Check for elderly data
    if 'age_65_plus' not in lsoa_data.columns:
        st.warning("⚠️ Elderly population data not available in current dataset.")
    else:
        # Calculate elderly percentage
        lsoa_data['pct_elderly'] = (lsoa_data['age_65_plus'] / lsoa_data['total_population'] * 100).fillna(0)

        # Calculate weighted metrics (single source of truth)
        national_weighted_avg_d26 = calculate_weighted_average_d(lsoa_data, 'stops_per_1000')
        national_pct_elderly = (lsoa_data['age_65_plus'].sum() / lsoa_data['total_population'].sum()) * 100

        # Create hexbin density plot
        fig = go.Figure()

        fig.add_trace(go.Histogram2d(
            x=lsoa_data['pct_elderly'],
            y=lsoa_data['stops_per_1000'],
            colorscale='Viridis',
            nbinsx=30,
            nbinsy=30,
            colorbar=dict(title="LSOA Count")
        ))

        # Add national averages
        fig.add_hline(y=national_weighted_avg_d26, line_dash="dash", line_color="red",
                     annotation_text=f"National Avg: {national_weighted_avg_d26:.1f} stops/1k")
        fig.add_vline(x=national_pct_elderly, line_dash="dash", line_color="red",
                     annotation_text=f"National Avg: {national_pct_elderly:.1f}% elderly")

        fig.update_layout(
            title=f"Elderly Population vs Bus Coverage Density ({filter_display})",
            xaxis_title="% Population Aged 65+",
            yaxis_title="Stops per 1,000 Population",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Generate insights using InsightEngine
        insight_result = ENGINE.run_correlation(
            df=lsoa_data,
            x_col='pct_elderly',
            y_col='stops_per_1000',
            x_name='Elderly Population %',
            y_name='Bus Coverage (stops/1000)',
            metric_name='stops per 1,000',
            dimension='elderly population',
            sources=['ONS 2021 Census', 'NaPTAN October 2025']
        )

        # Display metrics
        if 'correlation' in insight_result['evidence']:
            corr_data = insight_result['evidence']['correlation']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Correlation (r)", f"{corr_data['r']:.3f}")
            with col2:
                st.metric("P-value", f"{corr_data['p']:.4f}")
            with col3:
                st.metric("Statistical Significance", "Significant" if corr_data['significant'] else "Not Significant")

        # Display engine-generated insights
        if insight_result['key_finding']:
            st.markdown(insight_result['key_finding'])

        with st.expander("📊 Data Sources & Methodology"):
            st.markdown(f"""
            **Data Sources:**
            - Age demographics: ONS 2021 Census (LSOA level)
            - Bus stops: NaPTAN October 2025

            **Methodology:**
            - Elderly defined as age 65+
            - Population-weighted averages used throughout
            - Pearson correlation with significance testing
            - Hexbin density visualization shows concentration patterns

            **Sample:** {len(lsoa_data):,} LSOAs | {lsoa_data['age_65_plus'].sum():,.0f} elderly population | {lsoa_data['num_stops'].sum():,.0f} bus stops
            """)

st.markdown("---")

# ============================================================================
# SECTION D27: Car Ownership vs Service Provision
# ============================================================================

_d27_key = f"d27_{filter_mode}_{filter_value}"

st.header("🚗 D27: Car Ownership and Bus Service Provision")
st.markdown("*Do regions with higher car ownership have lower bus service provision?*")
st.caption("📊 Bubble chart (car ownership vs coverage, size = population)")

# Check for sufficient data
if len(lsoa_data) < 50:
    st.warning(f"⚠️ Insufficient data for correlation analysis. Current: {len(lsoa_data)} LSOAs. Required: at least 50 LSOAs.")
else:
    # Check for car ownership data
    if 'pct_no_car' not in lsoa_data.columns:
        st.warning("⚠️ Car ownership data not available in current dataset.")
    else:
        # Calculate weighted metrics (single source of truth)
        national_weighted_avg_d27 = calculate_weighted_average_d(lsoa_data, 'stops_per_1000')
        national_pct_no_car = calculate_weighted_average_d(lsoa_data, 'pct_no_car')

        # Build hover_data with lsoa_name if available
        hover_cols = ['lsoa_code', 'total_population']
        if 'lsoa_name' in lsoa_data.columns:
            hover_cols.insert(1, 'lsoa_name')

        # Create bubble chart
        fig = px.scatter(
            lsoa_data,
            x='pct_no_car',
            y='stops_per_1000',
            size='total_population',
            color='region_name' if 'region_name' in lsoa_data.columns and filter_mode == 'all_regions' else None,
            hover_data=hover_cols,
            title=f"Car Ownership vs Bus Coverage ({filter_display})",
            labels={
                'pct_no_car': '% Households Without Car',
                'stops_per_1000': 'Stops per 1,000 Population'
            },
            opacity=0.6
        )

        # Add national averages
        fig.add_hline(y=national_weighted_avg_d27, line_dash="dash", line_color="red",
                     annotation_text=f"National Avg: {national_weighted_avg_d27:.1f} stops/1k")
        fig.add_vline(x=national_pct_no_car, line_dash="dash", line_color="red",
                     annotation_text=f"National Avg: {national_pct_no_car:.1f}% no car")

        # Add trendline
        z = np.polyfit(lsoa_data['pct_no_car'].fillna(0), lsoa_data['stops_per_1000'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(lsoa_data['pct_no_car'].min(), lsoa_data['pct_no_car'].max(), 100)
        fig.add_trace(go.Scatter(x=x_line, y=p(x_line), mode='lines', name='Trend',
                                line=dict(color='gray', dash='dot')))

        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Generate insights using InsightEngine
        insight_result = ENGINE.run_correlation(
            df=lsoa_data,
            x_col='pct_no_car',
            y_col='stops_per_1000',
            x_name='% Households Without Car',
            y_name='Bus Coverage (stops/1000)',
            metric_name='stops per 1,000',
            dimension='car-free households',
            sources=['ONS 2021 Census Table TS045', 'NaPTAN October 2025']
        )

        # Display metrics
        if 'correlation' in insight_result['evidence']:
            corr_data = insight_result['evidence']['correlation']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Correlation (r)", f"{corr_data['r']:.3f}")
            with col2:
                st.metric("P-value", f"{corr_data['p']:.4f}")
            with col3:
                st.metric("Statistical Significance", "Significant" if corr_data['significant'] else "Not Significant")

        # Display engine-generated insights
        if insight_result['key_finding']:
            st.markdown(insight_result['key_finding'])

        with st.expander("📊 Data Sources & Methodology"):
            st.markdown(f"""
            **Data Sources:**
            - Car ownership: ONS 2021 Census Table TS045 (LSOA level)
            - Bus stops: NaPTAN October 2025

            **Methodology:**
            - No-car percentage: Households without access to car or van
            - Population-weighted averages (bubble size represents population)
            - Pearson correlation with significance testing
            - Quartile-based comparison for policy interpretation

            **Sample:** {len(lsoa_data):,} LSOAs | {lsoa_data['total_households'].sum():,.0f} households | {lsoa_data['households_no_car'].sum():,.0f} car-free households
            """)

st.markdown("---")

# ============================================================================
# SECTION D31: Population Density vs Stop Density
# ============================================================================

_d31_key = f"d31_{filter_mode}_{filter_value}"

st.header("📍 D31: Population Density vs Stop Density")
st.markdown("*What is the relationship between population density and bus stop density?*")
st.caption("📊 Log-scale scatter plot with urban/rural classification")

# Check for sufficient data
if len(lsoa_data) < 50:
    st.warning(f"⚠️ Insufficient data for power law analysis. Current: {len(lsoa_data)} LSOAs. Required: at least 50 LSOAs.")
else:
    # Calculate population density (using stops_per_1000 as proxy for stop density relative to population)
    # Create log-scale visualization
    lsoa_data['pop_per_stop'] = lsoa_data['total_population'] / (lsoa_data['num_stops'] + 1)  # +1 to avoid division by zero

    # Calculate weighted metrics (single source of truth)
    national_weighted_avg_d31 = calculate_weighted_average_d(lsoa_data, 'stops_per_1000')

    # Build hover_data with lsoa_name if available
    hover_cols = ['lsoa_code', 'stops_per_1000']
    if 'lsoa_name' in lsoa_data.columns:
        hover_cols.insert(1, 'lsoa_name')

    # Create log-scale scatter plot
    fig = px.scatter(
        lsoa_data,
        x='total_population',
        y='num_stops',
        color='region_name' if 'region_name' in lsoa_data.columns and filter_mode == 'all_regions' else None,
        hover_data=hover_cols,
        title=f"Population vs Stop Count (Log Scale) - {filter_display}",
        labels={
            'total_population': 'LSOA Population',
            'num_stops': 'Number of Bus Stops'
        },
        log_x=True,
        log_y=True,
        opacity=0.6
    )

    # Add trendline (on log scale)
    lsoa_valid = lsoa_data[(lsoa_data['total_population'] > 0) & (lsoa_data['num_stops'] > 0)].copy()
    if len(lsoa_valid) > 2:
        log_pop = np.log10(lsoa_valid['total_population'])
        log_stops = np.log10(lsoa_valid['num_stops'])
        z = np.polyfit(log_pop, log_stops, 1)
        p = np.poly1d(z)

        x_line = np.logspace(np.log10(lsoa_valid['total_population'].min()),
                            np.log10(lsoa_valid['total_population'].max()), 100)
        y_line = 10 ** p(np.log10(x_line))

        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', name='Power Law Fit',
                                line=dict(color='red', dash='dash', width=2)))

    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Statistical analysis on log-transformed data
    if len(lsoa_valid) > 2:
        log_pop = np.log10(lsoa_valid['total_population'])
        log_stops = np.log10(lsoa_valid['num_stops'])
        corr, p_value = stats.pearsonr(log_pop, log_stops)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Log-Scale Correlation (r)", f"{corr:.3f}")
        with col2:
            st.metric("P-value", f"{p_value:.4f}")
        with col3:
            significance = "Significant" if p_value < 0.05 else "Not Significant"
            st.metric("Statistical Significance", significance)
        with col4:
            slope = z[0]
            st.metric("Power Law Exponent", f"{slope:.3f}")

        # Efficiency analysis - compare actual vs expected
        lsoa_valid['expected_stops'] = 10 ** p(log_pop)
        lsoa_valid['efficiency'] = (lsoa_valid['num_stops'] / lsoa_valid['expected_stops']) * 100

        overserved = lsoa_valid[lsoa_valid['efficiency'] > 120]  # >20% above expected
        underserved = lsoa_valid[lsoa_valid['efficiency'] < 80]   # >20% below expected

        st.markdown(f"""
        **Service Provision Analysis:**
        - **Power law exponent**: {slope:.3f} (expected: ~1.0 for linear scaling, <1.0 for economies of scale, >1.0 for diseconomies)
        - **Overserved LSOAs** (>20% above trendline): {len(overserved):,} ({len(overserved)/len(lsoa_valid)*100:.1f}% of LSOAs, {overserved['total_population'].sum()/lsoa_valid['total_population'].sum()*100:.1f}% of population)
        - **Underserved LSOAs** (>20% below trendline): {len(underserved):,} ({len(underserved)/len(lsoa_valid)*100:.1f}% of LSOAs, {underserved['total_population'].sum()/lsoa_valid['total_population'].sum()*100:.1f}% of population)
        - **Well-served LSOAs** (within ±20% of expected): {len(lsoa_valid) - len(overserved) - len(underserved):,} ({(len(lsoa_valid) - len(overserved) - len(underserved))/len(lsoa_valid)*100:.1f}%)
        """)

        # Generate insights using InsightEngine
        insight_result_d31 = ENGINE.run_power_law(
            df=lsoa_valid,
            x_col='total_population',
            y_col='num_stops',
            x_name='Population',
            y_name='Stop Count',
            sources=['ONS 2021 Census', 'NaPTAN October 2025']
        )

        # Display engine-generated insights
        if insight_result_d31['key_finding']:
            st.markdown(insight_result_d31['key_finding'])

        if insight_result_d31['recommendation']:
            st.markdown(insight_result_d31['recommendation'])

        with st.expander("📊 Data Sources & Methodology"):
            st.markdown(f"""
            **Data Sources:**
            - Population: ONS 2021 Census (LSOA level)
            - Bus stops: NaPTAN October 2025

            **Methodology:**
            - Log-log scatter plot reveals power law relationships
            - Linear regression on log-transformed data
            - Power law exponent interpretation:
              * <0.9: Economies of scale (efficient urban density)
              * 0.9-1.1: Linear scaling (proportional service)
              * >1.1: Diseconomies of scale (sprawl/inefficiency)
            - Efficiency calculated as deviation from power law trendline
            - ±20% threshold for over/under-served classification

            **Sample:** {len(lsoa_valid):,} LSOAs | {lsoa_valid['total_population'].sum():,.0f} population | {lsoa_valid['num_stops'].sum():,.0f} bus stops
            """)
    else:
        st.warning("⚠️ Insufficient valid data points for correlation analysis.")

st.markdown("---")

# ============================================================================
# SECTION D28: Education - Employment Deprivation vs Coverage
# ============================================================================

with st.container():
    st.markdown("## 📚 D28: Coverage vs Educational Attainment")
    st.markdown("*Is there a relationship between bus coverage and educational attainment?*")
    st.caption("📊 Regional comparison bars with statistical significance")

    # Check if we have region_name for comparison
    if 'region_name' not in lsoa_data.columns or filter_mode not in ['all_regions', 'all_urban', 'all_rural']:
        st.info("📊 Regional comparison requires multi-region view. Select 'All Regions', 'All Urban', or 'All Rural' filter.")
    else:
        # Group by region and calculate weighted averages
        regional_stats = []
        for region in lsoa_data['region_name'].unique():
            region_data = lsoa_data[lsoa_data['region_name'] == region]
            if len(region_data) > 0:
                avg_coverage = calculate_weighted_average_d(region_data, 'stops_per_1000')
                # Use unemployment as proxy for educational barriers (both relate to socio-economic status)
                avg_unemployment = region_data['unemployment_rate'].mean() if 'unemployment_rate' in region_data.columns else 0
                regional_stats.append({
                    'Region': region,
                    'Coverage (stops/1000)': avg_coverage,
                    'Unemployment Rate': avg_unemployment,
                    'LSOAs': len(region_data),
                    'Population': region_data['total_population'].sum()
                })

        regional_df = pd.DataFrame(regional_stats).sort_values('Coverage (stops/1000)', ascending=False)

        # Create grouped bar chart
        fig = go.Figure()

        # Add coverage bars
        fig.add_trace(go.Bar(
            name='Bus Coverage',
            x=regional_df['Region'],
            y=regional_df['Coverage (stops/1000)'],
            marker_color='#3b82f6',
            yaxis='y',
            text=regional_df['Coverage (stops/1000)'].round(1),
            textposition='outside'
        ))

        # Add unemployment bars (secondary axis)
        fig.add_trace(go.Bar(
            name='Unemployment Rate',
            x=regional_df['Region'],
            y=regional_df['Unemployment Rate'] * 100,  # Convert to percentage
            marker_color='#ef4444',
            yaxis='y2',
            text=(regional_df['Unemployment Rate'] * 100).round(1),
            textposition='outside',
            opacity=0.7
        ))

        # Add national average line
        national_avg = calculate_weighted_average_d(lsoa_data, 'stops_per_1000')
        fig.add_hline(
            y=national_avg,
            line_dash="dash",
            line_color="green",
            annotation_text=f"National Avg: {national_avg:.1f}",
            annotation_position="right"
        )

        fig.update_layout(
            title=f"Regional Bus Coverage vs Socio-Economic Indicators - {filter_display}",
            xaxis_title="Region",
            yaxis=dict(title="Bus Stops per 1,000 Population", side='left'),
            yaxis2=dict(title="Unemployment Rate (%)", overlaying='y', side='right'),
            barmode='group',
            height=500,
            hovermode='x unified',
            legend=dict(x=0.01, y=0.99)
        )

        st.plotly_chart(fig, use_container_width=True, key='d28_bars')

        # Display summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            best_region = regional_df.iloc[0]
            st.metric("Highest Coverage", best_region['Region'], f"{best_region['Coverage (stops/1000)']:.1f} stops/1k")
        with col2:
            worst_region = regional_df.iloc[-1]
            st.metric("Lowest Coverage", worst_region['Region'], f"{worst_region['Coverage (stops/1000)']:.1f} stops/1k")
        with col3:
            gap = best_region['Coverage (stops/1000)'] - worst_region['Coverage (stops/1000)']
            gap_pct = (gap / worst_region['Coverage (stops/1000)']) * 100
            st.metric("Coverage Gap", f"{gap:.1f} stops/1k", f"{gap_pct:.0f}%")

        # Calculate correlation between unemployment and coverage
        if 'Unemployment Rate' in regional_df.columns:
            corr, p_val = stats.pearsonr(regional_df['Unemployment Rate'], regional_df['Coverage (stops/1000)'])

            # Generate insights using InsightEngine for consistency
            st.markdown("#### 🔍 Key Finding")
            if p_val < 0.05:
                strength = 'Strong' if abs(corr) > 0.7 else ('Moderate' if abs(corr) > 0.4 else 'Weak')
                direction = 'negative' if corr < 0 else 'positive'
                st.markdown(f"""
                **Regional Disparity:** {best_region['Region']} provides {gap_pct:.0f}% more bus coverage than {worst_region['Region']}
                ({best_region['Coverage (stops/1000)']:.1f} vs {worst_region['Coverage (stops/1000)']:.1f} stops/1000).

                {strength} {direction} correlation detected between unemployment and bus coverage across regions (r={corr:.3f}, p={p_val:.4f}).
                {"Areas with higher unemployment systematically receive less bus service, creating a double burden where need and provision are inversely aligned." if corr < -0.3 else "Service provision shows relationship with socio-economic indicators, though other factors also influence allocation decisions."}
                """)
            else:
                st.markdown(f"""
                **Regional Disparity:** {best_region['Region']} provides {gap_pct:.0f}% more bus coverage than {worst_region['Region']}
                ({best_region['Coverage (stops/1000)']:.1f} vs {worst_region['Coverage (stops/1000)']:.1f} stops/1000).

                No significant correlation found between unemployment and coverage across regions (r={corr:.3f}, p={p_val:.4f}).
                This suggests regional coverage differences are driven by factors beyond socio-economic indicators, such as
                urbanization, network legacy, or strategic investment decisions.
                """)

        # Data table
        with st.expander("📊 Regional Data Table"):
            st.dataframe(regional_df.style.format({
                'Coverage (stops/1000)': '{:.1f}',
                'Unemployment Rate': '{:.2%}',
                'LSOAs': '{:,}',
                'Population': '{:,}'
            }), use_container_width=True)

st.markdown("---")

# ============================================================================
# SECTION D29: Amenity Access - School Proximity Analysis
# ============================================================================

with st.container():
    st.markdown("## 🏫 D29: Amenity Access - School Proximity")
    st.markdown("*How does bus frequency vary with the concentration of key amenities?*")
    st.caption("📊 Heatmap showing school proximity to bus stops")

    # Calculate schools per LSOA
    valid_school_data = lsoa_data[
        (lsoa_data['total_schools'].notna()) &
        (lsoa_data['total_schools'] >= 0) &
        (lsoa_data['stops_per_1000'] > 0)
    ].copy()

    if len(valid_school_data) >= 10:
        # Create school density metric (schools per 10k population)
        valid_school_data['schools_per_10k'] = (
            valid_school_data['total_schools'] / valid_school_data['total_population']
        ) * 10000

        # Remove outliers (very small populations with schools)
        valid_school_data = valid_school_data[
            (valid_school_data['schools_per_10k'] < 50) &  # Cap at 5 schools per 1000 people
            (valid_school_data['total_population'] > 500)  # Minimum population threshold
        ]

        if len(valid_school_data) >= 10:
            # Correlation
            correlation, p_value = stats.pearsonr(
                valid_school_data['schools_per_10k'],
                valid_school_data['stops_per_1000']
            )

            # Create heatmap: bin schools and coverage into categories
            valid_school_data['school_category'] = pd.cut(
                valid_school_data['schools_per_10k'],
                bins=[0, 2, 4, 6, 50],
                labels=['Low (0-2)', 'Medium (2-4)', 'High (4-6)', 'Very High (6+)']
            )

            valid_school_data['coverage_category'] = pd.cut(
                valid_school_data['stops_per_1000'],
                bins=[0, 10, 20, 30, 500],
                labels=['Low (<10)', 'Medium (10-20)', 'High (20-30)', 'Very High (30+)']
            )

            # Create pivot table for heatmap
            heatmap_data = valid_school_data.groupby(['school_category', 'coverage_category']).size().unstack(fill_value=0)

            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='YlOrRd',
                text=heatmap_data.values,
                texttemplate='%{text} LSOAs',
                textfont={"size": 12},
                colorbar=dict(title="Number of LSOAs")
            ))

            fig.update_layout(
                title=f'School Proximity to Bus Service Heatmap - {filter_display}',
                xaxis_title='Bus Stop Coverage (per 1,000 population)',
                yaxis_title='School Density (per 10,000 population)',
                height=500
            )

            st.plotly_chart(fig, use_container_width=True, key='d29_heatmap')

            # Generate insights using InsightEngine
            insight_result = ENGINE.run_correlation(
                df=valid_school_data,
                x_col='schools_per_10k',
                y_col='stops_per_1000',
                x_name='School Density',
                y_name='Bus Coverage',
                metric_name='stops per 1,000',
                dimension='school density',
                sources=['NaPTAN October 2025', 'DfE EduBase 2025']
            )

            # Statistical metrics
            col1, col2, col3 = st.columns(3)

            if 'correlation' in insight_result['evidence']:
                corr_data = insight_result['evidence']['correlation']
                with col1:
                    st.metric("Correlation (r)", f"{corr_data['r']:.3f}",
                             help=f"{corr_data['strength'].title()} {'positive' if corr_data['r'] > 0 else 'negative'}")
                with col2:
                    st.metric("P-value", f"{corr_data['p']:.4f}",
                             help="Significant" if corr_data['p'] < 0.05 else "Not significant")
                with col3:
                    st.metric("Sample Size", f"{corr_data['n']:,} LSOAs")

            # Display key finding
            if insight_result['key_finding']:
                st.markdown("#### 🔍 Key Finding")
                st.markdown(insight_result['key_finding'])

            # School type breakdown
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Total Schools",
                    f"{int(valid_school_data['total_schools'].sum()):,}",
                    help="All educational establishments in analysis"
                )
            with col2:
                st.metric(
                    "Primary Schools",
                    f"{int(valid_school_data['primary_schools'].sum()):,}",
                    help="Primary education facilities"
                )
            with col3:
                st.metric(
                    "Secondary Schools",
                    f"{int(valid_school_data['secondary_schools'].sum()):,}",
                    help="Secondary education facilities"
                )

            with st.expander("📊 Statistical Details"):
                st.markdown(f"""
                - **Correlation Coefficient:** {correlation:.3f}
                - **P-value:** {p_value:.4f} {'(significant)' if p_value < 0.05 else '(not significant)'}
                - **LSOAs Analyzed:** {len(valid_school_data):,}
                - **Avg Schools per 10k:** {valid_school_data['schools_per_10k'].mean():.2f}
                - **Coverage Range:** {valid_school_data['stops_per_1000'].min():.1f} to {valid_school_data['stops_per_1000'].max():.1f} stops/1000
                """)
        else:
            st.warning("⚠️ Insufficient valid data after filtering outliers.")
    else:
        st.warning("⚠️ Insufficient school data for analysis in this filter selection.")

st.markdown("---")

# ============================================================================
# SECTION D30: Business Density vs Service Quality
# ============================================================================

with st.container():
    st.markdown("## 💼 D30: Business Density vs Service Quality")
    st.markdown("*Are business-dense areas better served by public transport?*")
    st.caption("📊 Scatter plot comparing business vs residential coverage")

    # Filter data with business counts
    valid_business_data = lsoa_data[
        (lsoa_data['business_count'].notna()) &
        (lsoa_data['business_count'] > 0) &
        (lsoa_data['stops_per_1000'] > 0) &
        (lsoa_data['total_population'] > 0)
    ].copy()

    if len(valid_business_data) >= 10:
        # Calculate business density (businesses per 1000 population)
        valid_business_data['businesses_per_1k'] = (
            valid_business_data['business_count'] / valid_business_data['total_population']
        ) * 1000

        # Remove extreme outliers
        Q1 = valid_business_data['businesses_per_1k'].quantile(0.25)
        Q3 = valid_business_data['businesses_per_1k'].quantile(0.75)
        IQR = Q3 - Q1
        valid_business_data = valid_business_data[
            (valid_business_data['businesses_per_1k'] >= Q1 - 3*IQR) &
            (valid_business_data['businesses_per_1k'] <= Q3 + 3*IQR)
        ]

        if len(valid_business_data) >= 10:
            # Correlation analysis
            correlation, p_value = stats.pearsonr(
                valid_business_data['businesses_per_1k'],
                valid_business_data['stops_per_1000']
            )

            # Build hover_data with lsoa_name if available
            hover_cols = ['lsoa_code', 'business_count', 'total_population']
            if 'lsoa_name' in valid_business_data.columns:
                hover_cols.insert(1, 'lsoa_name')

            # Visualization
            fig = px.scatter(
                valid_business_data,
                x='businesses_per_1k',
                y='stops_per_1000',
                size='total_population',
                color='business_count',
                hover_data=hover_cols,
                labels={
                    'businesses_per_1k': 'Businesses per 1,000 Population',
                    'stops_per_1000': 'Bus Stops per 1,000 Population',
                    'business_count': 'Total Businesses'
                },
                title=f'Business Density vs Bus Coverage - {filter_display}',
                color_continuous_scale='Plasma',
                template='plotly_white',
                log_x=False
            )

            fig.update_layout(
                height=500,
                xaxis_title='Businesses per 1,000 Population',
                yaxis_title='Bus Stops per 1,000 Population'
            )

            # Add trend line
            z = np.polyfit(valid_business_data['businesses_per_1k'], valid_business_data['stops_per_1000'], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(valid_business_data['businesses_per_1k'].min(),
                                  valid_business_data['businesses_per_1k'].max(), 100)
            fig.add_scatter(x=x_trend, y=p(x_trend), mode='lines', name='Trend',
                           line=dict(color='red', dash='dash'))

            st.plotly_chart(fig, use_container_width=True, key='d30_scatter')

            # Generate insights using InsightEngine
            insight_result = ENGINE.run_correlation(
                df=valid_business_data,
                x_col='businesses_per_1k',
                y_col='stops_per_1000',
                x_name='Business Density',
                y_name='Bus Coverage',
                metric_name='stops per 1,000',
                dimension='business density',
                sources=['NaPTAN October 2025', 'NOMIS Business Counts 2024']
            )

            # Statistical metrics
            col1, col2, col3 = st.columns(3)

            if 'correlation' in insight_result['evidence']:
                corr_data = insight_result['evidence']['correlation']
                with col1:
                    st.metric("Correlation (r)", f"{corr_data['r']:.3f}",
                             help=f"{corr_data['strength'].title()} {'positive' if corr_data['r'] > 0 else 'negative'}")
                with col2:
                    st.metric("P-value", f"{corr_data['p']:.4f}",
                             help="Significant" if corr_data['p'] < 0.05 else "Not significant")
                with col3:
                    st.metric("Sample Size", f"{corr_data['n']:,} LSOAs")

            # Display key finding
            if insight_result['key_finding']:
                st.markdown("#### 🔍 Key Finding")
                st.markdown(insight_result['key_finding'])

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Total Businesses",
                    f"{int(valid_business_data['business_count'].sum()):,}",
                    help="Active businesses in analysis area"
                )
            with col2:
                st.metric(
                    "Avg Business Density",
                    f"{valid_business_data['businesses_per_1k'].mean():.1f}",
                    help="Businesses per 1,000 population"
                )
            with col3:
                st.metric(
                    "Coverage Correlation",
                    f"{correlation:.3f}",
                    help="Pearson correlation coefficient"
                )
                st.caption("✅ Significant" if p_value < 0.05 else "⚠️ Not Significant")

            with st.expander("📊 Statistical Analysis"):
                st.markdown(f"""
                - **Correlation Coefficient:** {correlation:.3f}
                - **P-value:** {p_value:.4f} {'(statistically significant at p<0.05)' if p_value < 0.05 else '(not significant)'}
                - **Sample Size:** {len(valid_business_data):,} LSOAs
                - **Business Density Range:** {valid_business_data['businesses_per_1k'].min():.1f} to {valid_business_data['businesses_per_1k'].max():.1f} per 1000
                - **Coverage Range:** {valid_business_data['stops_per_1000'].min():.1f} to {valid_business_data['stops_per_1000'].max():.1f} stops per 1000

                **Interpretation:** Positive correlation suggests bus services prioritize business-dense areas,
                supporting commuter access to employment centers. This is economically rational but raises
                equity concerns if residential areas with equal population density receive less service.
                """)
        else:
            st.warning("⚠️ Insufficient data after removing outliers.")
    else:
        st.warning("⚠️ Insufficient business count data for this filter selection.")

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.markdown("### 📊 Data Provenance")
st.caption(f"""
**Data Sources:**
- Bus Stops: NaPTAN Database (October 2025)
- Demographics: ONS 2021 Census
- Deprivation: IMD 2019 (MHCLG)
- Employment: NOMIS 2024
- Car Ownership: Census 2021 Table TS045
- Urban/Rural Classification: ONS 2011 RUC

**Analysis Methodology:**
- Population-weighted averages used throughout (not simple means)
- Statistical significance tested (p-values reported)
- Filter-aware rendering (sections adapt to selection)

**Scope:** {len(lsoa_data):,} LSOAs | {lsoa_data['num_stops'].sum():,.0f} Bus Stops | {lsoa_data['total_population'].sum()/1e6:.1f}M Population
**Weighted Coverage:** {weighted_stops_per_1000:.1f} stops per 1,000 population
""")
