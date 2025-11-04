"""
Reusable category page template for UK Bus Analytics Dashboard
Professional consulting report style - NOT academic questionnaire format

Design Philosophy:
- Consulting firm aesthetic (McKinsey, Deloitte, PwC style)
- Executive summary approach
- Decision-maker focused
- Clean, spacious layouts
- NO academic labels ("Question A1", "Data Story", etc.)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Callable, Any

# Regional mapping
REGIONS = [
    'Yorkshire and Humber',
    'West Midlands',
    'East Midlands',
    'North East England',
    'South West England',
    'Greater London',
    'South East England',
    'North West England',
    'East of England'
]

def render_category_page(category_config: Dict[str, Any]) -> None:
    """
    Render professional consulting-style category page

    Args:
        category_config: Dict with structure:
        {
            'id': 'coverage',
            'title': 'Coverage & Accessibility',
            'icon': '🟢',
            'description': 'Understanding how well bus networks...',
            'sections': [
                {
                    'id': 'A1',  # Internal use only
                    'title': 'Regional Route Density Analysis',  # User-facing
                    'data_function': load_route_density_data,
                    'viz_function': create_route_density_viz,
                    'narrative_function': generate_route_density_narrative
                },
                ...
            ]
        }
    """

    # Page configuration
    st.set_page_config(
        page_title=category_config['title'],
        page_icon=category_config['icon'],
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Header - Clean and professional
    st.title(f"{category_config['icon']} {category_config['title']}")
    st.markdown(category_config['description'])

    # Metadata (subtle, not prominent)
    if 'metadata' in category_config:
        st.caption(category_config['metadata'])

    st.markdown("---")

    # Filters - Clean, minimal labels
    col1, col2, col3 = st.columns([3, 3, 2])

    with col1:
        selected_region = st.selectbox(
            "Region",
            ['All Regions'] + REGIONS,
            key=f"{category_config['id']}_region"
        )

    with col2:
        urban_rural = st.selectbox(
            "Area Type",
            ['All', 'Urban', 'Rural'],
            key=f"{category_config['id']}_urban"
        )

    with col3:
        if st.button("📥 Export Report", key=f"{category_config['id']}_export_btn"):
            st.info("Export functionality coming soon")

    st.markdown("---")

    # Render each analysis section
    for i, section in enumerate(category_config['sections']):
        render_analysis_section(
            section=section,
            region_filter=selected_region,
            urban_rural_filter=urban_rural,
            section_index=i
        )

        # Separator between sections (except last)
        if i < len(category_config['sections']) - 1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<br>", unsafe_allow_html=True)

    # Footer - Subtle call to action
    st.markdown("---")
    st.info("💬 Need deeper analysis? Our AI assistant can help explore these findings further.")


def render_analysis_section(
    section: Dict[str, Any],
    region_filter: str,
    urban_rural_filter: str,
    section_index: int
) -> None:
    """
    Render individual analysis section in consulting report style

    NO labels like "Data Story", "Key Insight" - just clean professional layout
    """

    # Section title - professional, descriptive
    st.markdown(f"## {section['title']}")
    st.markdown("")  # Spacing

    try:
        # Load data
        data = section['data_function'](region_filter, urban_rural_filter)

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            st.warning(f"No data available for this analysis with current filters")
            return

        # Create visualization
        viz = section['viz_function'](data)

        # Generate narrative content
        narrative = section['narrative_function'](data)

        # Layout: Visualization on left (60%), Narrative on right (40%)
        col_viz, col_narrative = st.columns([3, 2])

        with col_viz:
            # NO label like "📊 Visualization" - chart speaks for itself
            if viz is not None:
                st.plotly_chart(viz, use_container_width=True, key=f"viz_{section['id']}_{section_index}")
            else:
                st.info("Visualization not available")

        with col_narrative:
            # Executive summary - first paragraph(s)
            if narrative and 'summary' in narrative:
                st.markdown(narrative['summary'])
                st.markdown("")  # Spacing

            # Key Finding - highlighted box
            if narrative and 'key_finding' in narrative:
                st.markdown("**Key Finding**")
                st.info(narrative['key_finding'])
                st.markdown("")  # Spacing

            # Policy Recommendation - success box (green)
            if narrative and 'recommendation' in narrative:
                st.markdown("**Policy Recommendation**")
                st.success(narrative['recommendation'])
                st.markdown("")  # Spacing

            # Investment details (if applicable)
            if narrative and 'investment' in narrative:
                st.markdown("**Investment Requirement**")
                st.markdown(narrative['investment'])
                st.markdown("")  # Spacing

            # Related analysis links
            if narrative and 'related_links' in narrative and narrative['related_links']:
                st.markdown("**Related Analysis**")
                for link in narrative['related_links']:
                    st.markdown(f"→ [{link['text']}]({link['url']})")

    except Exception as e:
        st.error(f"Error loading analysis: {str(e)}")
        with st.expander("Technical Details"):
            st.exception(e)


# Helper functions for professional styling

def create_metric_cards(metrics: List[Dict[str, Any]]) -> None:
    """
    Display key metrics in clean card format

    Args:
        metrics: List of dicts with 'label', 'value', 'delta' (optional)
    """
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.metric(
                label=metric['label'],
                value=metric['value'],
                delta=metric.get('delta')
            )


def format_large_number(num: float) -> str:
    """Format large numbers with M/k suffixes"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}k"
    else:
        return f"{num:.0f}"


def calculate_percentage_change(current: float, baseline: float) -> str:
    """Calculate percentage change with +/- sign"""
    if baseline == 0:
        return "N/A"
    change = ((current - baseline) / baseline) * 100
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.1f}%"


def create_professional_table(
    data: pd.DataFrame,
    columns: List[str],
    height: int = 400
) -> None:
    """
    Display data in clean, professional table format

    Args:
        data: DataFrame to display
        columns: Columns to show
        height: Table height in pixels
    """
    st.dataframe(
        data[columns],
        use_container_width=True,
        hide_index=True,
        height=height
    )


def add_section_divider() -> None:
    """Add professional section divider with spacing"""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)


# Custom CSS for professional styling
def apply_professional_styling():
    """Apply custom CSS for consulting report aesthetic"""
    st.markdown("""
        <style>
        /* Clean, professional font */
        .stMarkdown {
            font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
        }

        /* Section titles - professional weight */
        h2 {
            font-weight: 600;
            color: #1f2937;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        /* Remove excessive padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Professional info boxes */
        .stAlert {
            border-radius: 0.5rem;
            border-left: 4px solid;
        }

        /* Clean metric cards */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 600;
        }

        /* Professional table styling */
        .stDataFrame {
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
