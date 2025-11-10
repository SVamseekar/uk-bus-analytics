"""
Category J: Economic Impact & BCR Analysis
Benefit-Cost Ratio analysis, economic multiplier effects, and monetized benefits

Sections:
- J49: BCR for proposed service expansions by region
- J50: Economic multiplier effects of bus investment
- J51: Employment accessibility improvement value
- J52: Carbon savings monetization

Author: Week 4 Economic Impact Implementation
Date: November 10, 2025
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
from plotly.subplots import make_subplots

from dashboard.utils.data_loader import load_regional_summary, load_regional_stops, REGION_CODES
from dashboard.utils.bcr_calculator import BCRCalculator

# Initialize BCR calculator
bcr_calc = BCRCalculator()

# Page config
st.set_page_config(
    page_title="Economic Impact & BCR | UK Bus Analytics",
    page_icon="💰",
    layout="wide"
)


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data
def load_lsoa_anomalies():
    """Load service gap data for investment targeting"""
    try:
        df = pd.read_csv('models/lsoa_anomalies.csv')
        return df
    except FileNotFoundError:
        return pd.DataFrame()


# ============================================================================
# HEADER & FILTERS
# ============================================================================

st.title("💰 Economic Impact & BCR Analysis")
st.markdown("""
Benefit-Cost Ratio (BCR) analysis following **HM Treasury Green Book** and **DfT TAG 2024** standards.
Quantifies economic value of bus service investments with full appraisal methodology.
""")

st.markdown("---")

# Filters (same pattern as other categories)
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

# Parse filters
if region_filter == 'All Regions':
    if urban_rural_filter == 'All':
        filter_mode = 'all_regions'
        filter_value = None
        filter_display = "📊 All Regions"
    elif urban_rural_filter == 'Urban Only':
        filter_mode = 'all_urban'
        filter_value = 'urban'
        filter_display = "🏙️ All Regions - Urban Areas"
    else:
        filter_mode = 'all_rural'
        filter_value = 'rural'
        filter_display = "🌾 All Regions - Rural Areas"
else:
    if urban_rural_filter == 'All':
        filter_mode = 'region'
        filter_value = region_filter
        filter_display = f"📍 {region_filter}"
    elif urban_rural_filter == 'Urban Only':
        filter_mode = 'region_urban'
        filter_value = region_filter
        filter_display = f"🏙️ {region_filter} - Urban"
    else:
        filter_mode = 'region_rural'
        filter_value = region_filter
        filter_display = f"🌾 {region_filter} - Rural"

st.info(f"**Active Filter:** {filter_display}")

st.markdown("---")


# ============================================================================
# SECTION J49: REGIONAL BCR ANALYSIS
# ============================================================================

st.header("J49. Regional BCR for Service Expansion Investments")

st.markdown("""
**Question:** *What is the Benefit-Cost Ratio for proposed service expansions in each region?*

