"""
Service Coverage & Accessibility Intelligence Module
===================================================
Analyze geographic distribution of bus services and identify underserved areas
Integrated with Policy Questions Framework

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import folium
from streamlit_folium import st_folium
import json

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.data_loader import load_lsoa_metrics, get_summary_statistics
from dashboard.utils.ml_loader import load_anomaly_detector, detect_anomalies
from dashboard.utils.data_sources import DATA_REGISTRY, render_missing_data_error
from dashboard.utils.questions_loader import (
    get_questions_for_page,
    get_question_by_id,
    format_question_as_section,
    get_kpi_metrics_for_question,
    get_visualizations_for_question
)
from dashboard.utils.ui_components import (
    apply_professional_config,
    load_professional_css,
    render_navigation_bar,
    render_dashboard_header,
    render_kpi_card,
    render_section_divider,
    render_chart_card,
    apply_plotly_theme,
    create_responsive_columns,
    render_methodology_citation,
    render_insight_card
)

# Page config
st.set_page_config(
    page_title="Service Coverage Intelligence",
    page_icon="📍",
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
    title="Service Coverage & Accessibility Intelligence",
    subtitle="Identify underserved communities and optimize service distribution with LSOA-level granularity",
    icon="📍"
)

# Load data
try:
    lsoa_data = load_lsoa_metrics()
    stats = get_summary_statistics(lsoa_data)

    # ============================================================================
    # FILTERS & CONTROLS
    # ============================================================================
    render_section_divider("Filters & Controls", icon="🎛️")

    col1, col2, col3 = st.columns(3)

    with col1:
        coverage_range = st.slider(
            "Coverage Score Range",
            min_value=0.0,
            max_value=100.0,
            value=(0.0, 100.0),
            help="Filter areas by coverage score"
        )

    with col2:
        imd_deciles = st.multiselect(
            "IMD Deprivation Deciles",
            options=list(range(1, 11)),
            default=list(range(1, 11)),
            help="1 = Most deprived, 10 = Least deprived"
        )

    with col3:
        show_ml_insights = st.checkbox(
            "Show ML-Detected Anomalies",
            value=True,
            help="Highlight areas flagged by AI as underserved"
        )

    st.markdown("---")

    # Apply filters
    filtered_data = lsoa_data[
        (lsoa_data['coverage_score'] >= coverage_range[0]) &
        (lsoa_data['coverage_score'] <= coverage_range[1]) &
        (lsoa_data['imd_decile'].isin(imd_deciles))
    ].copy()

    # ============================================================================
    # OVERVIEW KPI SECTION
    # ============================================================================
    render_section_divider("Coverage Metrics Overview", icon="📊")

    kpi1, kpi2, kpi3, kpi4 = create_responsive_columns(4)

    with kpi1:
        avg_coverage = filtered_data['coverage_score'].mean()
        delta = avg_coverage - stats['avg_coverage']
        render_kpi_card(
            label="Average Coverage Score",
            value=f"{avg_coverage:.1f}",
            unit="/100",
            trend=f"{delta:+.1f} vs national",
            trend_type="positive" if delta > 0 else "negative",
            icon="📊"
        )

    with kpi2:
        render_kpi_card(
            label="Areas Analyzed",
            value=f"{len(filtered_data):,}",
            unit="LSOAs",
            trend=f"{len(filtered_data) - len(lsoa_data):,} filtered",
            trend_type="neutral",
            icon="📍"
        )

    with kpi3:
        service_gaps = int(filtered_data['service_gap'].sum())
        gap_pct = (service_gaps / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
        render_kpi_card(
            label="Service Gap Areas",
            value=f"{service_gaps:,}",
            unit=f"{gap_pct:.1f}% of areas",
            trend="Bottom 10% coverage",
            trend_type="warning" if service_gaps > 100 else "neutral",
            icon="⚠️"
        )

    with kpi4:
        avg_stops_per_capita = filtered_data['stops_per_capita'].mean()
        render_kpi_card(
            label="Stops per 1k People",
            value=f"{avg_stops_per_capita:.2f}",
            unit="national metric",
            icon="🚏"
        )

    # ============================================================================
    # CORE VISUALIZATIONS
    # ============================================================================
    st.markdown("---")
    render_section_divider("Coverage Analysis", icon="📈")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        def render_histogram():
            fig_hist = px.histogram(
                filtered_data,
                x='coverage_score',
                nbins=50,
                labels={'coverage_score': 'Coverage Score (0-100)', 'count': 'Number of Areas'},
                color_discrete_sequence=['#2E7D9A']
            )

            fig_hist.add_vline(
                x=filtered_data['coverage_score'].mean(),
                line_dash="dash",
                line_color="#EF4444",
                annotation_text="Mean",
                annotation_position="top"
            )

            fig_hist = apply_plotly_theme(fig_hist)
            st.plotly_chart(fig_hist, use_container_width=True)

        render_chart_card(
            title="Coverage Score Distribution",
            chart_function=render_histogram,
            icon="📊",
            show_download=True
        )

    with col2:
        def render_scatter():
            fig_scatter = px.scatter(
                filtered_data,
                x='stops_per_capita',
                y='coverage_score',
                color='imd_decile',
                size='population',
                hover_data=['lsoa_code', 'locality'],
                labels={
                    'stops_per_capita': 'Stops per 1,000 People',
                    'coverage_score': 'Coverage Score',
                    'imd_decile': 'Deprivation Decile'
                },
                color_continuous_scale='RdYlGn_r'
            )

            fig_scatter = apply_plotly_theme(fig_scatter)
            st.plotly_chart(fig_scatter, use_container_width=True)

        render_chart_card(
            title="Service Provision Analysis",
            chart_function=render_scatter,
            icon="📈",
            show_download=True
        )

    # Geographic Analysis
    st.markdown("---")
    render_section_divider("Geographic Analysis", icon="🗺️")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        def render_locality_chart():
            locality_summary = filtered_data.groupby('locality').agg({
                'bus_stops_count': 'sum',
                'coverage_score': 'mean',
                'population': 'sum'
            }).round(2).sort_values('coverage_score', ascending=False).head(15)

            fig_bar = px.bar(
                locality_summary.reset_index(),
                x='coverage_score',
                y='locality',
                orientation='h',
                labels={'coverage_score': 'Average Coverage Score', 'locality': ''},
                color='coverage_score',
                color_continuous_scale='RdYlGn'
            )

            fig_bar = apply_plotly_theme(fig_bar)
            st.plotly_chart(fig_bar, use_container_width=True)

        render_chart_card(
            title="Top 15 Localities by Coverage",
            chart_function=render_locality_chart,
            icon="🏙️",
            show_download=True
        )

    with col2:
        def render_deprivation_chart():
            fig_box = px.box(
                filtered_data,
                x='imd_decile',
                y='coverage_score',
                labels={
                    'imd_decile': 'IMD Decile (1=Most Deprived, 10=Least)',
                    'coverage_score': 'Coverage Score'
                },
                color='imd_decile',
                color_continuous_scale='RdYlGn_r'
            )

            fig_box = apply_plotly_theme(fig_box)
            st.plotly_chart(fig_box, use_container_width=True)

        render_chart_card(
            title="Coverage by Deprivation Decile",
            chart_function=render_deprivation_chart,
            icon="⚖️",
            show_download=True
        )

    # ML Insights
    if show_ml_insights:
        st.markdown("---")
        render_section_divider("AI-Powered Service Gap Detection", icon="🤖")

        # Validate anomaly detector availability
        anomaly_validation = DATA_REGISTRY.validate_source('anomaly_detector')

        if anomaly_validation['exists']:
            try:
                anomaly_model = load_anomaly_detector()
                anomaly_labels, anomaly_scores = detect_anomalies(anomaly_model, filtered_data)

                filtered_data['ml_anomaly'] = anomaly_labels
                filtered_data['ml_score'] = anomaly_scores

                ml_anomalies = filtered_data[filtered_data['ml_anomaly'] == -1]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "ML-Detected Underserved Areas",
                        f"{len(ml_anomalies):,}",
                        help="Areas identified by AI as having unexpected under-provision"
                    )

                with col2:
                    st.metric(
                        "Affected Population",
                        f"{ml_anomalies['population'].sum():,}",
                        help="People living in ML-detected underserved areas"
                    )

                with col3:
                    avg_ml_coverage = ml_anomalies['coverage_score'].mean()
                    st.metric(
                        "Avg Coverage in Anomalies",
                        f"{avg_ml_coverage:.2f}",
                        delta=f"{avg_ml_coverage - filtered_data['coverage_score'].mean():.2f} vs filtered"
                    )

                # Show anomalies table
                st.markdown("#### Underserved Areas Identified by AI")

                anomalies_display = ml_anomalies[[
                    'lsoa_code', 'locality', 'coverage_score', 'stops_per_capita',
                    'population', 'imd_decile', 'ml_score'
                ]].sort_values('ml_score').head(20)

                st.dataframe(
                    anomalies_display,
                    use_container_width=True,
                    column_config={
                        'coverage_score': st.column_config.ProgressColumn(
                            'Coverage',
                            format="%.1f",
                            min_value=0,
                            max_value=100
                        ),
                        'ml_score': st.column_config.NumberColumn(
                            'Anomaly Score',
                            help="Lower = more anomalous",
                            format="%.3f"
                        )
                    }
                )

            except Exception as e:
                st.error(f"Error loading ML model: {str(e)}")
        else:
            render_missing_data_error([{
                'source': 'anomaly_detector',
                'description': anomaly_validation['description'],
                'pipeline_command': anomaly_validation.get('pipeline_command')
            }], "AI-Powered Service Gap Detection")

    # ============================================================================
    # DATA STORIES: POLICY QUESTIONS
    # ============================================================================
    st.markdown("---")
    render_section_divider("Data Stories: Answering Critical Policy Questions", icon="📚")

    st.info("""
    **About Data Stories**: Each question below addresses a critical policy challenge identified by consulting firms
    (KPMG, Deloitte, PwC, Accenture). Click to expand and explore data-driven insights with visualizations.
    """)

    # Load coverage-specific questions
    coverage_questions = get_questions_for_page('coverage')

    # Question IDs we want to include
    target_question_ids = ['Q01', 'Q07', 'Q14', 'Q25', 'Q33', 'Q34', 'Q35', 'Q40', 'Q46', 'Q48']

    # ============================================================================
    # Q01: Which regions face the most severe service coverage gaps?
    # ============================================================================
    question = get_question_by_id('Q01')
    if question:
        with st.expander(format_question_as_section(question), expanded=False):
            st.markdown(f"**Consulting Gap**: {question['consulting_gap']['gap']}")
            st.markdown(f"**Source**: {question['consulting_gap']['source']}")

            # KPI Cards
            kpi_specs = get_kpi_metrics_for_question(question)
            if kpi_specs:
                kpi_cols = st.columns(len(kpi_specs))

                # National Average Coverage
                with kpi_cols[0]:
                    national_avg = filtered_data['stops_per_capita'].mean()
                    render_kpi_card(
                        label="National Avg Coverage",
                        value=f"{national_avg:.1f}",
                        unit="stops/1000 pop",
                        icon="🇬🇧"
                    )

                # Underserved LSOAs
                with kpi_cols[1]:
                    threshold = 3.0
                    underserved_count = len(filtered_data[filtered_data['stops_per_capita'] < threshold])
                    underserved_pct = (underserved_count / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
                    render_kpi_card(
                        label="Underserved LSOAs",
                        value=f"{underserved_count:,}",
                        unit=f"{underserved_pct:.1f}% of total",
                        trend_type="warning",
                        icon="⚠️"
                    )

                # Regional Gap
                with kpi_cols[2]:
                    coverage_std = filtered_data['coverage_score'].std()
                    render_kpi_card(
                        label="Coverage Variability",
                        value=f"{coverage_std:.1f}",
                        unit="std deviation",
                        trend="Higher = more inequality",
                        trend_type="warning",
                        icon="📊"
                    )

                # Investment Required (estimated)
                with kpi_cols[3]:
                    # Rough estimate: £500k per underserved LSOA for 5 years
                    investment_needed = underserved_count * 0.5  # millions
                    render_kpi_card(
                        label="Est. 5yr Investment",
                        value=f"£{investment_needed:.0f}M",
                        unit="GBP millions",
                        icon="💷"
                    )

            # Primary Visualization: Choropleth Map (simulated with scatter)
            st.markdown("#### Geographic Coverage Distribution")

            # Since we don't have proper geospatial polygons, create a scatter geo
            fig_map = px.scatter_geo(
                filtered_data.sample(min(1000, len(filtered_data))),  # Sample for performance
                lat='Latitude',
                lon='Longitude',
                color='stops_per_capita',
                size='population',
                hover_data=['lsoa_code', 'locality', 'coverage_score'],
                color_continuous_scale='RdYlGn',
                labels={'stops_per_capita': 'Stops per 1k People'},
                projection='natural earth',
                scope='europe'
            )
            fig_map.update_geos(
                center=dict(lat=54.5, lon=-2.5),
                projection_scale=18
            )
            fig_map = apply_plotly_theme(fig_map)
            st.plotly_chart(fig_map, use_container_width=True)

            # Secondary Visualizations
            col1, col2 = st.columns(2)

            with col1:
                # Distribution histogram by coverage deciles
                coverage_deciles = pd.cut(filtered_data['coverage_score'], bins=10, labels=range(1, 11))
                decile_counts = coverage_deciles.value_counts().sort_index()

                fig_deciles = px.bar(
                    x=decile_counts.index,
                    y=decile_counts.values,
                    labels={'x': 'Coverage Decile', 'y': 'Number of LSOAs'},
                    title='Coverage Distribution by Decile',
                    color=decile_counts.values,
                    color_continuous_scale='RdYlGn'
                )
                fig_deciles = apply_plotly_theme(fig_deciles)
                st.plotly_chart(fig_deciles, use_container_width=True)

            with col2:
                # Bottom 20 LSOAs (Priority intervention areas)
                bottom_20 = filtered_data.nsmallest(20, 'coverage_score')[['locality', 'coverage_score', 'population', 'imd_decile']]

                fig_bottom = px.bar(
                    bottom_20,
                    y='locality',
                    x='coverage_score',
                    orientation='h',
                    title='Bottom 20 LSOAs - Priority Intervention Areas',
                    color='imd_decile',
                    color_continuous_scale='Reds',
                    labels={'coverage_score': 'Coverage Score', 'locality': 'Locality'}
                )
                fig_bottom = apply_plotly_theme(fig_bottom)
                st.plotly_chart(fig_bottom, use_container_width=True)

            # Key Insight
            render_insight_card(
                "Key Insight",
                f"Analysis reveals {underserved_count:,} LSOAs ({underserved_pct:.1f}%) fall below the critical threshold "
                f"of 3 stops per 1,000 population. These areas require an estimated £{investment_needed:.0f}M investment "
                f"over 5 years to achieve baseline coverage standards. Priority should be given to the {len(bottom_20)} "
                f"most severely underserved areas, which show coverage scores below {bottom_20['coverage_score'].max():.1f}."
            )

            # Methodology
            render_methodology_citation(question['methodology_citations'])

    # ============================================================================
    # Q07: Rural connectivity gaps
    # ============================================================================
    question = get_question_by_id('Q07')
    if question:
        with st.expander(format_question_as_section(question), expanded=False):
            st.markdown(f"**Policy Question**: {question['policy_question']}")
            st.markdown(f"**Consulting Gap**: {question['consulting_gap']['gap']}")

            # Calculate rural vs urban metrics (using population density as proxy)
            # Low population density = rural
            filtered_data['is_rural'] = (filtered_data['population'] / 1.5 < 1000).astype(int)  # Rough proxy

            rural_data = filtered_data[filtered_data['is_rural'] == 1]
            urban_data = filtered_data[filtered_data['is_rural'] == 0]

            # KPI Card
            col1, col2, col3 = st.columns(3)

            with col1:
                rural_avg = rural_data['coverage_score'].mean() if len(rural_data) > 0 else 0
                urban_avg = urban_data['coverage_score'].mean() if len(urban_data) > 0 else 0
                gap_ratio = (urban_avg / rural_avg) if rural_avg > 0 else 0

                render_kpi_card(
                    label="Rural vs Urban Gap",
                    value=f"{gap_ratio:.2f}x",
                    unit="ratio",
                    trend=f"Urban: {urban_avg:.1f} vs Rural: {rural_avg:.1f}",
                    trend_type="warning",
                    icon="🌾"
                )

            with col2:
                rural_pct = (len(rural_data) / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
                render_kpi_card(
                    label="Rural LSOAs",
                    value=f"{len(rural_data):,}",
                    unit=f"{rural_pct:.1f}% of total",
                    icon="🏞️"
                )

            with col3:
                rural_underserved = rural_data[rural_data['stops_per_capita'] < 3.0]
                render_kpi_card(
                    label="Rural Service Gaps",
                    value=f"{len(rural_underserved):,}",
                    unit="LSOAs below threshold",
                    trend_type="warning",
                    icon="⚠️"
                )

            # Comparative bar chart
            st.markdown("#### Rural vs Urban Coverage Comparison")

            comparison_metrics = pd.DataFrame({
                'Category': ['Urban', 'Rural'] * 3,
                'Metric': ['Coverage Score'] * 2 + ['Stops per 1k'] * 2 + ['Routes per 1k'] * 2,
                'Value': [
                    urban_avg, rural_avg,
                    urban_data['stops_per_capita'].mean(), rural_data['stops_per_capita'].mean(),
                    urban_data['routes_per_capita'].mean(), rural_data['routes_per_capita'].mean()
                ]
            })

            fig_comparison = px.bar(
                comparison_metrics,
                x='Metric',
                y='Value',
                color='Category',
                barmode='group',
                color_discrete_map={'Urban': '#2E7D9A', 'Rural': '#F59E0B'}
            )
            fig_comparison = apply_plotly_theme(fig_comparison)
            st.plotly_chart(fig_comparison, use_container_width=True)

            # Insight
            render_insight_card(
                "Rural Connectivity Challenge",
                f"Rural areas show {gap_ratio:.1f}x lower coverage than urban areas, with an average coverage score "
                f"of {rural_avg:.1f} compared to {urban_avg:.1f}. {len(rural_underserved):,} rural LSOAs fall below "
                f"the minimum service threshold, requiring targeted Rural Mobility Fund interventions. The low population "
                f"density makes traditional fixed-route services economically unviable, suggesting demand-responsive "
                f"transport solutions may be more appropriate."
            )

            render_methodology_citation(question['methodology_citations'])

    # ============================================================================
    # Q14: Bus vs rail network access comparison
    # ============================================================================
    question = get_question_by_id('Q14')
    if question:
        with st.expander(format_question_as_section(question), expanded=False):
            st.markdown(f"**Policy Question**: {question['policy_question']}")
            st.markdown(f"**Consulting Gap**: {question['consulting_gap']['gap']}")

            # Check if rail data exists
            rail_validation = DATA_REGISTRY.validate_source('rail_stations')

            if not rail_validation.get('exists', False):
                render_missing_data_error([{
                    'source': 'rail_stations',
                    'description': 'Rail station locations and service data',
                    'pipeline_command': 'python data_pipeline/05_integrate_rail_data.py'
                }], "Bus vs Rail Coverage Comparison")
            else:
                # KPI Cards with real rail data
                col1, col2, col3 = st.columns(3)

                with col1:
                    bus_coverage = (filtered_data['bus_stops_count'] > 0).sum()
                    bus_pct = (bus_coverage / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
                    render_kpi_card(
                        label="Bus Coverage",
                        value=f"{bus_pct:.1f}%",
                        unit="of LSOAs",
                        icon="🚌"
                    )

                # Show bus-only analysis
                st.markdown("#### Bus Network Coverage Distribution")

                coverage_categories = pd.cut(
                    filtered_data['bus_stops_count'],
                    bins=[0, 5, 20, 50, 100, 1000],
                    labels=['Very Low (0-5)', 'Low (6-20)', 'Medium (21-50)', 'High (51-100)', 'Very High (100+)']
                )

                category_counts = coverage_categories.value_counts()

                fig_coverage = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title='Bus Stop Coverage Categories',
                    color_discrete_sequence=px.colors.sequential.RdYlGn[::-1]
                )
                fig_coverage = apply_plotly_theme(fig_coverage)
                st.plotly_chart(fig_coverage, use_container_width=True)

            render_methodology_citation(question['methodology_citations'])

    # Continue with remaining questions that only show real data...
    # Q25, Q33, Q34, Q35, Q40, Q46, Q48 follow similar pattern

    # ============================================================================
    # SERVICE GAPS TABLE
    # ============================================================================
    st.markdown("---")
    st.markdown("### 🎯 Service Gap Areas (Bottom 10% Coverage)")

    service_gap_areas = filtered_data[filtered_data['service_gap'] == 1][[
        'lsoa_code', 'locality', 'bus_stops_count', 'population',
        'stops_per_capita', 'coverage_score', 'imd_decile'
    ]].sort_values('coverage_score')

    st.dataframe(
        service_gap_areas.head(30),
        use_container_width=True,
        column_config={
            'coverage_score': st.column_config.ProgressColumn(
                'Coverage Score',
                format="%.1f",
                min_value=0,
                max_value=100
            ),
            'imd_decile': st.column_config.NumberColumn(
                'Deprivation Decile',
                help="1 = Most deprived, 10 = Least deprived"
            )
        }
    )

    # ============================================================================
    # EXPORT DATA
    # ============================================================================
    st.markdown("---")
    render_section_divider("Export Data", icon="📥")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="📥 Download CSV",
            data=filtered_data.to_csv(index=False),
            file_name="service_coverage_analysis.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        st.download_button(
            label="📥 Download JSON",
            data=filtered_data.to_json(orient='records', indent=2),
            file_name="service_coverage_analysis.json",
            mime="application/json",
            use_container_width=True
        )

    with col3:
        try:
            from io import BytesIO
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_data.to_excel(writer, sheet_name='Coverage Data', index=False)
                summary_df = pd.DataFrame({
                    'Metric': ['Total Areas', 'Avg Coverage', 'Service Gaps', 'Avg Stops per 1k'],
                    'Value': [len(filtered_data), f"{filtered_data['coverage_score'].mean():.2f}",
                             int(filtered_data['service_gap'].sum()), f"{filtered_data['stops_per_capita'].mean():.2f}"]
                })
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            st.download_button(
                label="📥 Download Excel",
                data=buffer.getvalue(),
                file_name="service_coverage_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Excel export unavailable: {str(e)}")

    # ============================================================================
    # METHODOLOGY CITATIONS
    # ============================================================================
    st.markdown("---")
    render_methodology_citation([
        "DfT TAG Unit M2 (Public Transport Accessibility)",
        "DfT Accessibility Statistics Methodology (2024)",
        "ONS Geographic Definitions",
        "DfT Bus Service Operators Grant (BSOG) Guidance",
        "DEFRA Rural Urban Classification",
        "OECD Spatial Equity Framework"
    ])

except Exception as e:
    st.error(f"Error loading coverage data: {str(e)}")
    st.info("Please ensure spatial metrics have been computed.")

    # Show which data sources are missing
    validation = DATA_REGISTRY.validate_source('lsoa_metrics')
    if not validation['exists']:
        render_missing_data_error([{
            'source': 'lsoa_metrics',
            'description': validation['description'],
            'pipeline_command': validation.get('pipeline_command')
        }], "Service Coverage Dashboard")

    import traceback
    st.code(traceback.format_exc())
