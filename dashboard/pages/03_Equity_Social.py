"""
Category F: Equity & Social Inclusion Analysis
Examining fairness and accessibility of bus service distribution across demographic groups

IMPLEMENTATION PHILOSOPHY (from Categories A & D):
1. Population-weighted averages (never simple means)
2. Filter-aware conditional rendering
3. Single source of truth for calculations
4. State management with section keys
5. Statistical rigor (Gini coefficients, significance tests)
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

from dashboard.utils.data_loader import REGION_CODES

# Page config
st.set_page_config(
    page_title="Equity & Social Inclusion | UK Bus Analytics",
    page_icon="⚖️",
    layout="wide"
)

# ============================================================================
# HEADER & FILTERS
# ============================================================================

st.title("⚖️ Equity & Social Inclusion Analysis")
st.markdown("""
Examining the fairness and accessibility of bus service distribution across demographic groups,
income levels, and vulnerable populations.
""")

st.markdown("---")

# Filters (same pattern as Categories A & D)
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

# Parse filters into mode and value (exact same logic as Categories A & D)
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
# HELPER FUNCTIONS
# ============================================================================

def calculate_weighted_average_f(df, metric, groupby_col=None):
    """
    Calculate population-weighted averages for LSOA-level data

    CRITICAL: Never use df[metric].mean() for per-capita metrics!
    """
    if df.empty:
        return 0.0

    if groupby_col:
        grouped = df.groupby(groupby_col)
        results = {}
        for name, group in grouped:
            results[name] = calculate_weighted_average_f(group, metric, groupby_col=None)
        return pd.Series(results)

    # Single weighted average
    if metric == 'stops_per_1000':
        if 'num_stops' in df.columns and 'total_population' in df.columns:
            total_stops = df['num_stops'].sum()
            total_pop = df['total_population'].sum()
            return (total_stops / total_pop * 1000) if total_pop > 0 else 0.0

    return 0.0


def calculate_gini_coefficient(values, weights=None):
    """
    Calculate Gini coefficient for inequality measurement using standard formula

    Returns:
        float: Gini coefficient (0 = perfect equality, 1 = total inequality)
    """
    if len(values) == 0:
        return 0.0

    values = np.array(values)

    if weights is None:
        weights = np.ones(len(values))
    else:
        weights = np.array(weights)

    # Sort by values (ascending)
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]
    sorted_weights = weights[sorted_indices]

    # Total population and total service
    total_pop = sorted_weights.sum()
    total_service = (sorted_values * sorted_weights).sum()

    if total_pop == 0 or total_service == 0:
        return 0.0

    # Cumulative population share (X-axis of Lorenz curve)
    cum_pop_share = np.cumsum(sorted_weights) / total_pop
    cum_pop_share = np.insert(cum_pop_share, 0, 0)  # Add origin (0,0)

    # Cumulative service share (Y-axis of Lorenz curve)
    cum_service_share = np.cumsum(sorted_values * sorted_weights) / total_service
    cum_service_share = np.insert(cum_service_share, 0, 0)  # Add origin (0,0)

    # Calculate area under Lorenz curve using trapezoidal integration
    area_lorenz = np.trapz(cum_service_share, cum_pop_share)

    # Gini = 1 - 2 * Area under Lorenz curve
    # (Perfect equality has area = 0.5, so Gini = 0)
    gini = 1 - 2 * area_lorenz

    return max(0.0, min(1.0, gini))


def generate_lorenz_curve_data(values, weights=None):
    """Generate data for Lorenz curve visualization"""
    if len(values) == 0:
        return pd.DataFrame({'cum_pop_pct': [0, 100], 'cum_service_pct': [0, 100]})

    values = np.array(values)

    if weights is None:
        weights = np.ones(len(values))
    else:
        weights = np.array(weights)

    # Sort by values (ascending)
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]
    sorted_weights = weights[sorted_indices]

    # Total population and total service
    total_pop = sorted_weights.sum()
    total_service = (sorted_values * sorted_weights).sum()

    if total_pop == 0 or total_service == 0:
        return pd.DataFrame({'cum_pop_pct': [0, 100], 'cum_service_pct': [0, 100]})

    # Cumulative shares as percentages
    cum_pop_pct = (np.cumsum(sorted_weights) / total_pop) * 100
    cum_service_pct = (np.cumsum(sorted_values * sorted_weights) / total_service) * 100

    # Add origin point (0,0)
    cum_pop_pct = np.insert(cum_pop_pct, 0, 0)
    cum_service_pct = np.insert(cum_service_pct, 0, 0)

    return pd.DataFrame({
        'cum_pop_pct': cum_pop_pct,
        'cum_service_pct': cum_service_pct
    })


@st.cache_data(ttl=3600)
def load_gender_data_from_census():
    """
    Load gender demographics from Census 2021 MSOA data and map to LSOA codes

    The gender data is at MSOA (E02) level, but bus stops are at LSOA (E01) level.
    We use LSOA→MSOA lookup to map gender data to each LSOA.

    Returns: DataFrame with lsoa_code, male_population, female_population
    """
    try:
        # Load MSOA-level gender data
        gender_file = Path('data/raw/demographics/lsoa_population.csv')
        if not gender_file.exists():
            return pd.DataFrame()

        # Load gender data at MSOA level (E02 codes)
        msoa_gender = pd.read_csv(
            gender_file,
            usecols=[
                'geography code',
                'Gender: Male; Age: All Ages; measures: Value',
                'Gender: Female; Age: All Ages; measures: Value'
            ]
        )

        msoa_gender = msoa_gender.rename(columns={
            'geography code': 'msoa_code',
            'Gender: Male; Age: All Ages; measures: Value': 'male_population_msoa',
            'Gender: Female; Age: All Ages; measures: Value': 'female_population_msoa'
        })

        # Remove nulls
        msoa_gender = msoa_gender.dropna(subset=['male_population_msoa', 'female_population_msoa'])

        # Load LSOA→MSOA lookup table
        lookup_file = Path('data/raw/demographics/lsoa_to_msoa_lookup.csv')
        if not lookup_file.exists():
            return pd.DataFrame()

        lsoa_lookup = pd.read_csv(lookup_file)

        # Join: LSOA → MSOA → Gender data
        lsoa_gender = lsoa_lookup.merge(msoa_gender, on='msoa_code', how='left')

        # Each LSOA gets its parent MSOA's gender population
        # This is an approximation - ideally we'd have LSOA-level data
        lsoa_gender = lsoa_gender.rename(columns={
            'male_population_msoa': 'male_population',
            'female_population_msoa': 'female_population'
        })

        # Keep only LSOA code and gender columns
        lsoa_gender = lsoa_gender[['lsoa_code', 'male_population', 'female_population']].copy()

        return lsoa_gender

    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_ethnicity_data_from_census():
    """
    Load ethnicity demographics from Census 2021 TS021 at LSOA level

    Returns: DataFrame with lsoa_code and ethnic group percentages
    """
    try:
        ethnicity_file = Path('data/raw/demographics/ethnicity_lsoa_processed.csv')
        if not ethnicity_file.exists():
            return pd.DataFrame()

        ethnicity_df = pd.read_csv(ethnicity_file)

        # Keep only required columns
        cols_to_keep = [
            'lsoa_code',
            'total_population_ethnic',
            'ethnic_white', 'ethnic_bme', 'ethnic_asian', 'ethnic_black', 'ethnic_mixed', 'ethnic_other',
            'pct_white', 'pct_bme', 'pct_asian', 'pct_black', 'pct_mixed', 'pct_other'
        ]

        available_cols = [col for col in cols_to_keep if col in ethnicity_df.columns]
        ethnicity_df = ethnicity_df[available_cols].copy()

        # Mark that we have ethnicity data
        ethnicity_df['has_ethnicity_data'] = True

        return ethnicity_df

    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_lsoa_data_f(filter_mode, filter_value):
    """
    Load LSOA-level data for equity analysis
    Follows exact same pattern as Category D's load_lsoa_data_d()
    """
    # Determine which regions to load
    if filter_mode == 'all_regions' or 'all_' in filter_mode:
        regions_to_load = list(REGION_CODES.keys())
    else:
        regions_to_load = [filter_value]

    # Define columns we need (exclude gender cols - we'll join them separately)
    required_cols = [
        'stop_id', 'lsoa_code', 'lsoa_name',
        'total_population', 'age_0_15', 'age_16_64', 'age_65_plus',
        'Index of Multiple Deprivation (IMD) Score',
        'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)',
        'Employment Score (rate)',
        'Income Score (rate)',
        'Income Decile (where 1 is most deprived 10% of LSOAs)',
        'Health Deprivation and Disability Score',
        'Income Deprivation Affecting Older People (IDAOPI) Score (rate)',
        'UrbanRural (code)', 'UrbanRural (name)',
        'pct_no_car', 'pct_with_car', 'total_households', 'households_no_car'
    ]

    all_stops = []

    for region_name in regions_to_load:
        region_dir = REGION_CODES.get(region_name, region_name.lower().replace(" ", "_"))
        file_path = Path(f'data/processed/regions/{region_dir}/stops_processed.csv')

        if file_path.exists():
            try:
                df = pd.read_csv(file_path, usecols=lambda x: x in required_cols, low_memory=False)
                df['region_name'] = region_name
                all_stops.append(df)
            except Exception:
                pass

    if not all_stops:
        return pd.DataFrame()

    combined = pd.concat(all_stops, ignore_index=True)

    # Apply urban/rural filter
    if 'urban' in filter_mode or 'rural' in filter_mode:
        if 'UrbanRural (code)' in combined.columns:
            if 'urban' in filter_mode:
                combined = combined[combined['UrbanRural (code)'].str.startswith(('A', 'B', 'C'), na=False)]
            else:
                combined = combined[combined['UrbanRural (code)'].str.startswith(('D', 'E', 'F'), na=False)]

    # Aggregate at LSOA level
    lsoa_cols = {
        'stop_id': 'nunique',
        'total_population': 'first',
        'age_0_15': 'first',
        'age_16_64': 'first',
        'age_65_plus': 'first',
        'region_name': 'first'
    }

    if 'lsoa_name' in combined.columns:
        lsoa_cols['lsoa_name'] = 'first'

    # Add all demographic columns (exclude lsoa_code since it's the groupby key)
    for col in required_cols:
        if col not in lsoa_cols and col in combined.columns and col != 'stop_id' and col != 'lsoa_code':
            lsoa_cols[col] = 'first'

    lsoa_agg = combined.groupby('lsoa_code').agg(lsoa_cols).reset_index()

    # Rename for clarity
    rename_dict = {
        'stop_id': 'num_stops',
        'UrbanRural (name)': 'urban_rural',
        'Index of Multiple Deprivation (IMD) Score': 'imd_score',
        'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)': 'imd_decile',
        'Employment Score (rate)': 'employment_score',
        'Income Score (rate)': 'income_score',
        'Income Decile (where 1 is most deprived 10% of LSOAs)': 'income_decile',
        'Health Deprivation and Disability Score': 'health_disability_score',
        'Income Deprivation Affecting Older People (IDAOPI) Score (rate)': 'elderly_income_deprivation'
    }

    for old_name, new_name in rename_dict.items():
        if old_name in lsoa_agg.columns:
            lsoa_agg = lsoa_agg.rename(columns={old_name: new_name})

    # Calculate derived metrics
    lsoa_agg['stops_per_1000'] = (lsoa_agg['num_stops'] / lsoa_agg['total_population']) * 1000
    lsoa_agg['pct_elderly'] = (lsoa_agg['age_65_plus'] / lsoa_agg['total_population']) * 100

    # JOIN gender data from Census 2021
    gender_data = load_gender_data_from_census()

    if not gender_data.empty:
        lsoa_agg = lsoa_agg.merge(gender_data, on='lsoa_code', how='left')

        # Calculate gender percentages
        lsoa_agg['gender_total'] = lsoa_agg['male_population'] + lsoa_agg['female_population']
        lsoa_agg['pct_female'] = (lsoa_agg['female_population'] / lsoa_agg['gender_total']) * 100
        lsoa_agg['pct_male'] = (lsoa_agg['male_population'] / lsoa_agg['gender_total']) * 100
        lsoa_agg['has_gender_data'] = lsoa_agg['male_population'].notna()
    else:
        # Fallback if gender data file not found
        lsoa_agg['male_population'] = np.nan
        lsoa_agg['female_population'] = np.nan
        lsoa_agg['pct_female'] = 51.0
        lsoa_agg['pct_male'] = 49.0
        lsoa_agg['has_gender_data'] = False

    # JOIN ethnicity data from Census 2021
    ethnicity_data = load_ethnicity_data_from_census()

    if not ethnicity_data.empty:
        lsoa_agg = lsoa_agg.merge(ethnicity_data, on='lsoa_code', how='left')
        lsoa_agg['has_ethnicity_data'] = lsoa_agg['pct_bme'].notna()
    else:
        # Fallback if ethnicity data file not found
        for col in ['pct_bme', 'pct_white', 'pct_asian', 'pct_black', 'pct_mixed', 'pct_other']:
            lsoa_agg[col] = np.nan
        lsoa_agg['has_ethnicity_data'] = False

    # Filter out invalid data
    lsoa_agg = lsoa_agg[
        (lsoa_agg['total_population'] > 0) &
        (lsoa_agg['num_stops'] >= 0) &
        (lsoa_agg['stops_per_1000'].notna())
    ]

    return lsoa_agg


# ============================================================================
# PRE-LOAD DATA WITH SPINNER
# ============================================================================

# Pre-load data once with visual feedback to improve perceived performance
# Streamlit caching ensures this only runs once per filter combination
with st.spinner('Loading equity analysis data... (10-15 seconds on first load, instant after)'):
    _ = load_lsoa_data_f(filter_mode, filter_value)
    _ = load_gender_data_from_census()
    _ = load_ethnicity_data_from_census()

# ============================================================================
# SECTION F35: Service Distribution Across Deprivation Deciles
# ============================================================================

st.header("📊 Service Distribution Across Deprivation Deciles")
st.markdown("*How fairly are bus services distributed across areas of different deprivation levels?*")

# Check filter
if filter_mode not in ['all_regions', 'all_urban', 'all_rural']:
    st.info("📊 **Equity analysis requires multi-region data.** Select 'All Regions' to view this analysis.")
else:
    lsoa_data = load_lsoa_data_f(filter_mode, filter_value)

    if lsoa_data.empty or 'imd_decile' not in lsoa_data.columns:
        st.warning("⚠️ IMD (deprivation) data not available for this selection.")
    else:
        lsoa_data_clean = lsoa_data[lsoa_data['imd_decile'].notna()].copy()

        if len(lsoa_data_clean) < 30:
            st.warning(f"⚠️ Insufficient data ({len(lsoa_data_clean)} LSOAs). Need at least 30 for reliable equity analysis.")
        else:
            st.success(f"✅ Analyzing {len(lsoa_data_clean):,} LSOAs with deprivation data")

            # Box plot by IMD Decile
            fig_box = go.Figure()

            for decile in sorted(lsoa_data_clean['imd_decile'].unique()):
                decile_data = lsoa_data_clean[lsoa_data_clean['imd_decile'] == decile]

                fig_box.add_trace(go.Box(
                    y=decile_data['stops_per_1000'],
                    name=f"D{int(decile)}",
                    boxmean='sd',
                    marker_color='#dc2626' if decile <= 3 else '#16a34a' if decile >= 8 else '#3b82f6',
                    hovertemplate='<b>Decile %{fullData.name}</b><br>' +
                                  'Coverage: %{y:.2f} stops/1000<br>' +
                                  '<extra></extra>'
                ))

            national_avg = calculate_weighted_average_f(lsoa_data_clean, 'stops_per_1000')

            fig_box.add_hline(
                y=national_avg,
                line_dash="dash",
                line_color="#6b7280",
                annotation_text=f"National Avg: {national_avg:.2f}",
                annotation_position="right"
            )

            fig_box.update_layout(
                title="Bus Stop Coverage by IMD Decile (1 = Most Deprived, 10 = Least Deprived)",
                xaxis_title="IMD Decile",
                yaxis_title="Bus Stops per 1,000 Population",
                height=500,
                showlegend=False
            )

            st.plotly_chart(fig_box, use_container_width=True)

            # Lorenz Curve
            st.markdown("#### Lorenz Curve: Service Distribution Inequality")

            lorenz_data = generate_lorenz_curve_data(
                lsoa_data_clean['stops_per_1000'].values,
                lsoa_data_clean['total_population'].values
            )

            gini = calculate_gini_coefficient(
                lsoa_data_clean['stops_per_1000'].values,
                lsoa_data_clean['total_population'].values
            )

            fig_lorenz = go.Figure()

            # Perfect equality line
            fig_lorenz.add_trace(go.Scatter(
                x=[0, 100],
                y=[0, 100],
                mode='lines',
                name='Perfect Equality',
                line=dict(color='gray', dash='dash'),
                hovertemplate='<b>Perfect Equality</b><br>' +
                              'If services were perfectly equal<br>' +
                              '<extra></extra>'
            ))

            # Actual Lorenz curve
            fig_lorenz.add_trace(go.Scatter(
                x=lorenz_data['cum_pop_pct'],
                y=lorenz_data['cum_service_pct'],
                mode='lines',
                name='Actual Distribution',
                line=dict(color='indianred', width=3),
                fill='tonexty',
                fillcolor='rgba(255, 0, 0, 0.1)',
                hovertemplate='<b>Actual Distribution</b><br>' +
                              '%{x:.1f}% of population (sorted by coverage)<br>' +
                              'receives %{y:.1f}% of bus stops<br>' +
                              '<extra></extra>'
            ))

            fig_lorenz.update_layout(
                title=f"Lorenz Curve: Service Distribution (Gini Coefficient: {gini:.3f})",
                xaxis_title="Cumulative % of Population (sorted by coverage)",
                yaxis_title="Cumulative % of Bus Stops",
                height=500,
                xaxis=dict(range=[0, 100]),
                yaxis=dict(range=[0, 100])
            )

            st.plotly_chart(fig_lorenz, use_container_width=True)

            # Analysis
            most_deprived = lsoa_data_clean[lsoa_data_clean['imd_decile'] <= 3]
            least_deprived = lsoa_data_clean[lsoa_data_clean['imd_decile'] >= 8]

            coverage_most_deprived = calculate_weighted_average_f(most_deprived, 'stops_per_1000')
            coverage_least_deprived = calculate_weighted_average_f(least_deprived, 'stops_per_1000')

            disparity_pct = ((coverage_least_deprived - coverage_most_deprived) / coverage_most_deprived * 100)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Gini Coefficient", f"{gini:.3f}")

            with col2:
                st.metric("Most Deprived (D1-3)", f"{coverage_most_deprived:.2f}")

            with col3:
                st.metric("Least Deprived (D8-10)", f"{coverage_least_deprived:.2f}")

            with col4:
                st.metric(
                    "Disparity",
                    f"{abs(disparity_pct):.1f}%",
                    delta=f"{'Favors affluent' if disparity_pct > 0 else 'Favors deprived'}",
                    delta_color="inverse" if disparity_pct > 0 else "normal"
                )

            # Interpretation
            if gini < 0.25:
                inequality_level = "low inequality"
            elif gini < 0.35:
                inequality_level = "moderate inequality"
            elif gini < 0.45:
                inequality_level = "significant inequality"
            else:
                inequality_level = "severe inequality"

            st.markdown(f"""