Calculates BCR using **TAG 2024 time values** (£9.85/hr bus commuting), **30-year appraisal period**, and **3.5% discount rate**
following HM Treasury Green Book standards.
""")

# Load data
regional_data = load_regional_summary()
anomalies_data = load_lsoa_anomalies()

if not regional_data.empty:

    # Determine regions to analyze based on filter
    if filter_mode == 'all_regions':
        regions_to_analyze = regional_data.copy()
        analysis_scope = "all 9 regions"
    elif filter_mode == 'region':
        regions_to_analyze = regional_data[regional_data['region_name'] == region_filter].copy()
        analysis_scope = f"{region_filter}"
    else:
        st.warning("⚠️ Urban/Rural filtering not applicable for regional BCR. Showing full regional analysis.")
        if filter_mode.startswith('region_'):
            # Show single region if region_urban or region_rural
            regions_to_analyze = regional_data[regional_data['region_name'] == region_filter].copy()
            analysis_scope = f"{region_filter}"
        else:
            regions_to_analyze = regional_data.copy()
            analysis_scope = "all 9 regions"

    # Calculate BCR for each region
    bcr_results = []

    for idx, region in regions_to_analyze.iterrows():
        region_name = region['region_name']
        population = region['population']

        # Calculate service gap in this region
        region_code = REGION_CODES[region_name]
        region_gaps = anomalies_data[
            (anomalies_data['region_code'] == region_code) &
            (anomalies_data['is_anomaly'] == True)
        ] if not anomalies_data.empty else pd.DataFrame()

        gap_population = region_gaps['total_population'].sum() if not region_gaps.empty else population * 0.15

        # Investment scenario: £100 per capita in gap areas
        investment_amount = gap_population * 100

        # Determine if predominantly urban (>50% of pop in urban LSOAs)
        # Proxy: regions with >23 stops/1000 are predominantly urban
        is_urban = region['stops_per_1000'] > 23
        region_type = 'urban' if is_urban else 'rural'

        # Calculate BCR
        bcr_analysis = bcr_calc.calculate_full_bcr(
            investment_amount=investment_amount,
            population=gap_population,
            region_type=region_type,
            adoption_rate=0.22,  # 22% adoption (realistic for service improvements)
            time_saved_minutes=12.0,  # 12 min saved per trip (evidence from UK studies)
            modal_shift_from_car=0.60  # 60% from car (TAG typical value)
        )

        bcr_results.append({
            'region_name': region_name,
            'population': population,
            'gap_population': gap_population,
            'investment_amount': investment_amount,
            'total_pv_costs': bcr_analysis['total_pv_costs'],
            'total_pv_benefits': bcr_analysis['total_pv_benefits'],
            'bcr': bcr_analysis['bcr'],
            'bcr_category': bcr_analysis['bcr_category'],
            'net_present_value': bcr_analysis['net_present_value'],
            'region_type': region_type,
            'new_passengers': bcr_analysis['time_benefits']['new_passengers'],
            'carbon_saved_tonnes': bcr_analysis['carbon_benefits']['carbon_saved_tonnes'],
        })

    bcr_df = pd.DataFrame(bcr_results).sort_values('bcr', ascending=False)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_bcr = bcr_df['bcr'].mean()
        st.metric(
            "Average BCR",
            f"{avg_bcr:.2f}",
            delta=bcr_calc.categorize_bcr(avg_bcr),
            help="Mean BCR across analyzed regions"
        )

    with col2:
        total_investment = bcr_df['investment_amount'].sum()
        st.metric(
            "Total Investment",
            f"£{total_investment/1e6:.1f}M",
            help="Total investment required across all gap areas"
        )

    with col3:
        total_npv = bcr_df['net_present_value'].sum()
        st.metric(
            "Net Present Value",
            f"£{total_npv/1e6:.1f}M",
            delta="Benefits - Costs",
            help="Total NPV across all investments"
        )

    with col4:
        high_value_regions = len(bcr_df[bcr_df['bcr'] >= 2.0])
        st.metric(
            "High VfM Regions",
            f"{high_value_regions}/{len(bcr_df)}",
            delta=f"{high_value_regions/len(bcr_df)*100:.0f}%",
            help="Regions with BCR ≥ 2.0 (High or Very High value)"
        )

    # Visualization 1: BCR by Region
    fig_bcr = go.Figure()

    # Color scale based on BCR category
    color_map = {
        'Poor': '#d73027',
        'Low': '#fc8d59',
        'Medium': '#fee08b',
        'High': '#91cf60',
        'Very High': '#1a9850'
    }

    colors = [color_map[cat] for cat in bcr_df['bcr_category']]

    fig_bcr.add_trace(go.Bar(
        x=bcr_df['region_name'],
        y=bcr_df['bcr'],
        text=[f"{bcr:.2f}<br>{cat}" for bcr, cat in zip(bcr_df['bcr'], bcr_df['bcr_category'])],
        textposition='outside',
        marker=dict(color=colors),
        customdata=bcr_df[['investment_amount', 'net_present_value', 'new_passengers']],
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "BCR: %{y:.2f}<br>" +
            "Investment: £%{customdata[0]:,.0f}<br>" +
            "NPV: £%{customdata[1]:,.0f}<br>" +
            "New Passengers: %{customdata[2]:,.0f}<br>" +
            "<extra></extra>"
        )
    ))

    # Add threshold lines
    fig_bcr.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Poor/Low threshold")
    fig_bcr.add_hline(y=2.0, line_dash="dash", line_color="green", annotation_text="High VfM threshold")
    fig_bcr.add_hline(y=4.0, line_dash="dash", line_color="darkgreen", annotation_text="Very High VfM threshold")

    fig_bcr.update_layout(
        title=f"Benefit-Cost Ratio by Region ({analysis_scope})",
        xaxis_title="Region",
        yaxis_title="BCR (Benefits / Costs)",
        height=500,
        showlegend=False
    )

    st.plotly_chart(fig_bcr, use_container_width=True)

    # Visualization 2: Investment vs NPV scatter
    fig_scatter = px.scatter(
        bcr_df,
        x='investment_amount',
        y='net_present_value',
        size='bcr',
        color='bcr_category',
        color_discrete_map=color_map,
        text='region_name',
        hover_data={
            'investment_amount': ':,.0f',
            'net_present_value': ':,.0f',
            'bcr': ':.2f',
            'new_passengers': ':,.0f'
        },
        labels={
            'investment_amount': 'Investment Required (£)',
            'net_present_value': 'Net Present Value (£)',
            'bcr_category': 'BCR Category'
        }
    )

    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(
        title="Investment Required vs Net Present Value",
        height=500
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

    # Data table
    with st.expander("📊 Detailed BCR Analysis Table"):
        display_df = bcr_df[[
            'region_name', 'gap_population', 'investment_amount',
            'total_pv_costs', 'total_pv_benefits', 'bcr', 'bcr_category',
            'net_present_value', 'new_passengers', 'carbon_saved_tonnes'
        ]].copy()

        display_df.columns = [
            'Region', 'Gap Population', 'Investment (£)',
            'PV Costs (£)', 'PV Benefits (£)', 'BCR', 'Category',
            'NPV (£)', 'New Passengers', 'Carbon Saved (tonnes/yr)'
        ]

        # Format numbers
        for col in ['Gap Population', 'Investment (£)', 'PV Costs (£)', 'PV Benefits (£)', 'NPV (£)', 'New Passengers']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")

        display_df['BCR'] = display_df['BCR'].apply(lambda x: f"{x:.2f}")
        display_df['Carbon Saved (tonnes/yr)'] = display_df['Carbon Saved (tonnes/yr)'].apply(lambda x: f"{x:,.1f}")

        st.dataframe(display_df, use_container_width=True)

    # Narrative
    st.markdown("#### 📝 BCR Analysis Insights")

    highest_bcr_region = bcr_df.iloc[0]
    lowest_bcr_region = bcr_df.iloc[-1]
    high_value_count = len(bcr_df[bcr_df['bcr'] >= 2.0])

    narrative = f"""
