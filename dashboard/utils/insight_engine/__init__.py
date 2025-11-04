"""
Insight Engine - Dynamic narrative generation for UK Bus Analytics Dashboard

Architecture:
1. Context Resolver - Understands filter state and data shape
2. Centralized Calculators - TAG 2024 constants, BCR, stats, equity metrics
3. Insight Rules - Evidence-gated pattern detection
4. Template Renderer - Consulting-tone text generation
5. Evidence & Guardrails - Data sufficiency checks, source stamping

Usage:
    from dashboard.utils.insight_engine import InsightEngine, MetricConfig

    engine = InsightEngine()
    result = engine.run(df, metric_config, filters)

    # result contains: summary, key_finding, recommendation, investment, sources
"""

from .engine import InsightEngine
from .context import ViewContext, resolve_context
from .calc import TAG_2024, calculate_bcr, calculate_correlation, calculate_gap_to_target
from .rules import InsightRule, INSIGHT_REGISTRY
from .config import MetricConfig

__all__ = [
    'InsightEngine',
    'ViewContext',
    'resolve_context',
    'TAG_2024',
    'calculate_bcr',
    'calculate_correlation',
    'calculate_gap_to_target',
    'InsightRule',
    'INSIGHT_REGISTRY',
    'MetricConfig'
]

__version__ = '1.0.0'