**Gini coefficient of {gini:.3f}** indicates **{inequality_level}** in bus service distribution.

Most deprived areas (IMD Decile 1-3) receive **{coverage_most_deprived:.2f} stops per 1,000** population,
while least deprived areas (Decile 8-10) receive **{coverage_least_deprived:.2f} stops per 1,000** -
a **{abs(disparity_pct):.1f}%** {'advantage for affluent areas' if disparity_pct > 0 else 'disadvantage for deprived areas'}.

The Lorenz curve shows cumulative distribution: closer to the diagonal means more equal service distribution.
            """)

st.markdown("---")

# ============================================================================
# SECTION F36: Accessibility for Elderly and Disabled Populations
# ============================================================================

st.header("♿ Elderly and Disabled Population Accessibility")
st.markdown("*Do areas with high elderly populations (proxy for mobility challenges) have adequate bus service?*")

lsoa_data_f36 = load_lsoa_data_f(filter_mode, filter_value)

if lsoa_data_f36.empty:
    st.warning("⚠️ No data available for this selection.")
else:
    lsoa_data_f36 = lsoa_data_f36[
        (lsoa_data_f36['pct_elderly'].notna()) &
        (lsoa_data_f36['pct_elderly'] > 0) &
        (lsoa_data_f36['stops_per_1000'].notna())
    ].copy()

    if len(lsoa_data_f36) < 10:
        st.warning(f"⚠️ Insufficient data ({len(lsoa_data_f36)} LSOAs).")
    else:
        st.success(f"✅ Analyzing {len(lsoa_data_f36):,} LSOAs")

        # Add health deprivation if available for disability proxy
        if 'health_disability_score' in lsoa_data_f36.columns:
            lsoa_data_f36_clean = lsoa_data_f36[lsoa_data_f36['health_disability_score'].notna()].copy()
        else:
            lsoa_data_f36_clean = lsoa_data_f36.copy()

        # Scatter plot
        fig_elderly = px.scatter(
            lsoa_data_f36_clean,
            x='pct_elderly',
            y='stops_per_1000',
            color='region_name' if filter_mode in ['all_regions', 'all_urban', 'all_rural'] else None,
            size='total_population',
            hover_data={'lsoa_name': True, 'urban_rural': True, 'pct_elderly': ':.1f', 'stops_per_1000': ':.2f'},
            title="Bus Coverage vs Elderly Population %",
            labels={
                'pct_elderly': '% Population Aged 65+',
                'stops_per_1000': 'Bus Stops per 1,000 Population',
                'region_name': 'Region'
            },
            height=600
        )

        # Add trendline
        if len(lsoa_data_f36_clean) >= 30:
            corr, p_value = stats.pearsonr(lsoa_data_f36_clean['pct_elderly'], lsoa_data_f36_clean['stops_per_1000'])

            z = np.polyfit(lsoa_data_f36_clean['pct_elderly'], lsoa_data_f36_clean['stops_per_1000'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(lsoa_data_f36_clean['pct_elderly'].min(), lsoa_data_f36_clean['pct_elderly'].max(), 100)

            fig_elderly.add_trace(go.Scatter(
                x=x_line,
                y=p(x_line),
                mode='lines',
                name=f'Trend (r={corr:.3f}, p={p_value:.3f})',
                line=dict(color='red', dash='dash'),
                hovertemplate='<b>Trend Line</b><br>r=%{fullData.name}<extra></extra>'
            ))

        st.plotly_chart(fig_elderly, use_container_width=True)

        # Correlation analysis
        if len(lsoa_data_f36_clean) >= 30:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Correlation (r)", f"{corr:.3f}")

            with col2:
                # Use scientific notation for very small p-values
                if p_value < 0.0001:
                    st.metric("P-value", f"{p_value:.2e}")
                else:
                    st.metric("P-value", f"{p_value:.4f}")

            if p_value < 0.05:
                if corr < -0.3:
                    interpretation = "Areas with higher elderly populations have **lower** bus coverage - a concerning equity issue for mobility-challenged residents."
                elif corr > 0.3:
                    interpretation = "Areas with higher elderly populations have **higher** bus coverage - positive targeting of vulnerable populations."
                else:
                    interpretation = "Weak correlation - elderly population % has little relationship with coverage."
            else:
                interpretation = "No statistically significant relationship between elderly population % and bus coverage."

            # Format p-value for text display
            p_text = f"{p_value:.2e}" if p_value < 0.0001 else f"{p_value:.4f}"

            st.markdown(f"""
