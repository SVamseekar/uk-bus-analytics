"""
UK Bus Transport Intelligence Platform
UI Components & Utilities
Professional OECD-style Design System

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

import streamlit as st
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Literal


# ============================================================================
# CSS & THEME MANAGEMENT
# ============================================================================

def load_professional_css():
    """Load professional CSS design system based on OECD/World Bank standards"""
    css = """
    <style>
    /* =====================================================
       PROFESSIONAL DESIGN SYSTEM - TIER 1 CONSULTING STYLE
       ===================================================== */

    /* Color Variables */
    :root {
        --color-primary-1: #1E3A5F;
        --color-primary-2: #2E7D9A;
        --color-primary-3: #4CAF90;
        --color-success: #10B981;
        --color-warning: #F59E0B;
        --color-danger: #EF4444;
        --color-info: #3B82F6;
        --color-background: #FFFFFF;
        --color-surface: #F9FAFB;
        --color-border: #E5E7EB;
        --color-text-primary: #111827;
        --color-text-secondary: #6B7280;
    }

    /* Force light theme - override any dark mode */
    .stApp {
        background-color: #FFFFFF !important;
    }

    .main .block-container {
        background-color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] {
        background-color: #F9FAFB !important;
    }

    /* Ensure all text is visible */
    .stMarkdown, .stText, p, span, div {
        color: #111827 !important;
    }

    /* Fix plotly charts */
    .js-plotly-plot .plotly {
        background-color: #FFFFFF !important;
    }

    /* Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--color-text-primary);
    }

    /* Navigation Bar */
    .nav-bar {
        background: var(--color-primary-1);
        padding: 16px 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 32px;
    }

    .nav-bar__logo {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .nav-bar__tabs {
        display: flex;
        gap: 4px;
    }

    .nav-tab {
        color: white;
        padding: 12px 24px;
        text-decoration: none;
        border-radius: 6px;
        transition: background-color 0.2s;
        font-size: 15px;
        font-weight: 500;
        cursor: pointer;
    }

    .nav-tab:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    .nav-tab--active {
        background: var(--color-primary-2);
    }

    /* Dashboard Header */
    .dashboard-header {
        margin-bottom: 32px;
        padding: 32px;
        background: linear-gradient(135deg, var(--color-primary-1) 0%, var(--color-primary-2) 100%);
        border-radius: 12px;
        color: white;
    }

    .dashboard-header__title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .dashboard-header__subtitle {
        font-size: 1.125rem;
        opacity: 0.9;
        font-weight: 400;
    }

    /* Section Divider */
    .dashboard-section {
        margin: 40px 0 24px 0;
    }

    .dashboard-section__title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--color-text-primary);
        border-bottom: 3px solid var(--color-primary-2);
        padding-bottom: 8px;
        display: inline-block;
    }

    /* KPI Card */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
        border: 1px solid var(--color-border);
        height: 100%;
    }

    .kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }

    .kpi-card__label {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        font-weight: 600;
    }

    .kpi-card__value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--color-text-primary);
        line-height: 1.2;
        margin-bottom: 4px;
    }

    .kpi-card__unit {
        font-size: 0.875rem;
        color: var(--color-text-secondary);
        margin-bottom: 8px;
    }

    .kpi-card__trend {
        font-size: 0.875rem;
        font-weight: 500;
        margin-top: 8px;
    }

    .kpi-card__trend--positive { color: var(--color-success); }
    .kpi-card__trend--negative { color: var(--color-danger); }
    .kpi-card__trend--warning { color: var(--color-warning); }
    .kpi-card__trend--neutral { color: var(--color-text-secondary); }

    /* Chart Card */
    .chart-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--color-border);
        margin-bottom: 24px;
    }

    .chart-card__header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--color-border);
    }

    .chart-card__title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text-primary);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .chart-card__actions {
        display: flex;
        gap: 8px;
    }

    .chart-card__action-btn {
        background: transparent;
        border: 1px solid var(--color-border);
        border-radius: 6px;
        padding: 6px 12px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.875rem;
        color: var(--color-text-secondary);
    }

    .chart-card__action-btn:hover {
        background: var(--color-surface);
        border-color: var(--color-primary-2);
        color: var(--color-primary-2);
    }

    /* Insight Card */
    .insight-card {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        border-left: 4px solid var(--color-primary-2);
        border-radius: 8px;
        padding: 20px 24px;
        margin: 16px 0;
    }

    .insight-card__title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--color-primary-1);
        margin-bottom: 12px;
    }

    .insight-card__content {
        font-size: 0.9375rem;
        line-height: 1.6;
        color: var(--color-text-primary);
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .badge--success {
        background: #D1FAE5;
        color: #065F46;
    }

    .badge--warning {
        background: #FEF3C7;
        color: #92400E;
    }

    .badge--danger {
        background: #FEE2E2;
        color: #991B1B;
    }

    .badge--info {
        background: #DBEAFE;
        color: #1E40AF;
    }

    /* Remove Streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1920px;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .dashboard-header__title {
            font-size: 1.75rem;
        }

        .kpi-card__value {
            font-size: 2rem;
        }

        .nav-bar {
            flex-direction: column;
            gap: 16px;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def load_css():
    """Load custom CSS styling for OECD-style professional UI"""
    # Legacy function - kept for backwards compatibility
    load_professional_css()


def hide_streamlit_ui():
    """Hide default Streamlit UI elements for professional appearance"""
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


def apply_professional_config():
    """Apply professional page configuration"""
    load_css()
    hide_streamlit_ui()


def render_navigation_bar():
    """
    Render horizontal navigation bar with module tabs
    """
    nav_html = """
    <div class="nav-bar">
        <div class="nav-bar__logo">
            🚌 UK Bus Intelligence Platform
        </div>
        <div class="nav-bar__tabs">
            <a href="/" target="_self" class="nav-tab">Home</a>
            <a href="/Service_Coverage" target="_self" class="nav-tab">Coverage</a>
            <a href="/Equity_Intelligence" target="_self" class="nav-tab">Equity</a>
            <a href="/Investment_Appraisal" target="_self" class="nav-tab">Investment</a>
            <a href="/Policy_Scenarios" target="_self" class="nav-tab">Scenarios</a>
            <a href="/Network_Optimization" target="_self" class="nav-tab">Network</a>
            <a href="/Policy_Assistant" target="_self" class="nav-tab">Assistant</a>
        </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)


# ============================================================================
# KPI CARD COMPONENT
# ============================================================================

def render_kpi_card(
    label: str,
    value: str,
    unit: str = "",
    trend: Optional[str] = None,
    trend_type: Literal["positive", "negative", "warning", "neutral"] = "neutral",
    help_text: Optional[str] = None,
    icon: str = "📊"
):
    """
    Render a professional KPI card with trend indicators

    Args:
        label: KPI label (e.g., "Average Coverage")
        value: Main value to display (e.g., "6.2")
        unit: Unit text (e.g., "stops/1000 population")
        trend: Trend text (e.g., "+3.1% vs 2023")
        trend_type: Type of trend for color coding
        help_text: Optional tooltip text
        icon: Emoji icon for the card
    """

    # Trend indicators
    trend_icons = {
        "positive": "↑",
        "negative": "↓",
        "warning": "⚠️",
        "neutral": "→"
    }

    trend_colors = {
        "positive": "#10B981",
        "negative": "#EF4444",
        "warning": "#F59E0B",
        "neutral": "#6B7280"
    }

    # Build card HTML
    trend_html = ""
    if trend:
        trend_icon = trend_icons.get(trend_type, "")
        trend_color = trend_colors.get(trend_type, "#6B7280")
        trend_html = f"""
        <div class="kpi-card__trend kpi-card__trend--{trend_type}" style="color: {trend_color};">
            {trend_icon} {trend}
        </div>
        """

    # Build help text
    help_html = f' title="{help_text}"' if help_text else ''

    card_html = f"""
    <div class="kpi-card"{help_html}>
        <div class="kpi-card__label">{icon} {label}</div>
        <div class="kpi-card__value">{value}</div>
        {f'<div class="kpi-card__unit">{unit}</div>' if unit else ''}
        {trend_html if trend else ''}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


# ============================================================================
# CHART CARD WRAPPER
# ============================================================================

def render_chart_card(
    title: str,
    chart_function,
    icon: str = "📈",
    show_download: bool = True,
    show_settings: bool = False
):
    """
    Render a chart inside a professional card container with header and actions

    Args:
        title: Chart title
        chart_function: Function that renders the chart (plotly, matplotlib, etc.)
        icon: Emoji icon for the card
        show_download: Show download button
        show_settings: Show settings button
    """

    # Card header HTML
    actions_html = ""
    if show_settings:
        actions_html += '<button class="chart-card__action-btn">⚙️ Settings</button>'
    if show_download:
        actions_html += '<button class="chart-card__action-btn">📥 Download</button>'

    header_html = f"""
    <div class="chart-card__header">
        <div class="chart-card__title">
            <span class="chart-card__title-icon">{icon}</span>
            {title}
        </div>
        <div class="chart-card__actions">
            {actions_html}
        </div>
    </div>
    """

    with st.container():
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(header_html, unsafe_allow_html=True)
        st.markdown('<div class="chart-card__content">', unsafe_allow_html=True)

        # Render the actual chart
        chart_function()

        st.markdown('</div></div>', unsafe_allow_html=True)


# ============================================================================
# PLOTLY THEME
# ============================================================================

def get_plotly_theme() -> dict:
    """
    Get professional Plotly theme matching OECD design system

    Returns:
        dict: Plotly layout configuration
    """
    return {
        'font': {
            'family': 'Inter, Open Sans, sans-serif',
            'size': 14,
            'color': '#111827'
        },
        'plot_bgcolor': '#FFFFFF',
        'paper_bgcolor': '#FFFFFF',
        'colorway': [
            '#1E3A5F',  # Navy blue
            '#2E7D9A',  # Teal
            '#4CAF90',  # Mint green
            '#F59E0B',  # Amber
            '#EF4444',  # Red
            '#3B82F6',  # Blue
            '#8B5CF6',  # Purple
            '#EC4899'   # Pink
        ],
        'xaxis': {
            'showgrid': True,
            'gridcolor': '#E5E7EB',
            'gridwidth': 1,
            'zeroline': False,
            'showline': True,
            'linecolor': '#E5E7EB',
            'linewidth': 1,
            'title': {
                'font': {'size': 14, 'color': '#6B7280'}
            },
            'tickfont': {'size': 12, 'color': '#6B7280'}
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': '#E5E7EB',
            'gridwidth': 1,
            'zeroline': False,
            'showline': False,
            'title': {
                'font': {'size': 14, 'color': '#6B7280'}
            },
            'tickfont': {'size': 12, 'color': '#6B7280'}
        },
        'title': {
            'font': {'size': 20, 'color': '#111827', 'family': 'Inter, sans-serif'},
            'x': 0,
            'xanchor': 'left'
        },
        'legend': {
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': '#E5E7EB',
            'borderwidth': 1,
            'font': {'size': 12, 'color': '#6B7280'}
        },
        'hoverlabel': {
            'bgcolor': 'white',
            'bordercolor': '#E5E7EB',
            'font': {'size': 12, 'family': 'Inter, sans-serif', 'color': '#111827'}
        },
        'margin': {'t': 60, 'r': 40, 'b': 60, 'l': 60}
    }


def apply_plotly_theme(fig):
    """
    Apply professional theme to a Plotly figure

    Args:
        fig: Plotly figure object

    Returns:
        Modified figure with professional styling
    """
    theme = get_plotly_theme()
    fig.update_layout(**theme)
    return fig


# ============================================================================
# DASHBOARD HEADER
# ============================================================================

def render_dashboard_header(title: str, subtitle: str, icon: str = "📊"):
    """
    Render professional dashboard header with title and subtitle

    Args:
        title: Dashboard title
        subtitle: Dashboard subtitle/description
        icon: Emoji icon
    """
    header_html = f"""
    <div class="dashboard-header">
        <div>
            <div class="dashboard-header__title">
                {icon} {title}
            </div>
            <div class="dashboard-header__subtitle">
                {subtitle}
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


# ============================================================================
# SECTION DIVIDER
# ============================================================================

def render_section_divider(title: str, icon: str = ""):
    """
    Render a section divider with title

    Args:
        title: Section title
        icon: Optional emoji icon
    """
    icon_html = f"{icon} " if icon else ""
    divider_html = f"""
    <div class="dashboard-section">
        <h2 class="dashboard-section__title">{icon_html}{title}</h2>
    </div>
    """
    st.markdown(divider_html, unsafe_allow_html=True)


# ============================================================================
# INSIGHT CARD
# ============================================================================

def render_insight_card(title: str, content: str, icon: str = "🤖"):
    """
    Render AI-generated insight card with gradient background

    Args:
        title: Insight title
        content: Insight content
        icon: Emoji icon
    """
    insight_html = f"""
    <div class="insight-card">
        <div class="insight-card__title">{icon} {title}</div>
        <div class="insight-card__content">{content}</div>
    </div>
    """
    st.markdown(insight_html, unsafe_allow_html=True)


# ============================================================================
# BADGE COMPONENT
# ============================================================================

def render_badge(
    text: str,
    badge_type: Literal["success", "warning", "danger", "info"] = "info"
):
    """
    Render a small badge/chip component

    Args:
        text: Badge text
        badge_type: Type for color coding
    """
    badge_html = f'<span class="badge badge--{badge_type}">{text}</span>'
    st.markdown(badge_html, unsafe_allow_html=True)


# ============================================================================
# COLOR SCALES FOR VISUALIZATIONS
# ============================================================================

COLOR_SCALES = {
    'coverage': 'RdYlGn',  # Red (low) to Green (high)
    'deprivation': 'OrRd',  # White to Dark Red
    'bcr': 'Blues',  # Light to Dark Blue
    'diverging': 'RdBu',  # Red-Blue diverging
    'sequential': 'Viridis'  # Perceptually uniform
}


def get_color_scale(metric_type: str) -> str:
    """
    Get appropriate color scale for a metric type

    Args:
        metric_type: Type of metric ('coverage', 'deprivation', 'bcr', etc.)

    Returns:
        Plotly color scale name
    """
    return COLOR_SCALES.get(metric_type, 'Viridis')


# ============================================================================
# RESPONSIVE COLUMN LAYOUT
# ============================================================================

def create_responsive_columns(num_cols: int = 4):
    """
    Create responsive column layout that adapts to screen size

    Args:
        num_cols: Number of columns for desktop view

    Returns:
        Streamlit columns object
    """
    # This creates columns that will stack on mobile
    return st.columns(num_cols, gap="large")


# ============================================================================
# METHODOLOGY CITATION
# ============================================================================

def render_methodology_citation(citations: list[str]):
    """
    Render methodology citations at bottom of visualizations

    Args:
        citations: List of citation strings (e.g., ["DfT TAG Unit A1.1", "HM Treasury Green Book"])
    """
    citations_text = " | ".join(citations)
    citation_html = f"""
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #E5E7EB; font-size: 12px; color: #6B7280;">
        <strong>Methodology:</strong> {citations_text}
    </div>
    """
    st.markdown(citation_html, unsafe_allow_html=True)


# ============================================================================
# EXPORT FUNCTIONALITY
# ============================================================================

def add_export_buttons(data, filename_prefix: str = "export"):
    """
    Add CSV and Excel export buttons for data

    Args:
        data: DataFrame to export
        filename_prefix: Prefix for download filename
    """
    col1, col2 = st.columns(2)

    with col1:
        csv = data.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{filename_prefix}.csv",
            mime="text/csv"
        )

    with col2:
        # Excel export would require openpyxl
        st.download_button(
            label="📥 Download Excel",
            data=data.to_csv(index=False),  # Placeholder
            file_name=f"{filename_prefix}.xlsx",
            mime="application/vnd.ms-excel",
            disabled=True,
            help="Excel export coming soon"
        )
