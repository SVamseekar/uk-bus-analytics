"""
Quick test of UI components
"""
import streamlit as st
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.ui_components import (
    apply_professional_config,
    render_dashboard_header,
    render_kpi_card,
    create_responsive_columns
)

st.set_page_config(page_title="UI Test", layout="wide")

apply_professional_config()

render_dashboard_header(
    title="UI Component Test",
    subtitle="Testing the professional design system",
    icon="🧪"
)

st.markdown("## KPI Cards Test")

col1, col2, col3, col4 = create_responsive_columns(4)

with col1:
    render_kpi_card(
        label="Test Metric 1",
        value="1,234",
        unit="units",
        trend="+5.2%",
        trend_type="positive",
        icon="📊"
    )

with col2:
    render_kpi_card(
        label="Test Metric 2",
        value="567",
        unit="items",
        trend="-2.1%",
        trend_type="negative",
        icon="📉"
    )

with col3:
    render_kpi_card(
        label="Test Metric 3",
        value="89.5",
        unit="/100",
        trend="No change",
        trend_type="neutral",
        icon="➡️"
    )

with col4:
    render_kpi_card(
        label="Test Metric 4",
        value="£42M",
        unit="annual",
        trend="⚠️ Review needed",
        trend_type="warning",
        icon="💰"
    )

st.success("✅ If you can see the KPI cards above with professional styling, the UI system is working!")