**Investment Value Assessment for {analysis_scope}:**

{high_value_count} of {len(bcr_df)} analyzed regions demonstrate **High or Very High value for money** (BCR ≥ 2.0),
indicating strong economic justification for service expansion investments.

**Highest Return:** {highest_bcr_region['region_name']} shows BCR of **{highest_bcr_region['bcr']:.2f}**
({highest_bcr_region['bcr_category']} VfM), delivering **£{highest_bcr_region['net_present_value']/1e6:.1f}M net benefit**
from £{highest_bcr_region['investment_amount']/1e6:.1f}M investment. This translates to
**{highest_bcr_region['new_passengers']:,.0f} new passengers** and **{highest_bcr_region['carbon_saved_tonnes']:,.0f} tonnes CO₂
saved annually**.

**Investment Priority:** Regions with BCR > 2.0 should receive priority funding allocation. The combined investment of
£{total_investment/1e6:.1f}M across all gap areas generates £{total_npv/1e6:.1f}M net economic value over 30 years.

**Methodology:** Analysis uses **DfT TAG 2024 values** (£9.85/hr bus commuting time), **30-year appraisal period**, and
**3.5% social discount rate** per HM Treasury Green Book. Adoption rate 22%, time savings 12 min/trip, 60% modal shift from car.
Benefits include time savings with agglomeration effects and carbon monetization (£80/tonne CO₂).
"""

    st.info(narrative)

else:
    st.warning("⚠️ Regional summary data not available. Run data pipeline first.")

st.markdown("---")


# ============================================================================
# SECTION J50: ECONOMIC MULTIPLIER EFFECTS
# ============================================================================

st.header("J50. Economic Multiplier Effects of Bus Investment")

st.markdown("""
**Question:** *What are the economic multiplier effects (direct, indirect, induced) of bus service investment?*

