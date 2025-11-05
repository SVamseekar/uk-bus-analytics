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

    def run_correlation(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        x_name: str,
        y_name: str,
        metric_name: str = "coverage",
        dimension: str = "characteristic",
        rules: List[str] = ['correlation', 'quartile_comparison'],
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate narrative for correlation analysis (LSOA-level data)

        Simpler interface for Category D correlation patterns.

        Args:
            df: DataFrame with LSOA-level data
            x_col: X variable column name
            y_col: Y variable column name
            x_name: Display name for X variable
            y_name: Display name for Y variable
            metric_name: Name of metric being analyzed (e.g., "coverage", "stops per 1,000")
            dimension: Dimension being compared (e.g., "deprivation", "elderly population")
            rules: Which rules to apply
            sources: Data sources list

        Returns:
            Dict with summary, key_finding, etc.
        """
        metrics = {
            'unit': metric_name,
            'n': len(df),
            'x_name': x_name,
            'y_name': y_name,
            'metric_name': metric_name,
            'dimension': dimension
        }

        # Calculate correlation
        corr_result = calc.calculate_correlation(df, x_col, y_col)
        if corr_result:
            metrics['correlation'] = corr_result

        # Calculate quartile comparison if both columns exist
        if x_col in df.columns and y_col in df.columns:
            # Remove NaNs
            valid_data = df[[x_col, y_col, 'total_population']].dropna()

            if len(valid_data) >= 30:
                # High = top 25% of x_col, Low = bottom 25% of x_col
                q75 = valid_data[x_col].quantile(0.75)
                q25 = valid_data[x_col].quantile(0.25)

                high_group = valid_data[valid_data[x_col] >= q75]
                low_group = valid_data[valid_data[x_col] <= q25]

                # Calculate population-weighted y_col for each group
                high_value = (high_group[y_col] * high_group['total_population']).sum() / high_group['total_population'].sum()
                low_value = (low_group[y_col] * low_group['total_population']).sum() / low_group['total_population'].sum()

                gap_pct = ((high_value / low_value) - 1) * 100 if low_value > 0 else 0

                metrics['quartile_comparison'] = {
                    'high_label': f"High {dimension} areas (≥75th percentile)",
                    'low_label': f"Low {dimension} areas (≤25th percentile)",
                    'high_value': high_value,
                    'low_value': low_value,
                    'gap_pct': gap_pct,
                    'metric_name': metric_name,
                    'dimension': dimension
                }

        # Simple context for correlation analysis
        context = ViewContext(
            scope="correlation",
            n_groups=len(df),
            filter_mode='all_regions',
            filter_value=None
        )

        # Apply rules
        insights = []
        for rule_name in rules:
            rule_list = INSIGHT_REGISTRY.for_metric('correlation_analysis', [rule_name])
            for rule in rule_list:
                if data_sufficient(metrics, rule.requirements) and rule.applies(context, metrics):
                    insights.extend(rule.emit(context, metrics))

        # Render
        rendered = self.renderer.render_all(insights)

        return {
            'summary': '',
            'key_finding': rendered.get('key_finding', ''),
            'recommendation': '',
            'investment': '',
            'sources': sources or [],
            'evidence': metrics,
            'context': context
        }

    def run_power_law(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        x_name: str = "Population",
        y_name: str = "Stop Count",
        rules: List[str] = ['power_law', 'efficiency'],
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate narrative for power law analysis (log-log correlation)

        Used for analyzing scaling relationships like population vs stop density.

        Args:
            df: DataFrame with data
            x_col: X variable column (e.g., 'total_population')
            y_col: Y variable column (e.g., 'num_stops')
            x_name: Display name for X
            y_name: Display name for Y
            rules: Which rules to apply
            sources: Data sources

        Returns:
            Dict with key_finding, recommendation, evidence
        """
        import numpy as np
        from scipy import stats as scipy_stats

        # Filter valid data (both > 0 for log transform)
        valid_data = df[(df[x_col] > 0) & (df[y_col] > 0)].copy()

        if len(valid_data) < 30:
            return {
                'summary': '',
                'key_finding': '⚠️ Insufficient data for power law analysis (n < 30)',
                'recommendation': '',
                'investment': '',
                'sources': sources or [],
                'evidence': {'n': len(valid_data)},
                'context': None
            }

        # Log-transform
        log_x = np.log10(valid_data[x_col])
        log_y = np.log10(valid_data[y_col])

        # Linear regression on log-log data
        slope, intercept = np.polyfit(log_x, log_y, 1)
        r, p_value = scipy_stats.pearsonr(log_x, log_y)

        # Create polynomial for predictions
        poly = np.poly1d([slope, intercept])

        # Calculate efficiency
        valid_data['expected'] = 10 ** poly(log_x)
        valid_data['efficiency'] = (valid_data[y_col] / valid_data['expected']) * 100

        # Identify under/over-served
        underserved = valid_data[valid_data['efficiency'] < 80]  # >20% below expected
        overserved = valid_data[valid_data['efficiency'] > 120]  # >20% above expected

        # Build metrics
        metrics = {
            'power_law': {
                'slope': slope,
                'intercept': intercept,
                'r': r,
                'p_value': p_value,
                'n': len(valid_data)
            },
            'efficiency_analysis': {
                'n_underserved': len(underserved),
                'n_overserved': len(overserved),
                'n_well_served': len(valid_data) - len(underserved) - len(overserved),
                'pop_underserved': underserved[x_col].sum() if 'total_population' in underserved.columns else 0,
                'additional_stops_needed': (underserved['expected'].sum() - underserved[y_col].sum()) if len(underserved) > 0 else 0,
                'pct_underserved_lsoas': (len(underserved) / len(valid_data)) * 100,
                'pct_underserved_pop': (underserved[x_col].sum() / valid_data[x_col].sum()) * 100 if len(underserved) > 0 else 0
            }
        }

        # Simple context
        context = ViewContext(
            scope="power_law",
            n_groups=len(valid_data),
            filter_mode='all_regions',
            filter_value=None
        )

        # Apply rules
        insights = []
        for rule_name in rules:
            rule_list = INSIGHT_REGISTRY.for_metric('power_law_analysis', [rule_name])
            for rule in rule_list:
                if data_sufficient(metrics, rule.requirements) and rule.applies(context, metrics):
                    insights.extend(rule.emit(context, metrics))

        # Render
        rendered = self.renderer.render_all(insights)

        return {
            'summary': '',
            'key_finding': rendered.get('key_finding', ''),
            'recommendation': rendered.get('recommendation', ''),
            'investment': '',
            'sources': sources or [],
            'evidence': metrics,
            'context': context
        }

    def _calculate_national_average(self, df: pd.DataFrame, value_col: str) -> float:
        """
        Calculate population-weighted national average for per-capita metrics

        For per-capita metrics like routes_per_100k or stops_per_1000, we must NOT
        take the simple mean of per-capita values (which weights small regions equally).
        Instead, we recalculate from raw totals weighted by population.

        Args:
            df: DataFrame with regional data
            value_col: Column name (e.g., 'routes_per_100k', 'stops_per_1000')

        Returns:
            Population-weighted national average
        """
        if df.empty or 'population' not in df.columns:
            # Fallback to simple mean if no population data
            return df[value_col].mean() if value_col in df.columns else 0

        # Map per-capita columns to their raw count columns
        if value_col == 'routes_per_100k' and 'routes_count' in df.columns:
            # Recalculate: total routes / total population * 100,000
            total_routes = df['routes_count'].sum()
            total_pop = df['population'].sum()
            return (total_routes / total_pop * 100000) if total_pop > 0 else 0

        elif value_col == 'stops_per_1000' and 'total_stops' in df.columns:
            # Recalculate: total stops / total population * 1,000
            total_stops = df['total_stops'].sum()
            total_pop = df['population'].sum()
            return (total_stops / total_pop * 1000) if total_pop > 0 else 0

        else:
            # For non-per-capita metrics, simple mean is fine
            return df[value_col].mean() if value_col in df.columns else 0

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

        # National average - for single regions, load full dataset
        # CRITICAL: For per-capita metrics, must use population-weighted average, not simple mean
        if context.scope == "single_region":
            # Load full regional summary for true national comparison
            try:
                from dashboard.utils.data_loader import load_regional_summary
                full_df = load_regional_summary()
                if not full_df.empty and config.value_col in full_df.columns:
                    # Calculate population-weighted average for per-capita metrics
                    metrics['national_avg'] = self._calculate_national_average(full_df, config.value_col)
                    metrics['total_regions'] = len(full_df)
                else:
                    metrics['national_avg'] = self._calculate_national_average(df, config.value_col)
                    metrics['total_regions'] = 1
            except Exception:
                # Fallback if import fails
                metrics['national_avg'] = self._calculate_national_average(df, config.value_col)
                metrics['total_regions'] = 1
        else:
            # For multi-region views, use current data
            metrics['national_avg'] = self._calculate_national_average(df, config.value_col)

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

        # Single region positioning - calculate rank against full dataset
        if context.scope == "single_region" and config.groupby in df.columns:
            region_row = df.iloc[0]
            region_name = region_row[config.groupby]
            region_value = region_row[config.value_col]

            # Load full dataset and calculate true rank
            try:
                from dashboard.utils.data_loader import load_regional_summary
                full_df = load_regional_summary()

                if not full_df.empty and config.value_col in full_df.columns:
                    # Calculate rank: higher values = better rank (rank 1 = highest value)
                    full_df_sorted = full_df.sort_values(config.value_col, ascending=False).reset_index(drop=True)

                    # Find this region's rank in the full dataset
                    if config.groupby in full_df.columns:
                        region_in_full = full_df[full_df[config.groupby] == region_name]
                        if not region_in_full.empty:
                            true_rank = (full_df[config.value_col] > region_value).sum() + 1
                            total_regions = len(full_df)
                        else:
                            true_rank = 0
                            total_regions = len(full_df)
                    else:
                        true_rank = 1
                        total_regions = 1
                else:
                    true_rank = 1
                    total_regions = 1
            except Exception:
                # Fallback if loading fails
                true_rank = region_row.get('rank', region_row.get(f'{config.value_col}_rank', 1))
                total_regions = 1

            metrics['this_region'] = {
                'name': region_name,
                'value': region_value,
                'rank': true_rank,
                'total_regions': total_regions,
                'pct_vs_national': ((region_value / metrics['national_avg']) - 1) * 100 if metrics['national_avg'] != 0 else 0,
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
