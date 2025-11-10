"""
SOLUTION 2: Folium implementation (more robust for GeoJSON)
Requires: pip install folium streamlit-folium

Add to imports:
import folium
from streamlit_folium import st_folium

Replace map section with this code:
"""

with col_left:
    if metric_col in regional_data.columns:
        # Build mapping
        if "ons_code" not in regional_data.columns:
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

        # Create Folium map
        m = folium.Map(
            location=[52.8, -1.5],
            zoom_start=6,
            tiles='cartodbdark_matter' if basemap_style == 'carto-darkmatter' else 'cartodbpositron'
        )

        # Create choropleth
        folium.Choropleth(
            geo_data=region_boundaries,
            name='choropleth',
            data=regional_data,
            columns=['ons_code', metric_col],
            key_on='feature.properties.RGN21CD',  # Adjust to match your GeoJSON
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.5,
            legend_name=selected_metric_label,
            highlight=True
        ).add_to(m)

        # Add tooltips
        folium.GeoJsonTooltip(
            fields=['RGN21NM'],
            aliases=['Region:'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        ).add_to(m)

        # Display
        st_folium(m, width=700, height=600)
    else:
        st.error(f"Metric '{metric_col}' not found in regional data")