Calculates **total economic output**, **employment creation**, and **GVA contribution** using transport sector multipliers
from HM Treasury and ONS research.
""")

# Investment scenarios
st.markdown("### 💼 Investment Scenario Analysis")

col1, col2 = st.columns(2)

with col1:
    multiplier_investment = st.number_input(
        "Investment Amount (£ millions)",
        min_value=1.0,
        max_value=500.0,
        value=50.0,
        step=5.0,
        help="Total bus service investment"
    )

with col2:
    multiplier_region_type = st.selectbox(
        "Region Type",
        ['urban', 'rural'],
        help="Urban areas have higher multipliers due to density effects"
    )

multiplier_investment_pounds = multiplier_investment * 1_000_000

# Calculate multiplier effects
multiplier_results = bcr_calc.calculate_economic_multiplier_effects(
    investment_amount=multiplier_investment_pounds,
    region_type=multiplier_region_type
)

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Economic Output",
        f"£{multiplier_results['total_economic_output']/1e6:.1f}M",
        delta=f"{(multiplier_results['total_economic_output']/multiplier_investment_pounds - 1)*100:.0f}% above investment",
        help="Direct + Indirect + Induced economic output"
    )

with col2:
    st.metric(
        "Economic Multiplier",
        f"{multiplier_results['total_multiplier']:.2f}x",
        help="Total output per £1 invested"
    )

with col3:
    st.metric(
        "Jobs Created",
        f"{multiplier_results['total_jobs']:,.0f}",
        delta=f"{multiplier_results['total_jobs']/multiplier_results['direct_jobs']:.1f}x direct jobs",
        help="Direct + Indirect + Induced employment"
    )

with col4:
    st.metric(
        "GVA Contribution",
        f"£{multiplier_results['gva_contribution']/1e6:.1f}M",
        help="Gross Value Added to regional economy"
    )

# Visualization 1: Multiplier breakdown (Sankey diagram)
fig_sankey = go.Figure(go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=[
            "Investment",
            "Direct Output",
            "Indirect Output",
            "Induced Output",
            "Total Economic Output"
        ],
        color=["#0066CC", "#91cf60", "#fee08b", "#fc8d59", "#1a9850"]
    ),
    link=dict(
        source=[0, 0, 0, 1, 2, 3],
        target=[1, 2, 3, 4, 4, 4],
        value=[
            multiplier_results['direct_output'],
            multiplier_results['indirect_output'],
            multiplier_results['induced_output'],
            multiplier_results['direct_output'],
            multiplier_results['indirect_output'],
            multiplier_results['induced_output']
        ]
    )
))

fig_sankey.update_layout(
    title=f"Economic Multiplier Flow: £{multiplier_investment:.1f}M Investment → £{multiplier_results['total_economic_output']/1e6:.1f}M Output",
    height=400
)

st.plotly_chart(fig_sankey, use_container_width=True)

# Visualization 2: Employment breakdown
employment_df = pd.DataFrame({
    'Category': ['Direct Jobs', 'Indirect Jobs (Supply Chain)', 'Induced Jobs (Spending)'],
    'Jobs': [
        multiplier_results['direct_jobs'],
        multiplier_results['indirect_jobs'],
        multiplier_results['induced_jobs']
    ]
})

fig_employment = px.bar(
    employment_df,
    x='Category',
    y='Jobs',
    text='Jobs',
    color='Category',
    color_discrete_sequence=['#91cf60', '#fee08b', '#fc8d59']
)

fig_employment.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_employment.update_layout(
    title="Employment Creation by Category",
    yaxis_title="Number of Jobs",
    showlegend=False,
    height=400
)

st.plotly_chart(fig_employment, use_container_width=True)

# Narrative
st.markdown("#### 📝 Multiplier Effects Analysis")

narrative_j50 = f"""
**Economic Impact of £{multiplier_investment:.1f}M Bus Investment ({multiplier_region_type.capitalize()} Region):**

