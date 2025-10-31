"""
Policy Questions Data Story Loader
Load and organize the 57 policy questions for integration into dashboard pages

Author: UK Bus Analytics Platform
Date: 2025-10-30
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent.parent


def load_all_questions() -> Dict:
    """Load all 57 policy questions from JSON"""
    json_path = BASE_DIR / "data" / "mapping" / "policy_questions_visual_framework.json"
    with open(json_path, 'r') as f:
        return json.load(f)


def get_questions_for_page(page_name: str) -> List[Dict]:
    """
    Get questions relevant to a specific dashboard page

    Args:
        page_name: One of 'coverage', 'equity', 'investment', 'scenarios', 'optimization'

    Returns:
        List of question dictionaries
    """
    data = load_all_questions()
    questions = data['questions']

    # Define keyword mappings for each page
    page_keywords = {
        'coverage': {
            'keywords': ['coverage', 'accessibility', 'connectivity', 'rural', 'geographic', 'network access'],
            'ids': ['Q01', 'Q07', 'Q14', 'Q25', 'Q33', 'Q34', 'Q35', 'Q40', 'Q46', 'Q48']
        },
        'equity': {
            'keywords': ['equity', 'deprived', 'deprivation', 'employment', 'demographic', 'elderly', 'disability', 'youth', 'inclusion', 'educational', 'social'],
            'ids': ['Q02', 'Q04', 'Q08', 'Q11', 'Q13', 'Q19', 'Q20', 'Q22', 'Q41', 'Q42', 'Q55', 'Q56']
        },
        'investment': {
            'keywords': ['investment', 'benefit-cost', 'BCR', 'economic impact', 'property value', 'funding', 'procurement', 'value for money'],
            'ids': ['Q10', 'Q15', 'Q18', 'Q24', 'Q50', 'Q51', 'Q57']
        },
        'scenarios': {
            'keywords': ['fare', 'policy', 'pricing', 'park-and-ride', 'devolution', 'low emission', 'carbon', 'behavioral', 'campaign'],
            'ids': ['Q05', 'Q16', 'Q26', 'Q29', 'Q31', 'Q39', 'Q43', 'Q44', 'Q49']
        },
        'optimization': {
            'keywords': ['operational cost', 'efficiency', 'frequency', 'demand patterns', 'reliability', 'commercial viability', 'punctuality', 'performance', 'route'],
            'ids': ['Q03', 'Q06', 'Q09', 'Q12', 'Q17', 'Q21', 'Q23', 'Q27', 'Q28', 'Q30', 'Q32', 'Q36', 'Q37', 'Q38', 'Q45', 'Q47', 'Q52', 'Q53', 'Q54']
        }
    }

    if page_name not in page_keywords:
        return []

    # Get questions by ID
    page_ids = page_keywords[page_name]['ids']
    relevant_questions = [q for q in questions if q['question_id'] in page_ids]

    return relevant_questions


def get_question_by_id(question_id: str) -> Optional[Dict]:
    """Get a specific question by its ID"""
    data = load_all_questions()
    for q in data['questions']:
        if q['question_id'] == question_id:
            return q
    return None


def get_kpi_metrics_for_question(question: Dict) -> List[Dict]:
    """Extract KPI card specifications from a question"""
    return question.get('kpi_cards', [])


def get_visualizations_for_question(question: Dict) -> Dict:
    """
    Extract visualization specifications from a question

    Returns:
        {
            'primary': {...},
            'secondary': [...]
        }
    """
    return {
        'primary': question.get('primary_visualization', {}),
        'secondary': question.get('secondary_visualizations', [])
    }


def format_question_as_section(question: Dict) -> str:
    """
    Format a question as a markdown section header

    Returns:
        Formatted string like: "📊 Q01: Which regions face the most severe service coverage gaps?"
    """
    icon_map = {
        'choropleth_map': '🗺️',
        'scatter_plot': '📈',
        'line_chart': '📉',
        'bar_chart': '📊',
        'heatmap': '🔥',
        'histogram': '📊',
        'box_plot': '📦',
        'treemap': '🌳',
        'sunburst': '☀️',
        'network_graph': '🕸️'
    }

    viz_type = question.get('primary_visualization', {}).get('type', 'chart')
    icon = icon_map.get(viz_type, '📊')

    return f"{icon} **{question['question_id']}**: {question['policy_question']}"
