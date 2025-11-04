"""
Insight Engine - Orchestrates dynamic narrative generation

Coordinates all layers: context resolution, metrics computation, rule application, template rendering
"""

from typing import Dict, Any, List
import pandas as pd
from .context import ViewContext, resolve_context, data_sufficient
from .config import MetricConfig
from .rules import INSIGHT_REGISTRY, Insight
from .templates import TemplateRenderer
from . import calc


class InsightEngine:
    """
    Main engine that generates dynamic, context-aware narratives

    Usage:
        engine = InsightEngine()
        result = engine.run(df, metric_config, filters)
    """

    def __init__(self):
        self.renderer = TemplateRenderer()

    def run(self, df: pd.DataFrame, config: MetricConfig, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate narrative for a metric

        Args:
            df: DataFrame with data (after filters applied)
            config: Metric configuration
            filters: Dict of active filters

        Returns:
            Dict with:
                - summary: Executive summary
                - key_finding: Critical insight
                - recommendation: Policy actions
                - investment: Investment details
                - sources: Data sources list
                - evidence: All underlying numbers (for QA/export)
                - context: ViewContext object
        """

        # Step 1: Resolve context
        context = resolve_context(df, config.groupby, filters)

        # Step 2: Compute metrics
        metrics = self._compute_metrics(df, config, context)

        # Step 3: Select and apply rules
        insights = self._apply_rules(context, metrics, config)

        # Step 4: Render templates
        rendered = self.renderer.render_all(insights)

        # Step 5: Return complete result
        return {
            'summary': rendered.get('summary', ''),
            'key_finding': rendered.get('key_finding', ''),
            'recommendation': rendered.get('recommendation', ''),
            'investment': rendered.get('investment', ''),
            'sources': config.sources,
            'evidence': metrics,
            'context': context
        }

    def _compute_metrics(self, df: pd.DataFrame, config: MetricConfig, context: ViewContext) -> Dict[str, Any]:
        """
        Compute all metrics needed for rule evaluation

        Returns comprehensive metrics dict
        """
        metrics = {
            'unit': config.unit,
            'n': len(df),
            'n_groups': context.n_groups
        }

        if df.empty or config.value_col not in df.columns:
            return metrics

        # Distribution statistics
        metrics['distribution'] = calc.describe_distribution(df[config.value_col])

        # National average (or mean of current view)
        metrics['national_avg'] = df[config.value_col].mean()

        # Extrema (best/worst)
        if context.n_groups >= 2:
            max_idx = df[config.value_col].idxmax()
            min_idx = df[config.value_col].idxmin()

            metrics['extrema'] = {
                'max_row': {
                    'name': df.loc[max_idx, config.groupby] if config.groupby in df.columns else 'Unknown',
                    'value': df.loc[max_idx, config.value_col],
                    'population': df.loc[max_idx, 'population'] if 'population' in df.columns else 0
                },
                'min_row': {
                    'name': df.loc[min_idx, config.groupby] if config.groupby in df.columns else 'Unknown',
                    'value': df.loc[min_idx, config.value_col],
                    'population': df.loc[min_idx, 'population'] if 'population' in df.columns else 0
                }
            }

        # Single region positioning
        if context.scope == "single_region" and config.groupby in df.columns:
            region_row = df.iloc[0]

            # Load full dataset for national comparison
            # (In real implementation, this would load cached national summary)
            metrics['this_region'] = {
                'name': region_row[config.groupby],
                'value': region_row[config.value_col],
                'rank': region_row.get('rank', region_row.get(f'{config.value_col}_rank', 0)),
                'pct_vs_national': ((region_row[config.value_col] / metrics['national_avg']) - 1) * 100 if metrics['national_avg'] != 0 else 0,
                'population': region_row.get('population', 0)
            }

        # Gap analysis (regions below target)
        df_with_gaps = calc.calculate_gap_to_target(df, config.value_col)
        regions_below = df_with_gaps[df_with_gaps['below_target']]

        if len(regions_below) > 0:
            total_gap_units = regions_below['gap_absolute'].sum()
            total_pop_affected = regions_below['population'].sum() if 'population' in regions_below.columns else 0

            metrics['gaps'] = {
                'n_below_target': len(regions_below),
                'total_gap_units': total_gap_units,
                'total_pop_affected': total_pop_affected,
                'regions': regions_below[config.groupby].tolist() if config.groupby in regions_below.columns else []
            }

            # Calculate investment requirement (simplified - uses route cost)
            unit_cost = calc.UnitCosts.ROUTE_OPERATING_COST_URBAN  # TODO: Make configurable
            investment_calc = calc.calculate_investment_requirement(
                gap_units=total_gap_units,
                unit_cost=unit_cost,
                horizon_years=10
            )
            metrics['investment'] = investment_calc

            # Calculate BCR
            if total_pop_affected > 0:
                bcr_result = calc.calculate_bcr(
                    investment=investment_calc['npv'],
                    population_benefited=total_pop_affected,
                    service_improvement=total_gap_units,
                    area_type='urban'  # TODO: Detect from data
                )
                metrics['bcr'] = bcr_result

        # Outliers
        if metrics['distribution'].get('n_outliers', 0) > 0 and config.groupby in df.columns:
            dist = metrics['distribution']
            q1 = dist['q1']
            q3 = dist['q3']
            iqr = dist['iqr']
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr

            outlier_mask = (df[config.value_col] < lower_fence) | (df[config.value_col] > upper_fence)
            outlier_regions = df.loc[outlier_mask, config.groupby].tolist()
            metrics['outlier_regions'] = outlier_regions

        return metrics

    def _apply_rules(self, context: ViewContext, metrics: Dict[str, Any], config: MetricConfig) -> List[Insight]:
        """
        Apply insight rules and collect insights

        Returns list of Insight objects
        """
        insights = []

        # Get rules for this metric
        rules = INSIGHT_REGISTRY.for_metric(config.id, config.rules)

        for rule in rules:
            # Check data sufficiency
            if not data_sufficient(metrics, rule.requirements):
                continue

            # Check if rule applies
            if not rule.applies(context, metrics):
                continue

            # Generate insights
            rule_insights = rule.emit(context, metrics)
            insights.extend(rule_insights)

        return insights
