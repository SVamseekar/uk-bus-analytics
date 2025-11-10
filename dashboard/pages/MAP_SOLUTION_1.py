"""
SOLUTION 1: Clean go.Choroplethmapbox implementation
Replace lines 128-312 in Home.py with this code
"""

with col_left:
    if metric_col in regional_data.columns:
        # Auto-detect GeoJSON code field
        props0 = region_boundaries["features"][0]["properties"]
        code_keys = [k for k in props0.keys() if k.upper().endswith("CD")]

        import re
        FEATURE_CODE = None
        for k in code_keys:
            vals = [str(f["properties"][k]).strip() for f in region_boundaries["features"]]
            if len(vals) == 9 and all(re.fullmatch(r"E120000[0-9]{2}", v) for v in vals):
                FEATURE_CODE = k
                break

        if FEATURE_CODE is None:
            FEATURE_CODE = "RGN21CD"

        FEATURE_NAME = "RGN21NM"
        featureidkey = f"properties.{FEATURE_CODE}"

        # Build code mappings
        all_codes = [str(f["properties"][FEATURE_CODE]).strip() for f in region_boundaries["features"]]
        code2name = {
            str(f["properties"][FEATURE_CODE]).strip():
            str(f["properties"].get(FEATURE_NAME, f["properties"][FEATURE_CODE])).strip()
            for f in region_boundaries["features"]
        }

        # Ensure ons_code exists
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

        regional_data["ons_code"] = regional_data["ons_code"].astype(str).str.strip()

        # Build value mapping
        vals = pd.to_numeric(regional_data[metric_col], errors="coerce")
        value_by_code = {}
        for code, val in zip(regional_data["ons_code"], vals):
            if pd.notna(val):
                value_by_code[str(code).strip()] = float(val)

        # Create aligned arrays (9 elements)
        locations = all_codes
        z_values = [value_by_code.get(code, None) for code in all_codes]
        custom_text = [f"{code2name.get(code, code)}<br>{value_by_code.get(code, 'N/A')}" for code in all_codes]

        # Calculate z-range from finite values
        import numpy as np
        finite_vals = [v for v in z_values if v is not None and np.isfinite(v)]
        if finite_vals:
            z_min, z_max = float(min(finite_vals)), float(max(finite_vals))
            if z_min == z_max:
                z_min -= 0.5
                z_max += 0.5
        else:
            z_min, z_max = 0, 1

        # Build map using go.Choroplethmapbox
        fig = go.Figure(go.Choroplethmapbox(
            geojson=region_boundaries,
            locations=locations,
            z=z_values,
            featureidkey=featureidkey,
            colorscale=colorscale,
            zmin=z_min,
            zmax=z_max,
            marker_opacity=0.7,
            marker_line_width=2,
            marker_line_color="rgba(200,220,240,0.6)",
            text=custom_text,
            hovertemplate="<b>%{text}</b><extra></extra>",
            colorbar=dict(
                title=dict(text=selected_metric_label, font=dict(size=11, color="white")),
                len=0.6,
                thickness=15,
                x=1.01,
                tickfont=dict(size=9, color="white"),
                bgcolor="rgba(20,20,25,0.85)",
                bordercolor="rgba(255,255,255,0.25)",
                borderwidth=1
            )
        ))

        fig.update_layout(
            mapbox_style=basemap_style,
            mapbox_zoom=4.8,
            mapbox_center={"lat": 52.8, "lon": -1.5},
            margin=dict(l=0, r=0, t=0, b=0),
            height=600,
            paper_bgcolor='#0e1117',
            font=dict(color="white")
        )

        # Attribution
        fig.add_annotation(
            text="Map: © CARTO, © OpenStreetMap | Boundaries: ONS (OGL v3.0)",
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