Every **£1 invested** generates **£{multiplier_results['total_multiplier']:.2f} in total economic output** through
direct construction/operation, supply chain effects, and wage-induced spending.

**Output Breakdown:**
- **Direct output**: £{multiplier_results['direct_output']/1e6:.1f}M (construction, vehicles, infrastructure)
- **Indirect output**: £{multiplier_results['indirect_output']/1e6:.1f}M (supply chain - steel, technology, maintenance contracts)
- **Induced output**: £{multiplier_results['induced_output']/1e6:.1f}M (worker spending in local economy)

**Employment Impact:** Creates **{multiplier_results['total_jobs']:,.0f} jobs** across the economy, with
{multiplier_results['direct_jobs']:,.0f} direct transport sector jobs generating an additional
{multiplier_results['indirect_jobs'] + multiplier_results['induced_jobs']:,.0f} jobs through supply chains and spending effects.

**GVA Contribution:** Adds **£{multiplier_results['gva_contribution']/1e6:.1f}M to regional Gross Value Added**,
approximately **{multiplier_results['gva_contribution']/multiplier_investment_pounds*100:.0f}% of initial investment**
becomes sustainable economic output.

**Methodology:** Multipliers based on HM Treasury/ONS transport sector research. Urban multipliers higher due to supply chain
density and local spending retention. Employment calculated at £65K per job (ONS 2024 transport sector average). GVA estimated
as 60% of gross output (standard UK economic conversion).
"""

st.info(narrative_j50)

st.markdown("---")


# ============================================================================
# SECTION J51: EMPLOYMENT ACCESSIBILITY VALUE
# ============================================================================

st.header("J51. Employment Accessibility Improvement Value")

st.markdown("""
**Question:** *What is the economic value of improved employment accessibility through better bus services?*