**Correlation: {corr:.3f}** (p={p_text})

{interpretation}

Elderly passengers require: accessibility features (low-floor buses, shelters), shorter walking distances,
more frequent service, and better connectivity to healthcare facilities.
            """)

st.markdown("---")

# ============================================================================
# SECTION F37: Ethnic Minority Access Patterns
# ============================================================================

st.header("🌍 Ethnic Group Analysis: Transit Access Across All Communities")
st.markdown(f"*Analyzing bus coverage for White, Asian, Black, Mixed, and Other ethnic groups | **{filter_display}***")

ethnicity_data_f37 = load_lsoa_data_f(filter_mode, filter_value)

if ethnicity_data_f37.empty:
    st.warning("⚠️ No data available for this selection.")
else:
    # Check if we have actual ethnicity data
    has_ethnicity = ethnicity_data_f37['has_ethnicity_data'].any() if 'has_ethnicity_data' in ethnicity_data_f37.columns else False

    if not has_ethnicity:
        st.warning("⚠️ Ethnicity data from Census 2021 not found in processed files.")
    else:
        # Clean data for analysis
        ethnicity_clean = ethnicity_data_f37[
            (ethnicity_data_f37['pct_bme'].notna()) &
            (ethnicity_data_f37['pct_bme'] >= 0) &
            (ethnicity_data_f37['pct_bme'] <= 100) &
            (ethnicity_data_f37['stops_per_1000'].notna())
        ].copy()

        if len(ethnicity_clean) < 30:
            st.warning(f"⚠️ Insufficient data ({len(ethnicity_clean)} LSOAs). Need at least 30 for statistical analysis.")
        else:
            st.success(f"✅ Analyzing {len(ethnicity_clean):,} LSOAs with Census 2021 ethnicity data")
            st.info(f"""
            **Data Source:** Census 2021 TS021 (Ethnic Group) at LSOA level
            **Coverage for:** White, Asian, Black, Mixed/Multiple, Other ethnic groups
            """)

            # Calculate national/filtered average
            national_avg_ethnicity = (ethnicity_clean['num_stops'].sum() / ethnicity_clean['total_population'].sum()) * 1000

            # ========== Detailed Ethnic Subcategories Analysis ==========
            st.markdown("### Detailed Ethnic Subcategories (19 Groups)")
            st.markdown("*Census 2021 TS021 - Granular breakdown within each main ethnic group*")

            # Load detailed subcategories from original Census file
            try:
                census_detailed = pd.read_csv('data/raw/demographics/census_2021_ethnicity_lsoa.csv')

                # Extract subcategory columns (exact column names from Census)
                subcategory_cols = {
                    'Indian': 'Ethnic group: Asian, Asian British or Asian Welsh: Indian',
                    'Pakistani': 'Ethnic group: Asian, Asian British or Asian Welsh: Pakistani',
                    'Bangladeshi': 'Ethnic group: Asian, Asian British or Asian Welsh: Bangladeshi',
                    'Chinese': 'Ethnic group: Asian, Asian British or Asian Welsh: Chinese',
                    'Other Asian': 'Ethnic group: Asian, Asian British or Asian Welsh: Other Asian',
                    'African': 'Ethnic group: Black, Black British, Black Welsh, Caribbean or African: African',
                    'Caribbean': 'Ethnic group: Black, Black British, Black Welsh, Caribbean or African: Caribbean',
                    'Other Black': 'Ethnic group: Black, Black British, Black Welsh, Caribbean or African: Other Black',
                    'White & Black Caribbean': 'Ethnic group: Mixed or Multiple ethnic groups: White and Black Caribbean',
                    'White & Black African': 'Ethnic group: Mixed or Multiple ethnic groups: White and Black African',
                    'White & Asian': 'Ethnic group: Mixed or Multiple ethnic groups: White and Asian',
                    'Other Mixed': 'Ethnic group: Mixed or Multiple ethnic groups: Other Mixed or Multiple ethnic groups',
                    'English/Welsh/Scottish/NI/British': 'Ethnic group: White: English, Welsh, Scottish, Northern Irish or British',
                    'Irish': 'Ethnic group: White: Irish',
                    'Gypsy or Irish Traveller': 'Ethnic group: White: Gypsy or Irish Traveller',
                    'Roma': 'Ethnic group: White: Roma',
                    'Other White': 'Ethnic group: White: Other White',
                    'Arab': 'Ethnic group: Other ethnic group: Arab',
                    'Any Other': 'Ethnic group: Other ethnic group: Any other ethnic group'
                }

                # Rename columns for easier access
                census_detailed = census_detailed.rename(columns={'geography code': 'lsoa_code'})

                # Merge with ethnicity_clean to get coverage AND car ownership data
                detailed_merged = ethnicity_clean[['lsoa_code', 'num_stops', 'total_population', 'stops_per_1000', 'pct_no_car']].merge(
                    census_detailed[['lsoa_code'] + list(subcategory_cols.values())],
                    on='lsoa_code',
                    how='left'
                )

                # Calculate summary statistics for each subcategory
                subcategory_summary = []
                for display_name, col_name in subcategory_cols.items():
                    if col_name in detailed_merged.columns:
                        total_pop = detailed_merged[col_name].sum()
                        pct_of_total = (total_pop / detailed_merged['total_population'].sum() * 100)

                        # Calculate weighted average coverage for areas with this group
                        areas_with_group = detailed_merged[detailed_merged[col_name] > 0]
                        if len(areas_with_group) > 0:
                            avg_cov = (areas_with_group['num_stops'].sum() / areas_with_group['total_population'].sum()) * 1000
                            avg_no_car = areas_with_group['pct_no_car'].mean() if 'pct_no_car' in areas_with_group.columns else 0
                        else:
                            avg_cov = 0
                            avg_no_car = 0

                        # Determine parent category
                        if display_name in ['Indian', 'Pakistani', 'Bangladeshi', 'Chinese', 'Other Asian']:
                            parent = 'Asian'
                        elif display_name in ['African', 'Caribbean', 'Other Black']:
                            parent = 'Black'
                        elif 'White &' in display_name or display_name == 'Other Mixed':
                            parent = 'Mixed/Multiple'
                        elif display_name in ['Arab', 'Any Other']:
                            parent = 'Other'
                        else:
                            parent = 'White'

                        subcategory_summary.append({
                            'Parent Group': parent,
                            'Subcategory': display_name,
                            'Population': total_pop,
                            '% of Total': pct_of_total,
                            'Avg Coverage': avg_cov,
                            '% No Car': avg_no_car,
                            'LSOAs Present': len(areas_with_group)
                        })

                if subcategory_summary:
                    subcat_df = pd.DataFrame(subcategory_summary)
                    subcat_df = subcat_df.sort_values(['Parent Group', 'Population'], ascending=[True, False])

                    # VIZ 0: Treemap - perfect for hierarchical data with different sizes
                    st.markdown("#### Population Distribution by Ethnic Subcategory")

                    # Prepare data for treemap
                    fig_treemap = px.treemap(
                        subcat_df,
                        path=['Parent Group', 'Subcategory'],
                        values='Population',
                        color='Parent Group',
                        color_discrete_map={
                            'Asian': '#3b82f6',
                            'Black': '#10b981',
                            'White': '#8b5cf6',
                            'Mixed/Multiple': '#f59e0b',
                            'Other': '#ef4444'
                        },
                        title=f"Ethnic Subcategory Distribution - Treemap ({filter_display})",
                        height=600
                    )

                    fig_treemap.update_traces(
                        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>(%{percentParent})',
                        textposition='middle center',
                        textfont_size=11,
                        marker=dict(line=dict(width=2, color='white'))
                    )

                    fig_treemap.update_layout(
                        margin=dict(t=50, b=20, l=10, r=10)
                    )

                    st.plotly_chart(fig_treemap, use_container_width=True)

                    st.info("💡 **Reading this treemap:** Each rectangle represents an ethnic subcategory. Size = population. Grouped by color into 5 main ethnic groups. Click on a main group to zoom in.")

                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Population", f"{subcat_df['Population'].sum():,.0f}")
                    with col2:
                        largest = subcat_df.loc[subcat_df['Population'].idxmax()]
                        st.metric("Largest Subcategory", f"{largest['Subcategory']}", f"{(largest['Population']/subcat_df['Population'].sum()*100):.1f}%")
                    with col3:
                        st.metric("Total Subcategories", "19")

                    st.markdown("---")

                    # VIZ 1: Coverage comparison
                    st.markdown("##### Bus Coverage by Detailed Subcategory")
                    fig_cov_subcat = px.bar(
                        subcat_df,
                        x='Subcategory',
                        y='Avg Coverage',
                        color='Parent Group',
                        title="Average Bus Coverage by Detailed Ethnic Subcategory",
                        labels={'Avg Coverage': 'Bus Stops per 1,000 Population'},
                        height=500,
                        text='Avg Coverage'
                    )
                    fig_cov_subcat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    fig_cov_subcat.update_xaxes(tickangle=-45)
                    fig_cov_subcat.add_hline(
                        y=national_avg_ethnicity,
                        line_dash="dash",
                        line_color="gray",
                        annotation_text=f"Overall Avg: {national_avg_ethnicity:.2f}"
                    )
                    st.plotly_chart(fig_cov_subcat, use_container_width=True)

                    st.markdown("---")

                    # VIZ 2: Transit dependency (car ownership)
                    st.markdown("##### Transit Dependency by Detailed Subcategory")
                    fig_car_subcat = px.bar(
                        subcat_df,
                        x='Subcategory',
                        y='% No Car',
                        color='Parent Group',
                        title="Transit Dependency (% Households Without Car) by Ethnic Subcategory",
                        labels={'% No Car': '% Households Without Car'},
                        height=500,
                        text='% No Car'
                    )
                    fig_car_subcat.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_car_subcat.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig_car_subcat, use_container_width=True)

                    st.markdown("**Equity Principle:** Communities with higher transit dependency (higher % no car) should receive higher bus coverage.")

                    st.markdown("---")

                    # Detailed table
                    st.markdown("##### Comprehensive Statistics Table")
                    display_table = subcat_df.copy()
                    display_table['Population'] = display_table['Population'].apply(lambda x: f"{x:,.0f}")
                    display_table['% of Total'] = display_table['% of Total'].round(2)
                    display_table['Avg Coverage'] = display_table['Avg Coverage'].round(2)
                    display_table['% No Car'] = display_table['% No Car'].round(1)

                    st.dataframe(display_table, use_container_width=True, hide_index=True)

                    st.markdown("""
