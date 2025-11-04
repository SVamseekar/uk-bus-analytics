"""
Template Renderer - Consulting-tone text generation with Jinja2

Professional, evidence-based narratives with dynamic value injection
"""

from jinja2 import Template, Environment
from typing import Dict, Any
from .context import ViewContext
from .rules import Insight
from . import calc


# ============================================================================
# TEMPLATE ENVIRONMENT
# ============================================================================

env = Environment()

# Custom filters
env.filters['currency'] = calc.format_currency
env.filters['pct'] = calc.format_percentage
env.filters['num'] = lambda x, p=1: f"{x:,.{p}f}"


# ============================================================================
# SUMMARY TEMPLATES
# ============================================================================

RANKING_TEMPLATE = Template("""
**{{ best.name }}** leads the nation with **{{ best.value|num(1) }} {{ unit }}**, providing extensive network connectivity and multiple journey options for residents. This is {{ best_pct_above|pct(0) }} above the national average of {{ national_avg|num(1) }} {{ unit }}.

In contrast, **{{ worst.name }}** operates only **{{ worst.value|num(1) }} {{ unit }}** ({{ worst_pct_below|pct(0) }} below national average), limiting connectivity and reducing travel options for **{{ (worst.population/1e6)|num(1) }} million residents**.
""".strip())


SINGLE_REGION_TEMPLATE = Template("""
**{{ region_name }}** ranks **#{{ rank }}** of {{ total_regions }} regions with **{{ value|num(1) }} {{ unit }}**. This is {{ pct_vs_national|pct(0) }} {{ 'above' if pct_vs_national > 0 else 'below' }} the national average of {{ national_avg|num(1) }} {{ unit }}.

{% if pct_vs_national < -10 %}
This performance gap affects {{ population|num(1) }} million residents and represents a significant service delivery challenge requiring targeted investment.
{% elif pct_vs_national > 10 %}
This strong performance demonstrates effective network planning and strategic investment in public transport infrastructure.
{% else %}
Performance is close to the national benchmark, indicating typical service provision patterns for regions of this size and density.
{% endif %}
""".strip())


# ============================================================================
# KEY FINDING TEMPLATES
# ============================================================================

VARIATION_TEMPLATE = Template("""
Service provision varies {{ variation_factor|num(1) }}x between best and worst performing regions (CV={{ cv|pct(0) }}), indicating {{ variation_label }}. This suggests that **network design and policy choices** matter more than population scale alone - smaller regions can achieve high performance through strategic planning and investment prioritization.
""".strip())


CORRELATION_TEMPLATE = Template("""
{{ strength|title }} {{ 'positive' if r > 0 else 'negative' }} correlation detected between {{ x_name }} and {{ y_name }} (r={{ r|num(2) }}, p={{ p|num(3) }}, n={{ n }}). {% if r < 0 %}Areas with higher {{ x_name }} tend to have lower {{ y_name }}, suggesting systematic service distribution patterns that may warrant policy attention.{% else %}Higher {{ x_name }} is associated with better {{ y_name }}, indicating aligned service provision.{% endif %}
""".strip())


OUTLIER_TEMPLATE = Template("""
{{ n_outliers }} region{% if n_outliers > 1 %}s{% endif %} identified as statistical outlier{% if n_outliers > 1 %}s{% endif %}: {{ outlier_regions|join(', ') }}. These areas warrant individual investigation to understand local factors driving unusual performance patterns.
""".strip())


# ============================================================================
# RECOMMENDATION TEMPLATES
# ============================================================================

GAP_INVESTMENT_TEMPLATE = Template("""
**{{ n_below_target }} region{% if n_below_target > 1 %}s{% endif %} fall below the national average**, affecting {{ (total_pop_affected/1e6)|num(1) }} million residents.

Estimated investment to bring {% if n_below_target == 1 %}this region{% else %}bottom {{ n_below_target }} regions{% endif %} to national average: **{{ investment_npv|currency(1) }}** (NPV over {{ horizon_years }} years).

**BCR: {{ bcr|num(2) }}** - {{ vfm_category }} (HM Treasury Green Book standards).

This would add {{ gap_units|num(0) }} {{ unit }}, improving connectivity for underserved communities and supporting economic growth.

**Priority actions:**
(1) Identify highest-impact corridors using demographic and employment data
(2) Design service patterns that integrate with existing networks
(3) Phase investment to target areas with greatest unmet demand first
(4) Monitor outcomes using BCR framework to ensure value delivery
""".strip())


# ============================================================================
# INVESTMENT DETAIL TEMPLATES
# ============================================================================

INVESTMENT_DETAIL_TEMPLATE = Template("""
**Investment breakdown:**
- Net Present Value ({{ horizon_years }} years, 3.5% discount): {{ npv|currency(1) }}
- Annual operating cost: {{ annual_cost|currency(1) }}
- Total undiscounted: {{ total_undiscounted|currency(1) }}

Costs calculated using TAG 2024 unit costs and HM Treasury Green Book appraisal methodology.
""".strip())


# ============================================================================
# TEMPLATE RENDERER
# ============================================================================

class TemplateRenderer:
    """Renders insights into consulting-tone narratives"""

    def __init__(self):
        self.templates = {
            ('summary', 'ranking'): RANKING_TEMPLATE,
            ('summary', 'single_region_position'): SINGLE_REGION_TEMPLATE,
            ('key_finding', 'variation'): VARIATION_TEMPLATE,
            ('key_finding', 'correlation'): CORRELATION_TEMPLATE,
            ('key_finding', 'outliers'): OUTLIER_TEMPLATE,
            ('recommendation', 'gap_investment'): GAP_INVESTMENT_TEMPLATE,
            ('investment', 'investment_detail'): INVESTMENT_DETAIL_TEMPLATE,
        }

    def render(self, insight: Insight) -> str:
        """
        Render an insight to text

        Args:
            insight: Insight to render

        Returns:
            Rendered text
        """
        key = (insight.kind, insight.key)

        if key not in self.templates:
            return f"[Template not found for {insight.kind}/{insight.key}]"

        template = self.templates[key]

        try:
            return template.render(**insight.payload)
        except Exception as e:
            return f"[Rendering error: {e}]"

    def render_all(self, insights: list) -> Dict[str, str]:
        """
        Render all insights organized by kind

        Args:
            insights: List of Insight objects

        Returns:
            Dict with 'summary', 'key_finding', 'recommendation', 'investment' keys
        """
        result = {
            'summary': '',
            'key_finding': '',
            'recommendation': '',
            'investment': ''
        }

        for insight in insights:
            rendered = self.render(insight)

            if insight.kind in result:
                # Concatenate multiple insights of same kind
                if result[insight.kind]:
                    result[insight.kind] += "\n\n" + rendered
                else:
                    result[insight.kind] = rendered

        return result
