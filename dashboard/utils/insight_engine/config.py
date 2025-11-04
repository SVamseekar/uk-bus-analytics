"""
Metric Configuration - Defines what to analyze and how
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MetricConfig:
    """
    Configuration for a metric/analysis section

    Attributes:
        id: Unique identifier (e.g., 'routes_per_100k')
        groupby: Column to group by (e.g., 'region_name')
        value_col: Column with metric values
        unit: Display unit (e.g., 'routes per 100,000 population')
        sources: Data sources list
        rules: List of insight rule names to apply
        min_n: Minimum sample size
        min_groups: Minimum number of groups for comparisons
    """
    id: str
    groupby: str
    value_col: str
    unit: str
    sources: List[str]
    rules: List[str]
    min_n: int = 1
    min_groups: int = 1
    title: Optional[str] = None
    description: Optional[str] = None