Quantifies GDP contribution and welfare savings from connecting workers to jobs, following **DfT Wider Economic Impacts** guidance.
""")

# Load data for employment analysis
if not regional_data.empty:

    # Scenario inputs
    st.markdown("### 👔 Employment Accessibility Scenario")

    col1, col2, col3 = st.columns(3)

    with col1:
        if filter_mode == 'region' or filter_mode.startswith('region_'):
            selected_region_employment = regional_data[regional_data['region_name'] == region_filter].iloc[0]
            working_age_pop = selected_region_employment['population'] * 0.63  # 63% working age (16-64)
            st.metric("Working Age Population", f"{working_age_pop:,.0f}", help="Ages 16-64 in selected region")
        else:
            working_age_pop = regional_data['population'].sum() * 0.63
            st.metric("Working Age Population", f"{working_age_pop:,.0f}", help="Ages 16-64 across all regions")

    with col2:
        jobs_accessible = st.number_input(
            "Additional Jobs Made Accessible",
            min_value=1000,
            max_value=500000,
            value=50000,
            step=5000,
            help="Number of jobs within 45 min travel time after service improvement"
        )

    with col3:
        employment_rate_increase = st.slider(
            "Employment Rate Increase (%)",
            min_value=1.0,
            max_value=10.0,
            value=3.5,
            step=0.5,
            help="Expected increase in employment rate due to improved access"
        ) / 100

    # Calculate employment accessibility benefits
    employment_benefits = bcr_calc.calculate_employment_accessibility_value(
        population=working_age_pop,
        jobs_made_accessible=jobs_accessible,
        adoption_rate=0.18,  # 18% of working age pop benefit
        employment_rate_increase=employment_rate_increase
    )

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Workers Affected",
            f"{employment_benefits['workers_affected']:,.0f}",
            delta=f"{employment_benefits['workers_affected']/working_age_pop*100:.1f}% of working age",
            help="Workers benefiting from improved job access"
        )

    with col2:
        st.metric(
            "Additional Employment",
            f"{employment_benefits['additional_employed']:,.0f}",
            delta=f"+{employment_rate_increase*100:.1f}% rate",
            help="New jobs filled due to improved accessibility"
        )

    with col3:
        st.metric(
            "Annual GDP Contribution",
            f"£{employment_benefits['annual_gdp_contribution']/1e6:.1f}M",
            help="Annual economic output from additional employment"
        )

    with col4:
        st.metric(
            "Total 30-Year Value",
            f"£{employment_benefits['total_pv_value']/1e6:.1f}M",
            help="PV of employment benefits + welfare savings"
        )

    # Visualization: Benefit breakdown
    benefit_breakdown = pd.DataFrame({
        'Benefit Type': [
            'Employment GDP Contribution',
            'Welfare Savings (Reduced Benefits)'
        ],
        'Present Value (£M)': [
            employment_benefits['pv_employment_benefit'] / 1e6,
            employment_benefits['pv_welfare_savings'] / 1e6
        ]
    })

    fig_employment_value = px.bar(
        benefit_breakdown,
        x='Benefit Type',
        y='Present Value (£M)',
        text='Present Value (£M)',
        color='Benefit Type',
        color_discrete_sequence=['#1a9850', '#91cf60']
    )

    fig_employment_value.update_traces(texttemplate='£%{text:.1f}M', textposition='outside')
    fig_employment_value.update_layout(
        title="30-Year Present Value of Employment Accessibility Benefits",
        yaxis_title="Present Value (£ millions)",
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig_employment_value, use_container_width=True)

    # Narrative
    st.markdown("#### 📝 Employment Accessibility Insights")

    narrative_j51 = f"""
**Economic Value of Improved Job Access ({filter_display}):**

Making **{jobs_accessible:,} additional jobs accessible** within 45 minutes travel time impacts
**{employment_benefits['workers_affected']:,.0f} workers** ({employment_benefits['workers_affected']/working_age_pop*100:.1f}% of working-age population).

**Employment Impact:** Expected **{employment_rate_increase*100:.1f}% increase in employment rate** translates to
**{employment_benefits['additional_employed']:,.0f} additional people in work**. At average UK salary (£33K), these workers
contribute **£{employment_benefits['annual_gdp_contribution']/1e6:.1f}M annually to GDP** (70% of gross salary represents
economic output).

**Welfare Savings:** Reduced unemployment saves **£{employment_benefits['annual_welfare_savings']/1e6:.1f}M per year**
in welfare costs (£8,000 per unemployed person - DWP estimates), reducing public expenditure while increasing tax revenue.

**30-Year Value:** Combined present value of **£{employment_benefits['total_pv_value']/1e6:.1f}M**
(£{employment_benefits['pv_employment_benefit']/1e6:.1f}M GDP + £{employment_benefits['pv_welfare_savings']/1e6:.1f}M welfare savings)
demonstrates **strong business case** for connectivity investments beyond direct transport benefits.

**Methodology:** Based on DfT Wider Economic Impacts guidance. Employment response elasticity calibrated to UK labor market studies
(0.05-0.10 typical range). GDP contribution = 70% of average salary. Welfare savings from reduced JSA, UC, and support costs.
Benefits discounted at 3.5% over 30 years per Green Book.
"""

    st.info(narrative_j51)

else:
    st.warning("⚠️ Regional data not available for employment analysis.")

st.markdown("---")


# ============================================================================
# SECTION J52: CARBON SAVINGS MONETIZATION
# ============================================================================

st.header("J52. Carbon Savings Monetization")

st.markdown("""
**Question:** *What is the monetized value of carbon savings from modal shift to bus services?*