**Reading this analysis:**
- **19 detailed subcategories** from Census 2021 TS021
- **Asian subcategories:** Indian, Pakistani, Bangladeshi, Chinese, Other Asian
- **Black subcategories:** African, Caribbean, Other Black
- **White subcategories:** English/Welsh/Scottish/NI/British, Irish, Gypsy/Irish Traveller, Roma, Other White
- **Mixed subcategories:** White & Black Caribbean, White & Black African, White & Asian, Other Mixed
- **Other subcategories:** Arab, Any Other
- **Avg Coverage**: Bus stops per 1,000 in areas where subcategory is present
- **% No Car**: Transit dependency indicator (higher = more transit-dependent)
                    """)
                else:
                    st.warning("⚠️ Unable to calculate subcategory statistics.")

            except Exception as e:
                st.warning(f"⚠️ Detailed subcategory data not available. Using aggregated ethnic groups only.")


            # Policy context - condensed with key statistics
            st.markdown("""
---
### Policy Context: Transit Equity for All Ethnic Communities

**Census 2021 England & Wales Population:**
- White: 81.0% | Asian: 9.3% | Black: 4.2% | Mixed: 3.0% | Other: 2.1%

**Key Equity Findings:**
- Minority ethnic households: 15-30% lower car ownership than White households
- 86% of minority ethnic population lives in urban areas (vs 73% White)
- Income disparities: Median income 10-20% lower for many groups

