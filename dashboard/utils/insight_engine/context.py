"""
Context Resolver - Understands filter state and data shape

Prevents bugs like "best/worst" comparisons on single-row datasets
"""

from dataclasses import dataclass
from typing import Literal, Optional
import pandas as pd


@dataclass
class ViewContext:
    """
    Describes the current view context based on filters and data shape

    Attributes:
        scope: Type of view (all_regions, single_region, subset)
        n_groups: Number of groups after filtering/grouping
        region: Selected region name (if single_region)
        filters: Dict of active filters
        groupby_col: Column used for grouping
    """
    scope: Literal["all_regions", "single_region", "subset"]
    n_groups: int
    region: Optional[str]
    filters: dict
    groupby_col: str


def resolve_context(df: pd.DataFrame, groupby_col: str, filters: dict) -> ViewContext:
    """
    Resolve view context from data and filters

    Args:
        df: DataFrame after filters applied
        groupby_col: Column to group by (e.g., 'region_name')
        filters: Dict of active filters {'region': 'West Midlands', 'urban_only': True, ...}

    Returns:
        ViewContext describing the current view

    Examples:
        >>> df_all = load_regional_summary()
        >>> ctx = resolve_context(df_all, 'region_name', {})
        >>> ctx.scope
        'all_regions'

        >>> df_single = df_all[df_all['region_name'] == 'West Midlands']
        >>> ctx = resolve_context(df_single, 'region_name', {'region': 'West Midlands'})
        >>> ctx.scope
        'single_region'
    """

    # Handle empty data
    if df.empty:
        return ViewContext(
            scope="subset",
            n_groups=0,
            region=None,
            filters=filters,
            groupby_col=groupby_col
        )

    # Count unique groups
    if groupby_col not in df.columns:
        n_groups = 1
    else:
        n_groups = df[groupby_col].nunique()

    # Determine scope
    region_filter = filters.get('region')

    if n_groups == 1 and region_filter and region_filter != 'All Regions':
        # Single region selected
        return ViewContext(
            scope="single_region",
            n_groups=1,
            region=region_filter,
            filters=filters,
            groupby_col=groupby_col
        )

    elif not filters or (len(filters) == 1 and filters.get('region') == 'All Regions'):
        # No filters or only "All Regions" selected
        return ViewContext(
            scope="all_regions",
            n_groups=n_groups,
            region=None,
            filters=filters,
            groupby_col=groupby_col
        )

    else:
        # Subset view (urban/rural, demographic filters, etc.)
        return ViewContext(
            scope="subset",
            n_groups=n_groups,
            region=region_filter if region_filter != 'All Regions' else None,
            filters=filters,
            groupby_col=groupby_col
        )


def data_sufficient(metrics: dict, requirements: dict) -> bool:
    """
    Check if data meets minimum requirements for showing insights

    Args:
        metrics: Computed metrics dict
        requirements: Dict with thresholds like {'min_n': 30, 'min_groups': 3, 'max_missing': 0.2}

    Returns:
        True if data sufficient, False otherwise

    Examples:
        >>> metrics = {'n': 50, 'n_groups': 5, 'missing_rate': 0.1}
        >>> requirements = {'min_n': 30, 'min_groups': 3, 'max_missing': 0.2}
        >>> data_sufficient(metrics, requirements)
        True

        >>> metrics = {'n': 20, 'n_groups': 2}
        >>> data_sufficient(metrics, requirements)
        False
    """

    # Check minimum sample size
    if 'min_n' in requirements:
        if metrics.get('n', 0) < requirements['min_n']:
            return False

    # Check minimum groups (for between-group comparisons)
    if 'min_groups' in requirements:
        if metrics.get('n_groups', 0) < requirements['min_groups']:
            return False

    # Check maximum missing rate
    if 'max_missing' in requirements:
        if metrics.get('missing_rate', 1.0) > requirements['max_missing']:
            return False

    # Check minimum match rate (for demographic merges)
    if 'min_match_rate' in requirements:
        if metrics.get('match_rate', 0.0) < requirements['min_match_rate']:
            return False

    return True