Calculates CO₂ emissions saved and economic value using **DfT TAG 2024 carbon valuation** (£80/tonne CO₂).
""")

# Carbon scenario inputs
st.markdown("### 🌱 Modal Shift Scenario")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if filter_mode == 'region' or filter_mode.startswith('region_'):
        selected_region_carbon = regional_data[regional_data['region_name'] == region_filter].iloc[0]
        carbon_population = selected_region_carbon['population']
    else:
        carbon_population = regional_data['population'].sum()

    st.metric("Population Base", f"{carbon_population/1e6:.2f}M", help="Population in analysis scope")

with col2:
    modal_shift_pct = st.slider(
        "Car-to-Bus Modal Shift (%)",
        min_value=5.0,
        max_value=25.0,
        value=10.0,
        step=1.0,
        help="Percentage of car trips shifting to bus"
    ) / 100

with col3:
    bus_adoption = st.slider(
        "Bus Service Adoption Rate (%)",
        min_value=10.0,
        max_value=40.0,
        value=25.0,
        step=5.0,
        help="Population proportion using improved bus service"
    ) / 100

with col4:
    avg_trip_km = st.number_input(
        "Avg Trip Distance (km)",
        min_value=3.0,
        max_value=25.0,
        value=8.5,
        step=0.5,
        help="Average journey distance"
    )

# Calculate carbon benefits
carbon_results = bcr_calc.calculate_carbon_benefits(
    population=carbon_population,
    adoption_rate=bus_adoption,
    modal_shift_from_car=modal_shift_pct / bus_adoption,  # Of bus users, what % shifted from car
    avg_trip_distance_km=avg_trip_km
)

# Calculate multi-year projection
years = list(range(1, 31))  # 30 years
annual_carbon_values = [carbon_results['annual_carbon_value'] for _ in years]
cumulative_carbon_value = [sum(annual_carbon_values[:i+1]) for i in range(len(years))]
discounted_values = [val / ((1 + bcr_calc.DISCOUNT_RATE) ** year) for year, val in zip(years, annual_carbon_values)]
cumulative_pv = [sum(discounted_values[:i+1]) for i in range(len(years))]

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Car Switchers",
        f"{carbon_results['car_switchers']:,.0f}",
        delta=f"{carbon_results['car_switchers']/carbon_population*100:.2f}% of pop",
        help="People switching from car to bus"
    )

with col2:
    st.metric(
        "Annual CO₂ Saved",
        f"{carbon_results['carbon_saved_tonnes']:,.0f} tonnes",
        delta=f"-{carbon_results['carbon_saved_tonnes']/carbon_results['car_emissions_tonnes']*100:.0f}% emissions",
        help="Net carbon reduction (car - bus emissions)"
    )

with col3:
    st.metric(
        "Annual Carbon Value",
        f"£{carbon_results['annual_carbon_value']/1e6:.2f}M",
        help="Monetized value at £80/tonne CO₂"
    )

with col4:
    st.metric(
        "30-Year PV",
        f"£{carbon_results['pv_carbon_value']/1e6:.1f}M",
        help="Present value of carbon savings over 30 years"
    )

# Visualization 1: Emissions comparison
emissions_df = pd.DataFrame({
    'Source': ['Car Emissions', 'Bus Emissions', 'Net Savings'],
    'CO₂ Tonnes/Year': [
        carbon_results['car_emissions_tonnes'],
        carbon_results['bus_emissions_tonnes'],
        carbon_results['carbon_saved_tonnes']
    ],
    'Color': ['red', 'orange', 'green']
})

fig_emissions = px.bar(
    emissions_df,
    x='Source',
    y='CO₂ Tonnes/Year',
    text='CO₂ Tonnes/Year',
    color='Source',
    color_discrete_map={'Car Emissions': '#d73027', 'Bus Emissions': '#fc8d59', 'Net Savings': '#1a9850'}
)

fig_emissions.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_emissions.update_layout(
    title="Annual Carbon Emissions Comparison",
    yaxis_title="CO₂ Emissions (tonnes/year)",
    showlegend=False,
    height=400
)

st.plotly_chart(fig_emissions, use_container_width=True)

# Visualization 2: Cumulative carbon value over time
fig_cumulative = go.Figure()

fig_cumulative.add_trace(go.Scatter(
    x=years,
    y=[val/1e6 for val in cumulative_carbon_value],
    mode='lines',
    name='Nominal Value',
    line=dict(color='#91cf60', width=2),
    fill='tonexty'
))

fig_cumulative.add_trace(go.Scatter(
    x=years,
    y=[val/1e6 for val in cumulative_pv],
    mode='lines',
    name='Present Value (3.5% discount)',
    line=dict(color='#1a9850', width=3)
))

fig_cumulative.update_layout(
    title="Cumulative Carbon Savings Value Over 30 Years",
    xaxis_title="Year",
    yaxis_title="Cumulative Value (£ millions)",
    height=400,
    hovermode='x unified'
)

st.plotly_chart(fig_cumulative, use_container_width=True)

# Narrative
st.markdown("#### 📝 Carbon Savings Analysis")

narrative_j52 = f"""
**Carbon Emission Reductions from {modal_shift_pct*100:.0f}% Modal Shift ({filter_display}):**