**Service Design Priorities:**
- Routes to employment centers, healthcare, places of worship, cultural facilities
- Multilingual information and staff training
- Evening/weekend frequency for shift workers and community activities
- Affordability schemes and consultation with ethnic community organizations

**Limitations:** Census categories don't capture within-group diversity. Qualitative research needed for journey purposes, barriers (safety, discrimination), and community-specific mobility needs.
            """)

st.markdown("---")

# ============================================================================
# SECTION F38: Low-Income Household Coverage
# ============================================================================

st.header("💷 Income Deprivation and Service Access")
st.markdown("*Do low-income areas receive adequate bus service provision?*")

income_data = load_lsoa_data_f(filter_mode, filter_value)

if income_data.empty or 'income_decile' not in income_data.columns:
    st.warning("⚠️ Income deprivation data not available.")
else:
    income_data_clean = income_data[income_data['income_decile'].notna()].copy()

    if len(income_data_clean) < 30:
        st.warning(f"⚠️ Insufficient data ({len(income_data_clean)} LSOAs).")
    else:
        st.success(f"✅ Analyzing {len(income_data_clean):,} LSOAs")

        # Box plot
        fig_income = go.Figure()

        for decile in sorted(income_data_clean['income_decile'].unique()):
            decile_data = income_data_clean[income_data_clean['income_decile'] == decile]

            fig_income.add_trace(go.Box(
                y=decile_data['stops_per_1000'],
                name=f"D{int(decile)}",
                boxmean='sd',
                marker_color='#dc2626' if decile <= 3 else '#16a34a' if decile >= 8 else '#3b82f6',
                hovertemplate='<b>Decile %{fullData.name}</b><br>Coverage: %{y:.2f}<extra></extra>'
            ))

        national_avg_income = (income_data_clean['num_stops'].sum() / income_data_clean['total_population'].sum()) * 1000

        fig_income.add_hline(
            y=national_avg_income,
            line_dash="dash",
            line_color="#6b7280",
            annotation_text=f"National Avg: {national_avg_income:.2f}"
        )

        fig_income.update_layout(
            title="Bus Coverage by Income Deprivation Decile (1 = Highest Deprivation, 10 = Lowest)",
            xaxis_title="Income Decile",
            yaxis_title="Bus Stops per 1,000 Population",
            height=500,
            showlegend=False
        )

        st.plotly_chart(fig_income, use_container_width=True)

        # Disparity calculation
        low_income = income_data_clean[income_data_clean['income_decile'] <= 3]
        high_income = income_data_clean[income_data_clean['income_decile'] >= 8]

        coverage_low = (low_income['num_stops'].sum() / low_income['total_population'].sum()) * 1000
        coverage_high = (high_income['num_stops'].sum() / high_income['total_population'].sum()) * 1000

        disparity = ((coverage_high - coverage_low) / coverage_low * 100)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Low Income (D1-3)", f"{coverage_low:.2f}")

        with col2:
            st.metric("High Income (D8-10)", f"{coverage_high:.2f}")

        with col3:
            st.metric(
                "Income Disparity",
                f"{abs(disparity):.1f}%",
                delta=f"{'Favors high income' if disparity > 0 else 'Favors low income'}",
                delta_color="inverse" if disparity > 0 else "normal"
            )

        st.markdown(f"""
{'High-income areas receive **more** service' if disparity > 0 else 'Low-income areas receive **more** service'} -
a **{abs(disparity):.1f}%** difference.

