"""
Data Sources Registry
=====================
Central registry of all available data files and their purposes
Used by dashboard components to know what data to load and where to find it

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import json

BASE_DIR = Path(__file__).parent.parent.parent


class DataSourceRegistry:
    """Registry of all available data sources with validation"""

    def __init__(self):
        self.sources = {
            # LSOA-level spatial metrics (PRIMARY DATA SOURCE)
            'lsoa_metrics': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'spatial' / 'lsoa_metrics.csv',
                'description': 'LSOA-level coverage, equity, and service metrics',
                'columns': [
                    'lsoa_code', 'lsoa_name', 'locality', 'region',
                    'bus_stops_count', 'population', 'stops_per_capita',
                    'coverage_score', 'equity_index', 'service_gap',
                    'imd_decile', 'imd_score'
                ],
                'required_by': ['Service Coverage', 'Equity Intelligence', 'Investment Appraisal']
            },

            # Spatial answers (derived metrics)
            'spatial_answers': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'spatial' / 'spatial_answers.json',
                'description': 'Pre-computed answers to spatial analysis questions',
                'contains': ['metadata', 'coverage_analysis', 'equity_analysis', 'spatial_patterns'],
                'required_by': ['Home', 'Service Coverage', 'Equity Intelligence']
            },

            # Correlation analysis
            'correlation_metrics': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'correlation' / 'lsoa_metrics.csv',
                'description': 'LSOA metrics with correlation analysis',
                'required_by': ['Equity Intelligence', 'Investment Appraisal']
            },

            'correlation_analysis': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'correlation' / 'correlation_analysis_*.json',
                'description': 'Statistical correlation results (latest timestamped file)',
                'required_by': ['Equity Intelligence']
            },

            # Descriptive analytics
            'comprehensive_kpis': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'descriptive' / 'comprehensive_kpis.json',
                'description': 'National and regional KPI summaries',
                'required_by': ['Home', 'All dashboards']
            },

            'regional_summary': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'descriptive' / 'regional_summary.csv',
                'description': 'Regional-level summary statistics',
                'required_by': ['Service Coverage', 'Network Optimization']
            },

            'all_57_answers': {
                'path': BASE_DIR / 'analytics' / 'outputs' / 'descriptive' / 'all_57_answers.json',
                'description': 'Answers to all 57 policy questions',
                'required_by': ['All dashboards', 'Policy Assistant']
            },

            # Processed data from pipeline
            'stops_processed': {
                'path': BASE_DIR / 'data' / 'processed' / 'outputs' / 'stops_processed.csv',
                'description': 'All processed bus stops with coordinates',
                'required_by': ['Service Coverage', 'Network Optimization']
            },

            'routes_processed': {
                'path': BASE_DIR / 'data' / 'processed' / 'outputs' / 'routes_processed.csv',
                'description': 'All processed bus routes',
                'required_by': ['Network Optimization']
            },

            # Raw demographic data
            'lsoa_population': {
                'path': BASE_DIR / 'data' / 'raw' / 'demographics' / 'lsoa_population.csv',
                'description': 'LSOA population data from ONS',
                'required_by': ['Equity Intelligence']
            },

            'lsoa_boundaries': {
                'path': BASE_DIR / 'data' / 'raw' / 'boundaries' / 'lsoa_boundaries.csv',
                'description': 'LSOA boundary definitions',
                'required_by': ['Service Coverage maps']
            },

            # ML models
            'anomaly_detector': {
                'path': BASE_DIR / 'models' / 'anomaly_detector.pkl',
                'description': 'Trained isolation forest for anomaly detection',
                'required_by': ['Service Coverage', 'Equity Intelligence']
            },

            # Policy Q&A system
            'policy_qa_system': {
                'path': BASE_DIR / 'models' / 'policy_qa_system_advanced',
                'description': 'Trained semantic search model for policy questions',
                'required_by': ['Policy Assistant']
            }
        }

    def get_source_path(self, source_key: str) -> Optional[Path]:
        """Get path for a data source"""
        if source_key not in self.sources:
            return None

        path = self.sources[source_key]['path']

        # Handle wildcard paths (get latest file)
        if '*' in str(path):
            pattern = path.name
            parent = path.parent
            matching_files = sorted(parent.glob(pattern), reverse=True)
            if matching_files:
                return matching_files[0]
            return None

        return path

    def validate_source(self, source_key: str) -> Dict:
        """
        Validate that a data source exists and is accessible

        Returns:
            {
                'exists': bool,
                'path': Path,
                'error': Optional[str],
                'pipeline_command': Optional[str]  # Command to generate missing data
            }
        """
        if source_key not in self.sources:
            return {
                'exists': False,
                'path': None,
                'error': f'Unknown data source: {source_key}'
            }

        source_info = self.sources[source_key]
        path = self.get_source_path(source_key)

        if not path or not path.exists():
            # Provide helpful error with pipeline command
            pipeline_commands = {
                'lsoa_metrics': 'python analytics/spatial/01_compute_spatial_metrics_v2.py',
                'spatial_answers': 'python analytics/spatial/01_compute_spatial_metrics_v2.py',
                'correlation_metrics': 'python analytics/spatial/02_correlation_analysis.py',
                'correlation_analysis': 'python analytics/spatial/02_correlation_analysis.py',
                'comprehensive_kpis': 'python data_pipeline/04_descriptive_analytics.py',
                'regional_summary': 'python data_pipeline/04_descriptive_analytics.py',
                'all_57_answers': 'python scripts/answer_57_questions.py',
                'stops_processed': 'python data_pipeline/02_data_processing.py',
                'routes_processed': 'python data_pipeline/02_data_processing.py',
                'anomaly_detector': 'python scripts/train_anomaly_detector.py',
                'policy_qa_system': 'python scripts/build_advanced_knowledge_base.py'
            }

            return {
                'exists': False,
                'path': path,
                'error': f'Data file not found: {path}',
                'pipeline_command': pipeline_commands.get(source_key),
                'description': source_info['description']
            }

        return {
            'exists': True,
            'path': path,
            'error': None
        }

    def get_required_sources_for_page(self, page_name: str) -> List[str]:
        """Get list of required data sources for a dashboard page"""
        required = []
        for source_key, source_info in self.sources.items():
            if page_name in source_info.get('required_by', []):
                required.append(source_key)
        return required

    def validate_page_data(self, page_name: str) -> Dict:
        """
        Validate all required data sources for a page

        Returns:
            {
                'all_available': bool,
                'missing': List[Dict],  # List of missing sources with details
                'available': List[str]
            }
        """
        required = self.get_required_sources_for_page(page_name)
        missing = []
        available = []

        for source_key in required:
            validation = self.validate_source(source_key)
            if validation['exists']:
                available.append(source_key)
            else:
                missing.append({
                    'source': source_key,
                    **validation
                })

        return {
            'all_available': len(missing) == 0,
            'missing': missing,
            'available': available
        }


def render_missing_data_error(missing_sources: List[Dict], component_name: str):
    """
    Render a helpful error message when data is missing

    Args:
        missing_sources: List of missing source dicts from validate_page_data
        component_name: Name of the component (e.g., "Coverage Map", "Equity Analysis")
    """
    import streamlit as st

    st.error(f"❌ **{component_name}**: Required data not available")

    with st.expander("🔧 How to generate missing data"):
        for source in missing_sources:
            st.markdown(f"**Missing**: `{source['source']}`")
            st.caption(source['description'])

            if source.get('pipeline_command'):
                st.code(source['pipeline_command'], language='bash')

            st.markdown("---")

        st.info("""
        **Quick Fix**: Run the data pipeline to generate all required data:
        ```bash
        python data_pipeline/01_data_ingestion.py
        python data_pipeline/02_data_processing.py
        python data_pipeline/04_descriptive_analytics.py
        python analytics/spatial/01_compute_spatial_metrics_v2.py
        ```
        """)


# Global registry instance
DATA_REGISTRY = DataSourceRegistry()
