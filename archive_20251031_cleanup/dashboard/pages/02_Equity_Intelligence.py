"""
Equity Intelligence Module
=========================
Analyze transport equity across socio-economic dimensions
Measure how well service provision aligns with community needs

Author: UK Bus Analytics Platform
Date: 2025-10-29
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.data_loader import load_lsoa_metrics, get_summary_statistics
from dashboard.utils.ui_components import (
    apply_professional_config,
    load_professional_css,
    render_navigation_bar,
    render_dashboard_header,
    render_kpi_card,
    render_section_divider,
    create_responsive_columns,
    apply_plotly_theme,
    render_methodology_citation
)

# Page config
st.set_page_config(
    page_title="Equity Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply professional design
load_professional_css()
apply_professional_config()

# Navigation Bar
render_navigation_bar()

# Header
render_dashboard_header(
    title="Equity Intelligence",
    subtitle="Measure transport equity and identify communities requiring intervention with IMD overlay",
    icon="⚖️"
)

# Load data
try:
    lsoa_data = load_lsoa_metrics()
    stats = get_summary_statistics(lsoa_data)

    # Analysis Settings in main area
    render_section_divider("Analysis Settings", icon="⚙️")

    col1, col2, col3 = st.columns(3)

    with col1:
        analysis_type = st.selectbox(
            "Equity Analysis Type",
            ["Deprivation Equity", "Demographic Equity", "Multi-Dimensional Equity"],
            help="Choose the equity dimension to analyze"
        )

    with col2:
        equity_threshold = st.slider(
            "Equity Gap Threshold",
            min_value=0,
            max_value=100,
            value=25,
            help="Areas below this percentile are flagged as equity gaps"
        )

    with col3:
        show_priority_areas = st.checkbox(
            "Highlight Priority Intervention Areas",
            value=True,
            help="Show areas with low equity requiring urgent action"
        )

    st.markdown("---")

    # National Equity Overview
    render_section_divider("National Equity Overview", icon="📊")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        avg_equity = lsoa_data['equity_index'].mean()
        st.metric(
            "National Equity Score",
            f"{avg_equity:.2f}/100",
            help="Composite equity index (higher = better alignment of service with need)"
        )

    with kpi2:
        equity_gap_threshold_value = lsoa_data['equity_index'].quantile(equity_threshold/100)
        equity_gaps = len(lsoa_data[lsoa_data['equity_index'] < equity_gap_threshold_value])
        st.metric(
            "Equity Gap Areas",
            f"{equity_gaps:,}",
            help=f"Areas in bottom {equity_threshold}% of equity scores"
        )

    with kpi3:
        affected_pop = lsoa_data[lsoa_data['equity_index'] < equity_gap_threshold_value]['population'].sum()
        st.metric(
            "Affected Population",
            f"{affected_pop:,}",
            help="People living in equity gap areas"
        )

    with kpi4:
        # Correlation between deprivation and coverage
        corr = lsoa_data[['imd_score', 'coverage_score']].corr().iloc[0, 1]
        st.metric(
            "Deprivation-Service Correlation",
            f"{corr:.3f}",
            help="Correlation coefficient (-1 to +1)"
        )

    st.markdown("---")

    # Deprivation Equity Analysis
    if analysis_type == "Deprivation Equity":
        st.markdown("### 🎯 Deprivation-Service Equity Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Scatter: Deprivation vs Coverage
            st.markdown("#### Service Provision by Deprivation Level")

            # Add ideal equity line data
            ideal_line = pd.DataFrame({
                'imd_decile': [1, 10],
                'ideal_coverage': [90, 10]  # High deprivation should have high service
            })

            fig = px.scatter(
                lsoa_data,
                x='imd_decile',
                y='coverage_score',
                color='equity_index',
                size='population',
                hover_data=['lsoa_code', 'locality'],
                title='Coverage Score vs Deprivation Decile',
                labels={
                    'imd_decile': 'IMD Decile (1=Most Deprived, 10=Least)',
                    'coverage_score': 'Coverage Score',
                    'equity_index': 'Equity Index'
                },
                color_continuous_scale='RdYlGn'
            )

            # Add ideal equity line
            fig.add_scatter(
                x=ideal_line['imd_decile'],
                y=ideal_line['ideal_coverage'],
                mode='lines',
                name='Ideal Equity Line',
                line=dict(dash='dash', color='blue', width=2)
            )

            st.plotly_chart(fig, use_container_width=True)

            st.info("💡 **Interpretation**: Points below the ideal line indicate areas where deprived communities have inadequate service relative to their needs.")

        with col2:
            # Box plot: Coverage by deprivation decile
            st.markdown("#### Coverage Distribution by Deprivation")

            fig_box = px.box(
                lsoa_data,
                x='imd_decile',
                y='coverage_score',
                color='imd_decile',
                title='Service Coverage Distribution by Deprivation Decile',
                labels={
                    'imd_decile': 'IMD Decile',
                    'coverage_score': 'Coverage Score'
                },
                color_continuous_scale='RdYlGn_r'
            )

            st.plotly_chart(fig_box, use_container_width=True)

            # Summary by decile
            decile_summary = lsoa_data.groupby('imd_decile').agg({
                'coverage_score': 'mean',
                'stops_per_capita': 'mean',
                'population': 'sum'
            }).round(2)

            st.markdown("#### Average Coverage by Decile")
            st.dataframe(
                decile_summary,
                use_container_width=True,
                column_config={
                    'coverage_score': st.column_config.NumberColumn(
                        'Avg Coverage',
                        format="%.2f"
                    ),
                    'stops_per_capita': st.column_config.NumberColumn(
                        'Stops per 1k',
                        format="%.2f"
                    ),
                    'population': st.column_config.NumberColumn(
                        'Total Population',
                        format="%d"
                    )
                }
            )

    # Demographic Equity Analysis
    elif analysis_type == "Demographic Equity":
        st.markdown("### 👥 Demographic Equity Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Elderly Population Service Provision")

            fig_elderly = px.scatter(
                lsoa_data,
                x='elderly_pct',
                y='coverage_score',
                color='equity_index',
                size='population',
                hover_data=['lsoa_code', 'locality'],
                title='Coverage vs Elderly Population Percentage',
                labels={
                    'elderly_pct': 'Elderly Population (%)',
                    'coverage_score': 'Coverage Score',
                    'equity_index': 'Equity Index'
                },
                color_continuous_scale='RdYlGn'
            )

            st.plotly_chart(fig_elderly, use_container_width=True)

            # Correlation
            elderly_corr = lsoa_data[['elderly_pct', 'coverage_score']].corr().iloc[0, 1]
            st.metric(
                "Elderly-Service Correlation",
                f"{elderly_corr:.3f}",
                help="Should be positive: higher elderly % should have better service"
            )

        with col2:
            st.markdown("#### Car Ownership vs Service Provision")

            fig_car = px.scatter(
                lsoa_data,
                x='car_ownership_rate',
                y='coverage_score',
                color='equity_index',
                size='population',
                hover_data=['lsoa_code', 'locality'],
                title='Coverage vs Car Ownership Rate',
                labels={
                    'car_ownership_rate': 'Car Ownership Rate',
                    'coverage_score': 'Coverage Score',
                    'equity_index': 'Equity Index'
                },
                color_continuous_scale='RdYlGn'
            )

            st.plotly_chart(fig_car, use_container_width=True)

            # Correlation
            car_corr = lsoa_data[['car_ownership_rate', 'coverage_score']].corr().iloc[0, 1]
            st.metric(
                "Car Ownership-Service Correlation",
                f"{car_corr:.3f}",
                help="Should be negative: lower car ownership should have better service"
            )

    # Multi-Dimensional Equity
    else:  # Multi-Dimensional Equity
        st.markdown("### 🎨 Multi-Dimensional Equity Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Equity index distribution
            st.markdown("#### Equity Index Distribution")

            fig_hist = px.histogram(
                lsoa_data,
                x='equity_index',
                nbins=50,
                title="Distribution of Equity Scores",
                labels={'equity_index': 'Equity Index (0-100)', 'count': 'Number of Areas'},
                color_discrete_sequence=['#2ca02c']
            )

            fig_hist.add_vline(
                x=lsoa_data['equity_index'].mean(),
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {lsoa_data['equity_index'].mean():.1f}"
            )

            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            # 3D scatter: Deprivation, Coverage, Equity
            st.markdown("#### Multi-Dimensional Equity View")

            fig_3d = go.Figure(data=[go.Scatter3d(
                x=lsoa_data['imd_decile'],
                y=lsoa_data['coverage_score'],
                z=lsoa_data['equity_index'],
                mode='markers',
                marker=dict(
                    size=4,
                    color=lsoa_data['equity_index'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Equity Index")
                ),
                text=lsoa_data['lsoa_code'],
                hovertemplate='<b>%{text}</b><br>' +
                              'IMD Decile: %{x}<br>' +
                              'Coverage: %{y:.1f}<br>' +
                              'Equity: %{z:.1f}<br>' +
                              '<extra></extra>'
            )])

            fig_3d.update_layout(
                title="Equity in 3D: Deprivation × Coverage × Equity Index",
                scene=dict(
                    xaxis_title='IMD Decile',
                    yaxis_title='Coverage Score',
                    zaxis_title='Equity Index'
                ),
                height=500
            )

            st.plotly_chart(fig_3d, use_container_width=True)

    # Priority Intervention Areas
    if show_priority_areas:
        st.markdown("---")
        st.markdown("### 🎯 Priority Intervention Areas")

        # Define priority criteria: High deprivation + Low equity
        priority_areas = lsoa_data[
            (lsoa_data['imd_decile'] <= 3) &  # Most deprived (deciles 1-3)
            (lsoa_data['equity_index'] < lsoa_data['equity_index'].quantile(0.25))  # Bottom 25% equity
        ].copy()

        priority_areas = priority_areas.sort_values('equity_index')

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Priority Areas Identified",
                f"{len(priority_areas):,}",
                help="High deprivation + low equity areas"
            )

        with col2:
            st.metric(
                "Priority Population",
                f"{priority_areas['population'].sum():,}",
                help="People in priority intervention areas"
            )

        with col3:
            avg_priority_equity = priority_areas['equity_index'].mean()
            st.metric(
                "Avg Equity in Priority Areas",
                f"{avg_priority_equity:.2f}",
                delta=f"{avg_priority_equity - lsoa_data['equity_index'].mean():.2f} vs national"
            )

        # Priority areas table
        st.markdown("#### Top 30 Priority Intervention Areas")

        priority_display = priority_areas[[
            'lsoa_code', 'locality', 'equity_index', 'coverage_score',
            'imd_decile', 'stops_per_capita', 'population', 'elderly_pct'
        ]].head(30)

        st.dataframe(
            priority_display,
            use_container_width=True,
            column_config={
                'equity_index': st.column_config.ProgressColumn(
                    'Equity Score',
                    format="%.1f",
                    min_value=0,
                    max_value=100
                ),
                'coverage_score': st.column_config.ProgressColumn(
                    'Coverage',
                    format="%.1f",
                    min_value=0,
                    max_value=100
                ),
                'elderly_pct': st.column_config.NumberColumn(
                    'Elderly %',
                    format="%.1f%%"
                )
            }
        )

        # Download priority areas
        st.markdown("#### Export Priority Areas")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="📥 CSV",
                data=priority_areas.to_csv(index=False),
                file_name="priority_intervention_areas.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            st.download_button(
                label="📥 JSON",
                data=priority_areas.to_json(orient='records', indent=2),
                file_name="priority_intervention_areas.json",
                mime="application/json",
                use_container_width=True
            )

        with col3:
            try:
                from io import BytesIO
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    priority_areas.to_excel(writer, sheet_name='Priority Areas', index=False)
                st.download_button(
                    label="📥 Excel",
                    data=buffer.getvalue(),
                    file_name="priority_intervention_areas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except:
                st.caption("Excel export unavailable")

    # Equity Gap Summary
    st.markdown("---")
    st.markdown("### 📋 Equity Gap Summary by Locality")

    # Group by locality
    locality_equity = lsoa_data.groupby('locality').agg({
        'equity_index': 'mean',
        'coverage_score': 'mean',
        'population': 'sum',
        'imd_score': 'mean'
    }).round(2).sort_values('equity_index').head(20)

    fig_bar = px.bar(
        locality_equity.reset_index(),
        x='equity_index',
        y='locality',
        orientation='h',
        title='Bottom 20 Localities by Equity Score',
        labels={'equity_index': 'Average Equity Index', 'locality': ''},
        color='equity_index',
        color_continuous_scale='RdYlGn'
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # Key Insights
    st.markdown("---")
    st.markdown("### 💡 Key Equity Insights")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown("#### Deprivation Equity")
        most_deprived_coverage = lsoa_data[lsoa_data['imd_decile'] <= 3]['coverage_score'].mean()
        least_deprived_coverage = lsoa_data[lsoa_data['imd_decile'] >= 8]['coverage_score'].mean()

        if most_deprived_coverage > least_deprived_coverage:
            st.success(f"✅ **Progressive**: Most deprived areas have {most_deprived_coverage:.1f} vs {least_deprived_coverage:.1f} coverage")
        else:
            st.error(f"⚠️ **Regressive**: Most deprived areas have {most_deprived_coverage:.1f} vs {least_deprived_coverage:.1f} coverage")

    with insight_col2:
        st.markdown("#### Elderly Service")
        high_elderly_coverage = lsoa_data[lsoa_data['elderly_pct'] > 0.20]['coverage_score'].mean()
        low_elderly_coverage = lsoa_data[lsoa_data['elderly_pct'] < 0.15]['coverage_score'].mean()

        if high_elderly_coverage > low_elderly_coverage:
            st.success(f"✅ **Good**: High elderly areas have {high_elderly_coverage:.1f} coverage")
        else:
            st.warning(f"⚠️ **Needs Attention**: High elderly areas have {high_elderly_coverage:.1f} coverage")

    with insight_col3:
        st.markdown("#### Car Dependency")
        low_car_coverage = lsoa_data[lsoa_data['car_ownership_rate'] < 0.60]['coverage_score'].mean()
        high_car_coverage = lsoa_data[lsoa_data['car_ownership_rate'] > 0.80]['coverage_score'].mean()

        if low_car_coverage > high_car_coverage:
            st.success(f"✅ **Equitable**: Low car ownership areas have {low_car_coverage:.1f} coverage")
        else:
            st.warning(f"⚠️ **Gap**: Low car ownership areas have {low_car_coverage:.1f} coverage")

    # Methodology Citations
    st.markdown("---")
    render_methodology_citation(['OECD Spatial Equity Frameworks', 'Social Value UK Guidelines', 'DfT TAG Unit A4.1'])

except Exception as e:
    st.error(f"Error loading equity data: {str(e)}")
    st.info("Please ensure spatial metrics have been computed.")