Lowest income deciles (D1-3): **{coverage_low:.2f}** stops/1000 |
Highest income deciles (D8-10): **{coverage_high:.2f}** stops/1000

{"Low-income households are more dependent on public transport due to lower car ownership rates." if disparity > 0 else "Positive finding - services targeting areas of greatest income deprivation."}
        """)

st.markdown("---")

# ============================================================================
# SECTION F39: Social Exclusion Risk Zones (Triple Burden)
# ============================================================================

st.header("🚨 Social Exclusion Risk Zones")
st.markdown("*Which areas face the 'triple burden' of high deprivation, poor employment, and inadequate transport?*")

triple_data = load_lsoa_data_f(filter_mode, filter_value)

if triple_data.empty:
    st.warning("⚠️ Data not available.")
else:
    triple_data_clean = triple_data[
        (triple_data['imd_decile'].notna()) &
        (triple_data['employment_score'].notna()) &
        (triple_data['stops_per_1000'].notna())
    ].copy()

    if len(triple_data_clean) < 30:
        st.warning(f"⚠️ Insufficient data ({len(triple_data_clean)} LSOAs).")
    else:
        st.success(f"✅ Analyzing {len(triple_data_clean):,} LSOAs")

        # Define triple burden thresholds
        national_avg_triple = (triple_data_clean['num_stops'].sum() / triple_data_clean['total_population'].sum()) * 1000
        median_employment = triple_data_clean['employment_score'].median()

        triple_data_clean['high_deprivation'] = triple_data_clean['imd_decile'] <= 3
        triple_data_clean['high_unemployment'] = triple_data_clean['employment_score'] > median_employment
        triple_data_clean['low_coverage'] = triple_data_clean['stops_per_1000'] < national_avg_triple

        triple_data_clean['burden_count'] = (
            triple_data_clean['high_deprivation'].astype(int) +
            triple_data_clean['high_unemployment'].astype(int) +
            triple_data_clean['low_coverage'].astype(int)
        )

        triple_data_clean['risk_category'] = triple_data_clean['burden_count'].map({
            0: 'No Risk',
            1: 'Low Risk',
            2: 'Moderate Risk',
            3: 'High Risk (Triple Burden)'
        })

        triple_burden_lsoas = triple_data_clean[triple_data_clean['burden_count'] == 3]

        # Visualization: Regional breakdown of triple burden
        if filter_mode in ['all_regions', 'all_urban', 'all_rural'] and 'region_name' in triple_data_clean.columns:
            # Show regional breakdown
            regional_summary = triple_data_clean.groupby(['region_name', 'risk_category']).size().reset_index(name='count')

            fig_risk = px.bar(
                regional_summary,
                x='region_name',
                y='count',
                color='risk_category',
                title=f"Social Exclusion Risk Distribution by Region ({filter_display})",
                category_orders={'risk_category': ['No Risk', 'Low Risk', 'Moderate Risk', 'High Risk (Triple Burden)']},
                color_discrete_map={
                    'No Risk': '#16a34a',
                    'Low Risk': '#eab308',
                    'Moderate Risk': '#f97316',
                    'High Risk (Triple Burden)': '#dc2626'
                },
                labels={'region_name': 'Region', 'count': 'Number of LSOAs', 'risk_category': 'Risk Level'},
                height=500,
                barmode='stack'
            )

            fig_risk.update_xaxes(tickangle=-45)
        else:
            # Single region or subset - show simple histogram
            fig_risk = px.histogram(
                triple_data_clean,
                x='risk_category',
                color='risk_category',
                title=f"Social Exclusion Risk Distribution ({filter_display})",
                category_orders={'risk_category': ['No Risk', 'Low Risk', 'Moderate Risk', 'High Risk (Triple Burden)']},
                color_discrete_map={
                    'No Risk': '#16a34a',
                    'Low Risk': '#eab308',
                    'Moderate Risk': '#f97316',
                    'High Risk (Triple Burden)': '#dc2626'
                },
                height=400
            )

        st.plotly_chart(fig_risk, use_container_width=True)

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Triple Burden LSOAs", f"{len(triple_burden_lsoas):,}")

        with col2:
            pct_triple = (len(triple_burden_lsoas) / len(triple_data_clean)) * 100
            st.metric("% of Total", f"{pct_triple:.1f}%")

        with col3:
            pop_affected = triple_burden_lsoas['total_population'].sum()
            st.metric("Population Affected", f"{pop_affected:,}")

        with col4:
            avg_coverage_triple = (triple_burden_lsoas['num_stops'].sum() / triple_burden_lsoas['total_population'].sum() * 1000) if pop_affected > 0 else 0
            st.metric(
                "Avg Coverage",
                f"{avg_coverage_triple:.2f}",
                delta=f"{avg_coverage_triple - national_avg_triple:.2f} vs national",
                delta_color="inverse"
            )

        # Top 10 worst
        if len(triple_burden_lsoas) > 0:
            st.markdown("#### Top 10 Most Affected Areas")

            worst = triple_burden_lsoas.nsmallest(10, 'stops_per_1000')[
                ['lsoa_name', 'region_name', 'imd_decile', 'employment_score', 'stops_per_1000', 'total_population']
            ].copy()

            worst.columns = ['LSOA', 'Region', 'IMD', 'Employment', 'Stops/1000', 'Population']
            worst['IMD'] = worst['IMD'].astype(int)
            worst['Employment'] = worst['Employment'].round(3)
            worst['Stops/1000'] = worst['Stops/1000'].round(2)

            st.dataframe(worst, use_container_width=True, hide_index=True)

        st.markdown(f"""
