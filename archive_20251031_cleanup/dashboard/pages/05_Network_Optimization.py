"""
UK Bus Transport Intelligence Platform - Network Optimization
============================================================
Route clustering analysis and consolidation recommendations

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import numpy as np

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.ml_loader import load_route_clustering_model
from dashboard.utils.ui_components import (
    apply_professional_config,
    load_professional_css,
    render_navigation_bar,
    render_dashboard_header,
    render_section_divider
)

# Page configuration
st.set_page_config(
    page_title="Network Optimization",
    page_icon="🔀",
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
    title="Network Optimization",
    subtitle="Identify route consolidation opportunities using ML-powered clustering analysis",
    icon="🔀"
)

# Legacy CSS kept for backwards compatibility
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .insight-box {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">🔀 Network Optimization Intelligence</div>', unsafe_allow_html=True)
st.markdown("**AI-powered route clustering and consolidation recommendations**")

# Load model
@st.cache_resource
def load_clustering_data():
    """Load route clustering model and data"""
    try:
        model_data = load_route_clustering_model()

        # Extract components
        routes_metadata = model_data['routes_metadata']
        cluster_labels = model_data['cluster_labels']

        # Create routes dataframe
        routes_df = pd.DataFrame(routes_metadata)
        routes_df['cluster'] = cluster_labels

        return routes_df, model_data
    except Exception as e:
        st.error(f"Error loading clustering data: {e}")
        return None, None

# Load data
routes_df, model_data = load_clustering_data()

if routes_df is not None:

    # Overview metrics
    st.markdown("### 📊 Network Overview")

    col1, col2, col3, col4 = st.columns(4)

    num_clusters = routes_df['cluster'].nunique()
    num_routes = len(routes_df)
    noise_routes = len(routes_df[routes_df['cluster'] == -1])
    avg_cluster_size = routes_df[routes_df['cluster'] != -1].groupby('cluster').size().mean()

    with col1:
        st.metric(
            "Total Routes",
            f"{num_routes:,}",
            help="Total number of bus routes analyzed"
        )

    with col2:
        st.metric(
            "Route Clusters",
            f"{num_clusters - 1}",  # Exclude noise cluster (-1)
            help="Number of similar route groups identified by ML"
        )

    with col3:
        st.metric(
            "Avg Cluster Size",
            f"{avg_cluster_size:.1f}",
            help="Average number of routes per cluster"
        )

    with col4:
        st.metric(
            "Unclustered Routes",
            f"{noise_routes}",
            help="Routes that don't fit any cluster (noise)",
            delta=f"{(noise_routes/num_routes*100):.1f}%"
        )

    st.markdown("---")

    # Filters in main area
    render_section_divider("Filters & Controls", icon="🎛️")

    col1, col2 = st.columns(2)

    with col1:
        # Cluster filter
        valid_clusters = sorted([c for c in routes_df['cluster'].unique() if c != -1])
        selected_clusters = st.multiselect(
            "Select Clusters",
            options=valid_clusters,
            default=valid_clusters[:5] if len(valid_clusters) >= 5 else valid_clusters,
            help="Select clusters to analyze"
        )

    with col2:
        # Show noise routes
        show_noise = st.checkbox("Include Unclustered Routes", value=False)

    st.markdown("---")

    # Filter data
    if selected_clusters:
        if show_noise:
            filtered_df = routes_df[routes_df['cluster'].isin(selected_clusters + [-1])]
        else:
            filtered_df = routes_df[routes_df['cluster'].isin(selected_clusters)]
    else:
        filtered_df = routes_df

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Cluster Distribution",
        "🗺️ Regional Analysis",
        "🔍 Cluster Details",
        "💡 Recommendations"
    ])

    with tab1:
        st.markdown("### Route Cluster Distribution")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Cluster size distribution
            cluster_sizes = routes_df[routes_df['cluster'] != -1].groupby('cluster').size().reset_index(name='count')
            cluster_sizes = cluster_sizes.sort_values('count', ascending=False)

            fig = px.bar(
                cluster_sizes.head(20),
                x='cluster',
                y='count',
                title="Top 20 Largest Route Clusters",
                labels={'cluster': 'Cluster ID', 'count': 'Number of Routes'},
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title="Cluster ID",
                yaxis_title="Number of Routes",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Cluster size statistics
            st.markdown("**Cluster Size Statistics**")

            stats_df = pd.DataFrame({
                'Metric': ['Total Clusters', 'Max Size', 'Min Size', 'Median Size', 'Mean Size'],
                'Value': [
                    num_clusters - 1,
                    int(cluster_sizes['count'].max()),
                    int(cluster_sizes['count'].min()),
                    int(cluster_sizes['count'].median()),
                    f"{cluster_sizes['count'].mean():.1f}"
                ]
            })
            st.dataframe(stats_df, hide_index=True, use_container_width=True)

            # Optimization potential
            large_clusters = len(cluster_sizes[cluster_sizes['count'] >= 10])
            st.markdown(f"""
            <div class="insight-box">
                <strong>Optimization Potential</strong><br>
                {large_clusters} clusters have 10+ routes<br>
                <small>These represent consolidation opportunities</small>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Regional Distribution of Clusters")

        if 'region' in routes_df.columns:
            col1, col2 = st.columns(2)

            with col1:
                # Routes by region
                region_counts = routes_df.groupby('region').size().reset_index(name='count')
                region_counts = region_counts.sort_values('count', ascending=True)

                fig = px.bar(
                    region_counts,
                    y='region',
                    x='count',
                    orientation='h',
                    title="Routes by Region",
                    labels={'region': 'Region', 'count': 'Number of Routes'},
                    color='count',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Clusters by region
                region_clusters = routes_df[routes_df['cluster'] != -1].groupby('region')['cluster'].nunique().reset_index(name='cluster_count')
                region_clusters = region_clusters.sort_values('cluster_count', ascending=True)

                fig = px.bar(
                    region_clusters,
                    y='region',
                    x='cluster_count',
                    orientation='h',
                    title="Unique Clusters by Region",
                    labels={'region': 'Region', 'cluster_count': 'Number of Clusters'},
                    color='cluster_count',
                    color_continuous_scale='Oranges'
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Regional information not available in the dataset")

    with tab3:
        st.markdown("### Detailed Cluster Analysis")

        # Select cluster to explore
        cluster_to_explore = st.selectbox(
            "Select a cluster to explore",
            options=sorted([c for c in routes_df['cluster'].unique() if c != -1]),
            format_func=lambda x: f"Cluster {x}"
        )

        if cluster_to_explore is not None:
            cluster_routes = routes_df[routes_df['cluster'] == cluster_to_explore]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Routes in Cluster", len(cluster_routes))

            with col2:
                if 'region' in cluster_routes.columns:
                    regions = cluster_routes['region'].nunique()
                    st.metric("Regions Covered", regions)

            with col3:
                if 'operator' in cluster_routes.columns:
                    operators = cluster_routes['operator'].nunique()
                    st.metric("Unique Operators", operators)

            # Show route details
            st.markdown(f"#### Routes in Cluster {cluster_to_explore}")

            # Select columns to display
            display_cols = ['route_name', 'route_description']
            if 'region' in cluster_routes.columns:
                display_cols.append('region')
            if 'operator' in cluster_routes.columns:
                display_cols.append('operator')

            available_cols = [col for col in display_cols if col in cluster_routes.columns]

            st.dataframe(
                cluster_routes[available_cols].head(20),
                hide_index=True,
                use_container_width=True
            )

            if len(cluster_routes) > 20:
                st.info(f"Showing 20 of {len(cluster_routes)} routes. Download full data for complete list.")

            # Download button
            csv = cluster_routes.to_csv(index=False)
            st.download_button(
                label=f"📥 Download Cluster {cluster_to_explore} Data",
                data=csv,
                file_name=f"cluster_{cluster_to_explore}_routes.csv",
                mime="text/csv"
            )

    with tab4:
        st.markdown("### 💡 Consolidation Recommendations")

        # Identify clusters with consolidation potential
        large_clusters = routes_df[routes_df['cluster'] != -1].groupby('cluster').size()
        consolidation_candidates = large_clusters[large_clusters >= 10].sort_values(ascending=False)

        if len(consolidation_candidates) > 0:
            st.markdown(f"""
            <div class="insight-box">
                <strong>Key Findings</strong><br>
                • Identified <strong>{len(consolidation_candidates)}</strong> clusters with 10+ similar routes<br>
                • Combined, these clusters contain <strong>{consolidation_candidates.sum()}</strong> routes<br>
                • Average overlap: <strong>{consolidation_candidates.mean():.1f}</strong> routes per cluster<br>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Top Consolidation Opportunities")

            # Create recommendations dataframe
            recommendations = []
            for cluster_id, count in consolidation_candidates.head(10).items():
                cluster_routes = routes_df[routes_df['cluster'] == cluster_id]

                # Calculate potential savings
                potential_savings_pct = ((count - 1) / count) * 100

                recommendation = {
                    'Cluster ID': int(cluster_id),
                    'Routes': int(count),
                    'Potential Consolidation': f"{count} → {max(1, count // 2)}",
                    'Est. Cost Reduction': f"{potential_savings_pct * 0.3:.1f}%",
                    'Priority': '🔴 High' if count >= 20 else '🟡 Medium'
                }

                if 'region' in cluster_routes.columns:
                    recommendation['Primary Region'] = cluster_routes['region'].mode()[0] if len(cluster_routes['region'].mode()) > 0 else 'Multiple'

                recommendations.append(recommendation)

            recommendations_df = pd.DataFrame(recommendations)
            st.dataframe(recommendations_df, hide_index=True, use_container_width=True)

            # Strategic recommendations
            st.markdown("#### Strategic Recommendations")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                **Phase 1: Quick Wins (0-6 months)**
                1. Consolidate clusters with 20+ routes
                2. Focus on single-operator clusters first
                3. Pilot in low-risk regions
                4. Target 15-20% cost reduction
                """)

            with col2:
                st.markdown("""
                **Phase 2: Network Redesign (6-18 months)**
                1. Address multi-operator overlaps
                2. Integrate with demand data
                3. Implement dynamic routing
                4. Achieve 30%+ efficiency gains
                """)

            # Warning box
            st.markdown("""
            <div class="warning-box">
                ⚠️ <strong>Implementation Considerations</strong><br>
                • Consult with operators before consolidation<br>
                • Assess impact on service coverage and equity<br>
                • Consider peak vs off-peak demand patterns<br>
                • Maintain minimum service levels for accessibility
            </div>
            """, unsafe_allow_html=True)

        else:
            st.info("No large clusters detected. The network appears well-optimized.")

    # Export full data
    st.markdown("---")
    st.markdown("### 📥 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        csv = routes_df.to_csv(index=False)
        st.download_button(
            label="Download All Routes Data",
            data=csv,
            file_name="all_routes_clusters.csv",
            mime="text/csv"
        )

    with col2:
        if selected_clusters:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download Filtered Data",
                data=csv,
                file_name="filtered_routes_clusters.csv",
                mime="text/csv"
            )

else:
    st.error("Unable to load route clustering data. Please ensure the model file exists.")
    st.info("Expected location: `models/route_clustering.pkl`")
