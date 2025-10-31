"""
Script to apply professional design system to all dashboard pages
"""

import re
from pathlib import Path

# Dashboard pages to update
PAGES = {
    "02_⚖️_Equity_Intelligence.py": {
        "title": "Equity Intelligence",
        "subtitle": "Measure transport equity and identify communities requiring intervention with IMD overlay",
        "icon": "⚖️",
        "methodology": ["OECD Spatial Equity Frameworks", "Social Value UK Guidelines", "DfT TAG Unit A4.1"]
    },
    "03_💰_Investment_Appraisal.py": {
        "title": "Investment Appraisal",
        "subtitle": "Calculate Benefit-Cost Ratios and economic impact following HM Treasury Green Book methodology",
        "icon": "💰",
        "methodology": ["HM Treasury Green Book (2022)", "DfT TAG Unit A1.1", "BEIS Carbon Valuation"]
    },
    "04_🎯_Policy_Scenarios.py": {
        "title": "Policy Scenarios",
        "subtitle": "Simulate policy interventions and forecast impacts with dynamic recalculation",
        "icon": "🎯",
        "methodology": ["DfT Transport Appraisal Guidance", "HM Treasury Green Book", "BEIS Emission Factors"]
    },
    "05_🔀_Network_Optimization.py": {
        "title": "Network Optimization",
        "subtitle": "Optimize route structures and identify clustering opportunities for efficiency gains",
        "icon": "🔀",
        "methodology": ["DfT BSOG Efficiency Standards", "Network Optimization Theory"]
    },
    "06_💬_Policy_Assistant.py": {
        "title": "Policy Assistant",
        "subtitle": "AI-powered conversational interface for policy exploration and insights",
        "icon": "💬",
        "methodology": ["Semantic Search", "RAG Pipeline", "LangChain Framework"]
    }
}

def update_page_header(page_path: Path, config: dict):
    """Update a dashboard page with professional design"""

    content = page_path.read_text()

    # Find and replace imports
    old_imports_pattern = r"import streamlit as st.*?from dashboard\.utils\.data_loader import[^\n]+"

    new_imports = """import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.data_loader import load_lsoa_metrics, get_summary_statistics
from dashboard.utils.ui_components import (
    apply_professional_config,
    render_dashboard_header,
    render_kpi_card,
    render_section_divider,
    render_chart_card,
    apply_plotly_theme,
    create_responsive_columns,
    render_methodology_citation
)"""

    # Replace page config
    old_page_config = r"st\.set_page_config\([^)]+\)"
    new_page_config = f'''st.set_page_config(
    page_title="{config['title']}",
    page_icon="{config['icon']}",
    layout="wide",
    initial_sidebar_state="collapsed"
)'''

    # Replace header
    old_header_pattern = r"st\.title\([^)]+\)\s*st\.markdown\([^)]+\)\s*st\.markdown\([^)]+\)"
    new_header = f'''apply_professional_config()

render_dashboard_header(
    title="{config['title']}",
    subtitle="{config['subtitle']}",
    icon="{config['icon']}"
)'''

    # Apply replacements
    content = re.sub(old_page_config, new_page_config, content, flags=re.DOTALL)
    content = re.sub(old_header_pattern, new_header, content, flags=re.DOTALL)

    # Add methodology citations before the final except block
    methodology_code = f'''
    # Methodology Citations
    st.markdown("---")
    render_methodology_citation({config['methodology']})

except Exception as e:'''

    content = content.replace('\nexcept Exception as e:', methodology_code)

    # Write back
    page_path.write_text(content)
    print(f"✅ Updated {page_path.name}")

def main():
    dashboard_dir = Path("/Users/souravamseekarmarti/Projects/uk_bus_analytics/dashboard/pages")

    for page_name, config in PAGES.items():
        page_path = dashboard_dir / page_name
        if page_path.exists():
            try:
                update_page_header(page_path, config)
            except Exception as e:
                print(f"❌ Error updating {page_name}: {e}")
        else:
            print(f"⚠️  Page not found: {page_name}")

    print("\n✨ Dashboard design update complete!")

if __name__ == "__main__":
    main()