**{len(triple_burden_lsoas):,} LSOAs** ({pct_triple:.1f}%) face the **triple burden**:
high deprivation + high unemployment + low coverage, affecting **{pop_affected:,} residents**.

These areas require priority intervention due to compounded mobility and economic challenges.
        """)

st.markdown("---")

# ============================================================================
# SECTION F40: Gender-Disaggregated Accessibility
# ============================================================================

st.header("👥 Gender, Identity, and Service Access")
st.markdown(f"*How does bus service provision relate to gender demographics and identity? (Analyzing: {filter_display})*")

gender_data = load_lsoa_data_f(filter_mode, filter_value)

if gender_data.empty:
    st.warning("⚠️ No data available for this selection.")
else:
    # Check if we have actual gender data
    has_gender = gender_data['has_gender_data'].any() if 'has_gender_data' in gender_data.columns else False

    if not has_gender:
        st.warning("⚠️ Gender-disaggregated Census 2021 data not found in processed files.")
    else:
        st.error("""
        🚨 **CRITICAL DATA LIMITATION - LGBTQ+ Communities NOT Represented**

        **What This Analysis CAN Show:**
        - Male vs Female coverage patterns (Census 2021 binary sex data at LSOA level)

        **What This Analysis CANNOT Show:**
        - Trans, non-binary, gender diverse people's access patterns
        - LGBTQ+ community-specific coverage needs
        - Sexual orientation demographics at small area level

        **Why This Data Is Missing:**
        Census 2021 was the first UK census to ask about gender identity and sexual orientation, but due to **statistical disclosure controls** (protecting identifiable individuals in small areas), this data is **NOT published at LSOA level**.

        **For LGBTQ+ transit equity analysis:**
        - National/regional Census data available from ONS (England & Wales level)
        - Qualitative research with LGBTQ+ communities required
        - Safety audits and co-design needed to understand unmet mobility needs

        **This section shows Male/Female patterns ONLY - NOT a complete gender equity analysis.**
        """)

        st.info("""
        **Census 2021 National Stats (England & Wales):**
        - 262,000 people (0.5%) have gender identity different from sex assigned at birth
        - 3.2% identify as LGB+ (1.5M people)
        - Higher concentrations in urban areas: London, Brighton, Manchester, Bristol
        - Estimated 15-20% higher reliance on public transport (Stonewall research)
        """)
        # Clean data for analysis
        gender_clean = gender_data[
            (gender_data['pct_female'].notna()) &
            (gender_data['pct_female'] > 0) &
            (gender_data['pct_female'] < 100) &
            (gender_data['stops_per_1000'].notna())
        ].copy()

        if len(gender_clean) < 30:
            st.warning(f"⚠️ Insufficient data ({len(gender_clean)} LSOAs). Need at least 30 for statistical analysis.")
        else:
            st.success(f"✅ Analyzing {len(gender_clean):,} LSOAs with gender-disaggregated Census 2021 data")

            # Gender distribution summary
            total_male_pop = gender_clean['male_population'].sum()
            total_female_pop = gender_clean['female_population'].sum()
            total_gender_pop = total_male_pop + total_female_pop

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Male Population", f"{total_male_pop:,}", f"{(total_male_pop/total_gender_pop*100):.1f}%")
            with col2:
                st.metric("Female Population", f"{total_female_pop:,}", f"{(total_female_pop/total_gender_pop*100):.1f}%")
            with col3:
                st.metric("Total Population", f"{total_gender_pop:,}")

            # Calculate national/filtered average
            national_avg_gender = (gender_clean['num_stops'].sum() / gender_clean['total_population'].sum()) * 1000

            # VISUALIZATION 1: Side-by-side comparison of Male vs Female areas
            st.markdown("#### Average Bus Coverage: Male-Majority vs Female-Majority Areas")
            st.markdown("*Comparing areas with above-average male % vs above-average female %*")

            avg_male_pct = gender_clean['pct_male'].mean()
            avg_female_pct = gender_clean['pct_female'].mean()

            male_majority = gender_clean[gender_clean['pct_male'] > avg_male_pct]
            female_majority = gender_clean[gender_clean['pct_female'] > avg_female_pct]

            coverage_male = (male_majority['num_stops'].sum() / male_majority['total_population'].sum()) * 1000
            coverage_female = (female_majority['num_stops'].sum() / female_majority['total_population'].sum()) * 1000

            gender_comparison_df = pd.DataFrame({
                'Gender Majority': ['Male-Majority Areas', 'Female-Majority Areas'],
                'Avg Coverage': [coverage_male, coverage_female],
                'LSOAs': [len(male_majority), len(female_majority)],
                'Avg %': [male_majority['pct_male'].mean(), female_majority['pct_female'].mean()]
            })

            fig_gender_compare = px.bar(
                gender_comparison_df,
                x='Gender Majority',
                y='Avg Coverage',
                text='Avg Coverage',
                title="Bus Coverage Comparison: Male-Majority vs Female-Majority Areas",
                labels={'Avg Coverage': 'Bus Stops per 1,000 Population'},
                color='Avg Coverage',
                color_continuous_scale='RdYlGn',
                height=400
            )

            fig_gender_compare.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_gender_compare.add_hline(
                y=national_avg_gender,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Overall Average: {national_avg_gender:.2f}"
            )

            st.plotly_chart(fig_gender_compare, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Male-Majority Areas", f"{coverage_male:.2f} stops/1000",
                         f"{((coverage_male - national_avg_gender) / national_avg_gender * 100):+.1f}% vs avg")
            with col2:
                st.metric("Female-Majority Areas", f"{coverage_female:.2f} stops/1000",
                         f"{((coverage_female - national_avg_gender) / national_avg_gender * 100):+.1f}% vs avg")

            st.markdown("**Note:** Data shows binary Male/Female categories only (Census 2021 limitation). Trans, non-binary, and gender diverse people are not represented in this geographic breakdown.")

            st.markdown("---")

            # VISUALIZATION 2: Scatter plot for correlation analysis
            st.markdown("#### Gender Demographics Correlation Analysis")
            corr_female, p_value_female = stats.pearsonr(gender_clean['pct_female'], gender_clean['stops_per_1000'])

            # Scatter plot: Female % vs Coverage (keeping original for statistical analysis)
            fig_gender = px.scatter(
                gender_clean,
                x='pct_female',
                y='stops_per_1000',
                color='region_name' if filter_mode in ['all_regions', 'all_urban', 'all_rural'] else None,
                size='total_population',
                hover_data={
                    'lsoa_name': True,
                    'pct_female': ':.2f',
                    'pct_male': ':.2f',
                    'stops_per_1000': ':.2f',
                    'female_population': ':,',
                    'male_population': ':,'
                },
                title="Bus Coverage vs Female Population %",
                labels={
                    'pct_female': '% Female Population',
                    'stops_per_1000': 'Bus Stops per 1,000 Population',
                    'region_name': 'Region'
                },
                height=600
            )

            # Add trendline
            z = np.polyfit(gender_clean['pct_female'], gender_clean['stops_per_1000'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(gender_clean['pct_female'].min(), gender_clean['pct_female'].max(), 100)

            fig_gender.add_trace(go.Scatter(
                x=x_line,
                y=p(x_line),
                mode='lines',
                name=f'Trend (r={corr_female:.3f})',
                line=dict(color='red', dash='dash', width=2),
                hovertemplate='<b>Trend Line</b><br>r=%{fullData.name}<extra></extra>'
            ))

            # Add national average line
            fig_gender.add_hline(
                y=national_avg_gender,
                line_dash="dot",
                line_color="gray",
                annotation_text=f"Average: {national_avg_gender:.2f}",
                annotation_position="right"
            )

            st.plotly_chart(fig_gender, use_container_width=True)

            # Statistical Summary
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Correlation (r)", f"{corr_female:.3f}")

            with col2:
                # Use scientific notation for very small p-values
                if p_value_female < 0.0001:
                    st.metric("P-value", f"{p_value_female:.2e}")
                else:
                    st.metric("P-value", f"{p_value_female:.4f}")

            with col3:
                sig_status = "Significant" if p_value_female < 0.05 else "Not Significant"
                st.metric("Statistical Significance", sig_status)

            # Quartile analysis: Compare LSOAs with high female % vs low female %
            gender_clean['female_quartile'] = pd.qcut(gender_clean['pct_female'], q=4, labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'])

            quartile_summary = gender_clean.groupby('female_quartile').apply(
                lambda x: pd.Series({
                    'avg_coverage': (x['num_stops'].sum() / x['total_population'].sum()) * 1000,
                    'avg_female_pct': x['pct_female'].mean(),
                    'num_lsoas': len(x),
                    'population': x['total_population'].sum()
                })
            ).reset_index()

            st.markdown("#### Coverage by Female Population Quartile")

            fig_quartile = px.bar(
                quartile_summary,
                x='female_quartile',
                y='avg_coverage',
                text='avg_coverage',
                title="Average Bus Coverage by Female Population Quartile",
                labels={
                    'female_quartile': 'Female Population Quartile',
                    'avg_coverage': 'Bus Stops per 1,000 Population'
                },
                color='avg_coverage',
                color_continuous_scale='RdYlGn',
                height=400
            )

            fig_quartile.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_quartile.update_layout(showlegend=False)

            st.plotly_chart(fig_quartile, use_container_width=True)

            # Display quartile table
            quartile_display = quartile_summary.copy()
            quartile_display['avg_coverage'] = quartile_display['avg_coverage'].round(2)
            quartile_display['avg_female_pct'] = quartile_display['avg_female_pct'].round(2)
            quartile_display.columns = ['Quartile', 'Avg Coverage', 'Avg Female %', 'LSOAs', 'Population']

            st.dataframe(quartile_display, use_container_width=True, hide_index=True)

            # Interpretation
            st.markdown("#### Analysis")

            if p_value_female < 0.05:
                if abs(corr_female) > 0.3:
                    strength = "strong" if abs(corr_female) > 0.5 else "moderate"
                    direction = "positive" if corr_female > 0 else "negative"

                    # Format p-value
                    p_text_f = f"{p_value_female:.2e}" if p_value_female < 0.0001 else f"{p_value_female:.4f}"

                    st.markdown(f"""