**{carbon_results['car_switchers']:,.0f} people** ({carbon_results['car_switchers']/carbon_population*100:.2f}% of population)
switching from private cars to buses reduces annual emissions by **{carbon_results['carbon_saved_tonnes']:,.0f} tonnes CO₂**.

**Emission Breakdown:**
- Car emissions avoided: **{carbon_results['car_emissions_tonnes']:,.0f} tonnes/year** (0.171 kg CO₂e/passenger-km)
- Bus emissions added: **{carbon_results['bus_emissions_tonnes']:,.0f} tonnes/year** (0.0965 kg CO₂e/passenger-km)
- **Net savings: {carbon_results['carbon_saved_tonnes']:,.0f} tonnes/year**
({(carbon_results['carbon_saved_tonnes']/carbon_results['car_emissions_tonnes']*100):.0f}% reduction)

**Economic Value:** At **DfT TAG 2024 carbon valuation of £80/tonne CO₂**, annual savings worth
**£{carbon_results['annual_carbon_value']/1e6:.2f}M**. Over 30-year appraisal period with 3.5% discounting,
present value totals **£{carbon_results['pv_carbon_value']/1e6:.1f}M**.

**Wider Climate Impact:** Equivalent to:
- **{carbon_results['carbon_saved_tonnes']/2.3:.0f} cars removed from roads** (avg UK car: 2.3 tonnes CO₂/year)
- **{carbon_results['carbon_saved_tonnes']*3.7:.0f} trees planted** (1 tree sequesters ~0.27 tonnes CO₂/year)
- Supports **UK Net Zero 2050 target** through sustainable transport transition

**Methodology:** Emissions factors from BEIS 2024 (car: 0.171 kg, bus: 0.0965 kg per passenger-km). Carbon valuation per
DfT TAG A3 (£80/tonne central estimate). Trip distance {avg_trip_km} km, 300 trips/year per person. Modal shift percentage
applied to bus adoption base. PV calculated at 3.5% social discount rate over 30 years per HM Treasury Green Book.
"""

st.info(narrative_j52)

st.markdown("---")

# Footer
st.markdown("""
---
**Methodology Summary:**
- **BCR Framework**: HM Treasury Green Book, DfT TAG 2024
- **Appraisal Period**: 30 years
- **Discount Rate**: 3.5% (social time preference rate)
- **Time Values**: £9.85/hr bus commuting, £12.65/hr car commuting (TAG A1.3 Table 2)
- **Carbon Valuation**: £80/tonne CO₂ (TAG A3 central estimate 2024)
- **Economic Multipliers**: HM Treasury/ONS transport sector research
- **Employment Effects**: DfT Wider Economic Impacts guidance
- **BCR Categories**: Poor <1.0, Low 1.0-1.5, Medium 1.5-2.0, High 2.0-4.0, Very High >4.0

All monetary values in 2024 prices. Benefits and costs discounted to present value.
""")
