"""
UK Bus Analytics Platform - Homepage
Professional consulting intelligence platform for UK bus transport analysis
Features: Interactive night-satellite map with bus infrastructure and demographic overlays
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from dashboard.utils.data_loader import load_regional_summary, get_national_stats

# Page configuration
st.set_page_config(
    page_title="UK Bus Analytics Platform",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_region_boundaries(version=2):  # Cache buster - increment when GeoJSON changes
    """Load England region GeoJSON boundaries"""
    geojson_path = Path(__file__).parent.parent / 'data' / 'raw' / 'boundaries' / 'regions_2021_england.geojson'
    with open(geojson_path, 'r') as f:
        return json.load(f)

def prepare_map_data():
    """Prepare regional data with validated ONS codes for GeoJSON joining"""
    regional_summary = load_regional_summary()

    # Validate that all regions have ONS codes
    if 'ons_code' not in regional_summary.columns:
        st.error("Regional summary missing 'ons_code' column. Please regenerate regional_summary.csv")
        return pd.DataFrame()

    missing_codes = regional_summary['ons_code'].isna().sum()
    if missing_codes > 0:
        st.warning(f"{missing_codes} regions missing ONS codes")

    return regional_summary

# Load data
national_stats = get_national_stats()
regional_data = prepare_map_data()
region_boundaries = load_region_boundaries()

# Header
st.title("🚌 UK Bus Analytics Platform")
st.markdown("**Professional intelligence for bus transport decision-makers**")
st.markdown("*Understanding service patterns through demographic lens*")
st.markdown("---")

# Map configuration section
st.markdown("## 🗺️ Interactive UK Map")

col_left, col_right = st.columns([3, 1])

with col_right:
    st.markdown("### Map Controls")

    # Basemap selector (free options only)
    basemap_style = st.selectbox(
        "**Basemap Style:**",
        options=["carto-darkmatter", "carto-positron", "open-street-map"],
        index=0,
        help="All options free, no API key required"
    )

    # Data domain selector
    data_domain = st.radio(
        "**Select Data Type:**",
        options=["Bus Infrastructure", "Demographics"],
        index=0
    )

    # Metric selector with explicit colorscales (arrays work better with Choroplethmapbox)
    if data_domain == "Bus Infrastructure":
        metric_options = {
            "Total Bus Stops": ("total_stops", [[0, "#f7fbff"], [0.2, "#deebf7"], [0.5, "#9ecae1"], [0.8, "#4292c6"], [1, "#08519c"]], "Absolute count of bus stops"),
            "Stops per 1,000 Population": ("stops_per_1000", [[0, "#f7fcf5"], [0.2, "#e5f5e0"], [0.5, "#a1d99b"], [0.8, "#41ab5d"], [1, "#006d2c"]], "Per-capita stop density"),
            "Total Routes": ("routes_count", [[0, "#fcfbfd"], [0.2, "#efedf5"], [0.5, "#bcbddc"], [0.8, "#807dba"], [1, "#54278f"]], "Absolute count of routes"),
            "Routes per 100k Population": ("routes_per_100k", [[0, "#ffffcc"], [0.2, "#d9f0a3"], [0.5, "#78c679"], [0.8, "#31a354"], [1, "#006837"]], "Per-capita route density"),
            "Coverage Rank": ("coverage_rank", [[0, "#d73027"], [0.5, "#ffffbf"], [1, "#1a9850"]], "Regional ranking (1=best)")
        }
    else:  # Demographics
        metric_options = {
            "Total Population": ("population", [[0, "#ffffcc"], [0.2, "#ffeda0"], [0.5, "#feb24c"], [0.8, "#f03b20"], [1, "#bd0026"]], "Total population served"),
            "IMD Deprivation Score": ("avg_imd_score", [[0, "#1a9850"], [0.5, "#ffffbf"], [1, "#d73027"]], "Higher = more deprived"),
            "Unemployment Rate (%)": ("avg_unemployment_rate", [[0, "#fff5f0"], [0.2, "#fee0d2"], [0.5, "#fc9272"], [0.8, "#de2d26"], [1, "#a50f15"]], "% unemployed"),
            "No Car Households (%)": ("pct_no_car", [[0, "#ffffe5"], [0.2, "#fff7bc"], [0.5, "#fec44f"], [0.8, "#d95f0e"], [1, "#993404"]], "% without car access")
        }

    selected_metric_label = st.selectbox(
        "**Select Metric:**",
        options=list(metric_options.keys()),
        index=0
    )

    metric_col, colorscale, metric_desc = metric_options[selected_metric_label]

    st.caption(f"*{metric_desc}*")

    # Display key stats for selected metric
    st.markdown("---")
    st.markdown("### Quick Stats")

    if metric_col in regional_data.columns:
        metric_values = regional_data[metric_col].dropna()

        if len(metric_values) > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Max", f"{metric_values.max():.1f}")
                st.metric("Min", f"{metric_values.min():.1f}")
            with col2:
                st.metric("Mean", f"{metric_values.mean():.1f}")
                st.metric("Median", f"{metric_values.median():.1f}")

with col_left:
    # Prepare choropleth data using ONS codes for robust joining
    if metric_col in regional_data.columns:
        # --- A) Auto-detect the correct code field from GeoJSON ---
        props0 = region_boundaries["features"][0]["properties"]

        # Find keys that end with 'CD' (ONS code fields)
        code_keys = [k for k in props0.keys() if k.upper().endswith("CD")]

        # Collect candidate values for each candidate key
        candidates = {}
        for k in code_keys:
            vals = [str(f["properties"][k]).strip() for f in region_boundaries["features"]]
            candidates[k] = vals

        # Pick the key whose values look like region codes (E12000001-E12000009)
        import re
        def looks_like_region_codes(vals):
            return len(vals) == 9 and all(re.fullmatch(r"E120000[0-9]{2}", v) for v in vals)

        FEATURE_CODE = None
        for k, vals in candidates.items():
            if looks_like_region_codes(vals):
                FEATURE_CODE = k
                break

        # Fallback: if nothing matched, keep the original but warn user
        if FEATURE_CODE is None:
            st.error(f"❌ Could not auto-detect ONS code field. Available keys: {list(props0.keys())}")
            FEATURE_CODE = "RGN21CD"  # Assume standard

        # Also auto-detect name field
        FEATURE_NAME = "RGN21NM"  # Standard name field

        featureidkey = f"properties.{FEATURE_CODE}"

        # Show what we're using (helpful for debugging)
        st.write("### 🔧 AUTO-DETECTION DEBUG")
        st.write(f"**Code keys found ending with CD:** {code_keys}")
        st.write(f"**Candidates dict:** {candidates}")
        st.write(f"**Selected FEATURE_CODE:** `{FEATURE_CODE}`")
        st.write(f"**FEATURE_NAME:** `{FEATURE_NAME}`")
        st.write(f"**featureidkey:** `{featureidkey}`")

        # --- B) Build the truth list of codes from the GeoJSON (always 9) ---
        all_codes = [str(f["properties"][FEATURE_CODE]).strip() for f in region_boundaries["features"]]
        code2name = {
            str(f["properties"][FEATURE_CODE]).strip():
            (str(f["properties"][FEATURE_NAME]).strip() if FEATURE_NAME else str(f["properties"][FEATURE_CODE]).strip())
            for f in region_boundaries["features"]
        }

        # CRITICAL: Verify we have exactly 9 region codes
        if len(all_codes) != 9:
            st.error(f"❌ FATAL: GeoJSON has {len(all_codes)} features, expected 9!")
            st.write(f"Codes found: {all_codes}")

        # --- C) Build an explicit mapping from DF (code -> value), with strict numeric coercion ---
        # Ensure ons_code column exists and is clean
        if "ons_code" not in regional_data.columns:
            # Map region names to codes
            name2code_map = {
                'North East England': 'E12000001',
                'North West England': 'E12000002',
                'Yorkshire and Humber': 'E12000003',
                'East Midlands': 'E12000004',
                'West Midlands': 'E12000005',
                'East of England': 'E12000006',
                'Greater London': 'E12000007',
                'South East England': 'E12000008',
                'South West England': 'E12000009'
            }
            regional_data["ons_code"] = regional_data["region_name"].map(name2code_map)

        regional_data["ons_code"] = regional_data["ons_code"].astype(str).str.strip()

        # Make a dict of values by code (only rows that are truly numeric get into the dict)
        vals = pd.to_numeric(regional_data[metric_col], errors="coerce")
        value_by_code = {}
        for code, val in zip(regional_data["ons_code"], vals):
            if pd.notna(val):
                value_by_code[str(code).strip()] = float(val)

        # DEBUG: Show what's in the value dict
        st.write("### 📊 VALUE MAPPING DEBUG")
        st.write(f"**Metric column:** `{metric_col}`")
        st.write(f"**Values in value_by_code:** {list(value_by_code.keys())}")
        st.write(f"**Sample values:** {dict(list(value_by_code.items())[:3])}")

        # --- D) Create z_values exactly in GeoJSON order (9 elements), None where missing ---
        locations = all_codes
        z_values = [value_by_code.get(code, None) for code in all_codes]

        # --- E) Defensive z-range (from finite values only) ---
        import numpy as np
        finite_vals = [v for v in z_values if v is not None and np.isfinite(v)]
        if finite_vals:
            z_min, z_max = float(min(finite_vals)), float(max(finite_vals))
            if z_min == z_max:
                z_min -= 0.5
                z_max += 0.5
        else:
            z_min, z_max = 0, 1

        # --- F) Debug output ---
        missing_from_df = [c for c in all_codes if c not in value_by_code]
        nan_codes = [c for c, v in zip(all_codes, z_values) if v is None]

        st.write("🔍 **DEBUG — Before plotting:**")
        st.write(f"- Locations (should be 9): {len(locations)}")
        st.write(f"- Missing from DF (should be []): {missing_from_df if missing_from_df else '✅ None'}")
        st.write(f"- NaN/None codes (should be []): {nan_codes if nan_codes else '✅ None'}")
        st.dataframe(pd.DataFrame({
            "code": locations,
            "name": [code2name.get(c, c) for c in locations],
            metric_col: z_values
        }))

        # --- G) Build modern choropleth_map with MapLibre ---

        # FINAL DEBUG: Print exactly what we're passing to Plotly
        st.write("### 🎯 FINAL CHECK - DATA BEING PASSED TO PLOTLY")
        st.write(f"**locations length:** {len(locations)}")
        st.write(f"**z_values length:** {len(z_values)}")
        st.write(f"**locations:** {locations}")
        st.write(f"**z_values:** {z_values}")
        st.write(f"**featureidkey:** {featureidkey}")
        st.write(f"**colorscale:** {colorscale}")

        # Prepare DataFrame for px.choropleth_mapbox (requires DataFrame input)
        plot_df = pd.DataFrame({
            'ons_code': locations,
            'region_name': [code2name.get(c, c) for c in locations],
            'value': z_values
        })

        # Use px.choropleth_mapbox with manual zoom (most reliable)
        fig = px.choropleth_mapbox(
            plot_df,
            geojson=region_boundaries,
            locations='ons_code',
            color='value',
            featureidkey=featureidkey,
            color_continuous_scale=colorscale,
            range_color=[z_min, z_max],
            hover_name='region_name',
            hover_data={'ons_code': False, 'value': ':.1f'},
            labels={'value': selected_metric_label},
            mapbox_style=basemap_style,  # carto-darkmatter, carto-positron, or open-street-map
            center={"lat": 52.5, "lon": -1.5},  # Center of England
            zoom=4.7  # Manually tested zoom that shows all 9 regions
        )

        # Update layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=600,
            paper_bgcolor='#0e1117',
            font=dict(color="white")
        )

        # Update colorbar styling
        fig.update_layout(
            coloraxis_colorbar=dict(
                title=dict(
                    text=selected_metric_label,
                    font=dict(size=12, color="white")
                ),
                len=0.6,
                thickness=18,
                x=1.01,
                tickfont=dict(size=10, color="white"),
                bgcolor="rgba(20,20,25,0.8)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1
            )
        )

        # Update trace styling for borders
        fig.update_traces(
            marker_line_width=2,
            marker_line_color="rgba(200,220,240,0.5)",
            marker_opacity=0.8
        )

        # Attribution (all free data sources)
        attribution_text = "Map: © CARTO, © OpenStreetMap contributors | Boundaries: ONS (OGL v3.0)"
        fig.add_annotation(
            text=attribution_text,
            showarrow=False,
            x=0.5, y=0.01,
            xref="paper", yref="paper",
            font=dict(size=8, color="rgba(255,255,255,0.5)"),
            align="center",
            xanchor="center", yanchor="bottom",
            bgcolor="rgba(0,0,0,0.5)",
            borderpad=4
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Metric '{metric_col}' not found in regional data")

st.markdown("---")

# National overview metrics
if national_stats:
    st.markdown("## 📊 National Overview")

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

# Auto-generated insights
st.markdown("## 🔍 Key Insights")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    # Insight 1: Coverage gap
    if 'stops_per_1000' in regional_data.columns:
        worst_coverage = regional_data.nsmallest(1, 'stops_per_1000').iloc[0]
        national_avg = regional_data['stops_per_1000'].mean()
        gap_pct = ((national_avg - worst_coverage['stops_per_1000']) / national_avg) * 100

        st.markdown(f"""
        **⚠️ Coverage Gap**
        {worst_coverage['region_name']} has the lowest coverage at {worst_coverage['stops_per_1000']:.1f} stops per 1,000 population,
        {gap_pct:.0f}% below the national average of {national_avg:.1f}.
        """)

    # Insight 2: Best performer
    if 'stops_per_1000' in regional_data.columns:
        best_coverage = regional_data.nlargest(1, 'stops_per_1000').iloc[0]

        st.markdown(f"""
        **✅ Coverage Leader**
        {best_coverage['region_name']} leads with {best_coverage['stops_per_1000']:.1f} stops per 1,000 population,
        serving {best_coverage['population']/1e6:.1f}M people with {best_coverage['total_stops']:,} stops.
        """)

with insights_col2:
    # Insight 3: Deprivation context
    if 'avg_imd_score' in regional_data.columns and 'stops_per_1000' in regional_data.columns:
        high_imd = regional_data.nlargest(1, 'avg_imd_score').iloc[0]

        st.markdown(f"""
        **📊 Equity Context**
        {high_imd['region_name']} has the highest deprivation (IMD: {high_imd['avg_imd_score']:.1f})
        with {high_imd['stops_per_1000']:.1f} stops per 1,000 population—
        {'above' if high_imd['stops_per_1000'] > national_avg else 'below'} the national average.
        """)

    # Insight 4: Route density
    if 'routes_per_100k' in regional_data.columns:
        best_routes = regional_data.nlargest(1, 'routes_per_100k').iloc[0]
        worst_routes = regional_data.nsmallest(1, 'routes_per_100k').iloc[0]
        ratio = best_routes['routes_per_100k'] / worst_routes['routes_per_100k']

        st.markdown(f"""
        **🚌 Route Density Range**
        {best_routes['region_name']} ({best_routes['routes_per_100k']:.1f} routes/100k)
        has {ratio:.1f}x more routes per capita than {worst_routes['region_name']} ({worst_routes['routes_per_100k']:.1f}).
        """)

st.markdown("---")

# Regional comparison table
if not regional_data.empty:
    st.markdown("## 📈 Regional Performance")

    # Display clean table
    display_cols = [
        'region_name',
        'total_stops',
        'population',
        'stops_per_1000',
        'routes_count',
        'routes_per_100k'
    ]

    # Check which columns exist
    available_cols = [col for col in display_cols if col in regional_data.columns]

    if available_cols:
        # Rename columns for display
        display_df = regional_data[available_cols].copy()

        # Create display names
        col_rename = {
            'region_name': 'Region',
            'total_stops': 'Bus Stops',
            'population': 'Population',
            'stops_per_1000': 'Stops/1000',
            'routes_count': 'Routes',
            'routes_per_100k': 'Routes/100k'
        }

        display_df = display_df.rename(columns={k: v for k, v in col_rename.items() if k in display_df.columns})

        # Format numbers
        if 'Bus Stops' in display_df.columns:
            display_df['Bus Stops'] = display_df['Bus Stops'].apply(lambda x: f"{x:,}")
        if 'Population' in display_df.columns:
            display_df['Population'] = display_df['Population'].apply(lambda x: f"{x:,}")
        if 'Stops/1000' in display_df.columns:
            display_df['Stops/1000'] = display_df['Stops/1000'].apply(lambda x: f"{x:.1f}")
        if 'Routes' in display_df.columns:
            display_df['Routes'] = display_df['Routes'].apply(lambda x: f"{x:,}")
        if 'Routes/100k' in display_df.columns:
            display_df['Routes/100k'] = display_df['Routes/100k'].apply(lambda x: f"{x:.1f}")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

    st.markdown("---")

# Navigation guide
st.markdown("## 🧭 Analysis Categories")

st.markdown("""
Explore comprehensive analysis across analytical domains:

**Category A: Coverage & Accessibility** 🟢
Network density, service gaps, walking distances, urban/rural equity

**Category B: Service Quality** 🔵
Peak hour analysis, evening/weekend services, stop amenities, accessibility features

**Category C: Route Characteristics** 🔴
Route lengths, overlaps, connectivity patterns, network topology

**Category D: Socio-Economic Correlations** 👥
Deprivation, unemployment, demographics, income patterns

**Category F: Equity & Social Inclusion** ⚖️
Service distribution fairness, Gini coefficients, accessibility gaps, ethnic minority access

Use the sidebar to navigate to detailed analysis pages.
""")

st.markdown("---")

# Data sources footer
st.caption("""
**Data Sources:** BODS (Bus Open Data Service October 2024), ONS Census 2021, NaPTAN (National Public Transport Access Nodes), IMD 2019, NOMIS Labour Market Statistics
**Coverage:** 779,262 stops across 9 English regions
**Last Updated:** November 2025
""")