**Statistically significant {strength} {direction} correlation** (r={corr_female:.3f}, p={p_text_f})
between female population % and bus coverage.

{'Areas with higher female populations have **better** bus coverage.' if corr_female > 0 else 'Areas with higher female populations have **lower** bus coverage.'}

**Quartile Analysis:**
- Q1 (Lowest female %): {quartile_summary.iloc[0]['avg_coverage']:.2f} stops/1000 ({quartile_summary.iloc[0]['avg_female_pct']:.1f}% female)
- Q4 (Highest female %): {quartile_summary.iloc[3]['avg_coverage']:.2f} stops/1000 ({quartile_summary.iloc[3]['avg_female_pct']:.1f}% female)
- **Disparity: {abs(quartile_summary.iloc[3]['avg_coverage'] - quartile_summary.iloc[0]['avg_coverage']):.2f} stops/1000** difference

{"This is a **positive equity finding** - areas with higher female populations (who are more transit-dependent) receive better service." if corr_female > 0 else "This is an **equity concern** - areas with higher female populations (who are more transit-dependent) receive lower service."}
                    """)
                else:
                    p_text_f = f"{p_value_female:.2e}" if p_value_female < 0.0001 else f"{p_value_female:.4f}"
                    st.markdown(f"""
**Weak correlation** (r={corr_female:.3f}, p={p_text_f}) - gender demographics show little
relationship with bus coverage patterns.

Coverage appears to be driven by other factors (urban density, deprivation, regional policy) rather than
gender composition of the population.
                    """)
            else:
                p_text_f = f"{p_value_female:.2e}" if p_value_female < 0.0001 else f"{p_value_female:.4f}"
                st.markdown(f"""
**No statistically significant relationship** (r={corr_female:.3f}, p={p_text_f}) between
female population % and bus coverage.

This suggests bus network planning does not systematically account for (or discriminate based on)
gender demographics at the LSOA level.
                """)

            st.markdown("---")

            # Policy context - condensed
            st.markdown("""
### Policy Context: Gender-Inclusive Transit (Male, Female, Trans, Non-Binary, LGBTQ+)

**Key Findings from Research (NTS 2021, Stonewall, Transport Focus):**
- **Women**: 75% of unpaid care work, 20% less likely to hold driving license
- **Men**: Higher work-trip focus, early morning/late evening industrial routes needed
- **Trans/Non-Binary**: 95% report safety concerns, gender-neutral facilities critical
- **LGBTQ+**: 15-20% higher transit reliance, late-night service to LGBTQ+ districts essential

**Service Design Priorities for ALL Genders:**
- **Men**: Early morning/late evening service, direct commuter routes, affordable fares
- **Women**: Trip-chaining connectivity, school hours frequency, safety lighting/CCTV
- **Trans/Non-Binary**: Gender-neutral facilities, staff training, flexible ID policies
- **LGBTQ+**: Late-night service, safety audits, anti-discrimination enforcement
- **All**: Accessible infrastructure, real-time info, harassment reporting, community consultation

**Data Gaps:** LSOA-level trans, non-binary, LGBTQ+ geographic data not available. Qualitative research, safety audits, and co-design with diverse gender communities required for true equity analysis.
            """)

st.markdown("---")

# End of Equity & Social Inclusion page
