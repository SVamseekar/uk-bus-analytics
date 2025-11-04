"""
Centralized Calculators - Single source of truth for all metrics

Contains TAG 2024 constants, BCR calculations, statistical functions, equity metrics
All numbers in narratives must come from functions in this module
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats


# ============================================================================
# TAG 2024 CONSTANTS (WebTAG Data Book, January 2024)
# ============================================================================

@dataclass
class TAG_2024:
    """Transport Analysis Guidance 2024 values (DfT WebTAG)"""

    # Time values (£/hour, 2010 prices, uplifted to 2024)
    TIME_VALUE_BUS_COMMUTING = 9.85
    TIME_VALUE_CAR_COMMUTING = 12.65
    TIME_VALUE_BUSINESS = 28.30
    TIME_VALUE_LEISURE = 7.85

    # Carbon values (£/tonne CO2e, 2024)
    CARBON_VALUE_2024 = 80.0  # TAG A3 central value

    # Emissions (kg CO2e per passenger-km)
    BUS_EMISSIONS = 0.0965  # BEIS 2024
    CAR_EMISSIONS = 0.171   # Average car

    # Agglomeration uplift factors
    AGGLOMERATION_URBAN = 1.25    # 25% uplift in urban areas
    AGGLOMERATION_CITY = 1.50     # 50% uplift in city centers

    # HM Treasury Green Book BCR categories
    BCR_POOR = 1.0
    BCR_LOW = 1.5
    BCR_MEDIUM = 2.0
    BCR_HIGH = 2.5
    BCR_VERY_HIGH = 4.0

    # Discount rate
    DISCOUNT_RATE = 0.035  # 3.5% social time preference

    @staticmethod
    def bcr_category(bcr: float) -> str:
        """
        Get HM Treasury Green Book BCR category

        Args:
            bcr: Benefit-cost ratio

        Returns:
            Category string
        """
        if bcr < TAG_2024.BCR_POOR:
            return "Poor value for money"
        elif bcr < TAG_2024.BCR_LOW:
            return "Low value for money"
        elif bcr < TAG_2024.BCR_MEDIUM:
            return "Medium value for money"
        elif bcr < TAG_2024.BCR_HIGH:
            return "High value for money"
        elif bcr < TAG_2024.BCR_VERY_HIGH:
            return "Very high value for money"
        else:
            return "Exceptional value for money"


# ============================================================================
# UNIT COSTS (for investment calculations)
# ============================================================================

@dataclass
class UnitCosts:
    """Unit costs for infrastructure and operations"""

    # Infrastructure (one-time)
    BUS_STOP_INSTALLATION = 15000  # £15k per stop (basic shelter + signage)
    BUS_STOP_ACCESSIBLE = 35000    # £35k per accessible stop (raised platform, shelter)

    # Operating costs (annual per route)
    ROUTE_OPERATING_COST_URBAN = 250000   # £250k/year urban route
    ROUTE_OPERATING_COST_RURAL = 180000   # £180k/year rural route

    # Vehicles
    SINGLE_DECK_BUS = 200000       # £200k capital cost
    DOUBLE_DECK_BUS = 300000       # £300k capital cost


# ============================================================================
# RANKING & BENCHMARKING
# ============================================================================

def calculate_rank_and_distance(df: pd.DataFrame, value_col: str, groupby_col: str = 'region_name') -> pd.DataFrame:
    """
    Calculate rankings and distance from national average

    Args:
        df: DataFrame with metric values
        value_col: Column to rank
        groupby_col: Column defining groups

    Returns:
        DataFrame with rank, pct_vs_national, distance_from_avg columns
    """
    if df.empty or value_col not in df.columns:
        return df

    # Calculate national average
    national_avg = df[value_col].mean()

    # Add ranking (1 = highest value)
    df = df.copy()
    df['rank'] = df[value_col].rank(ascending=False, method='min').astype(int)

    # Calculate percentage vs national
    df['pct_vs_national'] = ((df[value_col] / national_avg) - 1) * 100

    # Absolute distance from average
    df['distance_from_avg'] = df[value_col] - national_avg

    return df


def describe_distribution(series: pd.Series) -> dict:
    """
    Comprehensive distribution description

    Returns:
        Dict with mean, median, std, cv, iqr, min, max, outliers
    """
    if series.empty:
        return {}

    # Remove NaN
    s = series.dropna()

    if len(s) == 0:
        return {}

    # Basic stats
    mean = s.mean()
    median = s.median()
    std = s.std()
    cv = std / mean if mean != 0 else np.inf  # Coefficient of variation

    # Quantiles
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1

    # Outliers (IQR method)
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    outliers = s[(s < lower_fence) | (s > upper_fence)]

    return {
        'mean': mean,
        'median': median,
        'std': std,
        'cv': cv,
        'min': s.min(),
        'max': s.max(),
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'n_outliers': len(outliers),
        'outlier_values': outliers.tolist() if len(outliers) > 0 else []
    }


# ============================================================================
# GAP ANALYSIS & INVESTMENT
# ============================================================================

def calculate_gap_to_target(df: pd.DataFrame, value_col: str, target = 'national_avg') -> pd.DataFrame:
    """
    Calculate gap to target (e.g., national average)

    Args:
        df: DataFrame with values
        value_col: Column with metric values
        target: Target value or 'national_avg'

    Returns:
        DataFrame with gap columns
    """
    if df.empty or value_col not in df.columns:
        return df

    df = df.copy()

    # Resolve target
    if target == 'national_avg':
        target_value = df[value_col].mean()
    else:
        target_value = float(target)

    # Calculate gaps
    df['gap_absolute'] = target_value - df[value_col]
    df['gap_relative'] = (df['gap_absolute'] / target_value) * 100
    df['below_target'] = df['gap_absolute'] > 0

    return df


def calculate_investment_requirement(
    gap_units: float,
    unit_cost: float,
    horizon_years: int = 10,
    discount_rate: float = TAG_2024.DISCOUNT_RATE
) -> dict:
    """
    Calculate investment requirement for closing a gap

    Args:
        gap_units: Number of units needed (routes, stops, etc.)
        unit_cost: Cost per unit (annual for operating, one-time for capital)
        horizon_years: Appraisal period
        discount_rate: Social discount rate

    Returns:
        Dict with npv, annual_cost, total_undiscounted
    """
    if gap_units <= 0:
        return {'npv': 0, 'annual_cost': 0, 'total_undiscounted': 0}

    # NPV of annual costs
    discount_factors = [(1 + discount_rate) ** -t for t in range(1, horizon_years + 1)]
    npv = sum(unit_cost * gap_units * df for df in discount_factors)

    return {
        'npv': npv,
        'annual_cost': unit_cost * gap_units,
        'total_undiscounted': unit_cost * gap_units * horizon_years,
        'gap_units': gap_units,
        'horizon_years': horizon_years
    }


# ============================================================================
# BCR CALCULATION (simplified wrapper - delegates to full calculator)
# ============================================================================

def calculate_bcr(
    investment: float,
    population_benefited: float,
    service_improvement: float,
    area_type: str = 'urban',
    **kwargs
) -> dict:
    """
    Calculate simplified BCR for narrative purposes

    For full BCR calculation, use the dedicated module:
    archive_20251031_cleanup/analysis/spatial/utils/bcr_calculator.py

    Args:
        investment: Total investment (£)
        population_benefited: Number of people affected
        service_improvement: Improvement metric (e.g., added routes, reduced time)
        area_type: 'urban' or 'rural'

    Returns:
        Dict with bcr, vfm_category, benefits, costs
    """

    # Simplified benefit calculation for narratives
    # Assumes average time saving of 5 minutes per person per trip, 250 trips/year
    time_saving_hours = (5 / 60) * 250 * population_benefited

    # Apply TAG 2024 time value
    time_benefits = time_saving_hours * TAG_2024.TIME_VALUE_BUS_COMMUTING

    # Apply agglomeration uplift
    if area_type == 'urban':
        time_benefits *= TAG_2024.AGGLOMERATION_URBAN
    elif area_type == 'city':
        time_benefits *= TAG_2024.AGGLOMERATION_CITY

    # Simplified BCR
    bcr = time_benefits / investment if investment > 0 else 0

    return {
        'bcr': bcr,
        'vfm_category': TAG_2024.bcr_category(bcr),
        'benefits': time_benefits,
        'costs': investment,
        'time_saving_hours': time_saving_hours
    }


# ============================================================================
# STATISTICAL FUNCTIONS
# ============================================================================

def calculate_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    min_n: int = 30,
    alpha: float = 0.05
) -> Optional[dict]:
    """
    Calculate correlation with significance test

    Args:
        df: DataFrame
        x_col: First variable
        y_col: Second variable
        min_n: Minimum sample size
        alpha: Significance level

    Returns:
        Dict with r, p, n, significant, or None if insufficient data
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return None

    # Remove missing values
    data = df[[x_col, y_col]].dropna()

    if len(data) < min_n:
        return None

    # Calculate Pearson correlation
    r, p = stats.pearsonr(data[x_col], data[y_col])

    return {
        'r': r,
        'p': p,
        'n': len(data),
        'significant': p < alpha,
        'strength': _correlation_strength(abs(r))
    }


def _correlation_strength(r: float) -> str:
    """Interpret correlation strength"""
    r = abs(r)
    if r < 0.3:
        return "weak"
    elif r < 0.5:
        return "moderate"
    elif r < 0.7:
        return "strong"
    else:
        return "very strong"


# ============================================================================
# EQUITY METRICS
# ============================================================================

def calculate_gini_coefficient(values: pd.Series, weights: Optional[pd.Series] = None) -> float:
    """
    Calculate Gini coefficient (0 = perfect equality, 1 = perfect inequality)

    Args:
        values: Distribution values
        weights: Optional weights (e.g., population)

    Returns:
        Gini coefficient
    """
    if values.empty:
        return 0.0

    values = values.dropna()

    if len(values) == 0:
        return 0.0

    # Sort values
    sorted_values = np.sort(values)

    if weights is None:
        weights = np.ones(len(sorted_values))
    else:
        weights = weights.iloc[values.index].values
        weights = weights[np.argsort(values)]

    # Calculate Gini
    n = len(sorted_values)
    cumsum = np.cumsum(sorted_values * weights)
    total = cumsum[-1]

    if total == 0:
        return 0.0

    gini = (n + 1 - 2 * np.sum(cumsum) / total) / n

    return max(0.0, min(1.0, gini))  # Clamp to [0, 1]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(value: float, precision: int = 0) -> str:
    """Format as £M or £k"""
    if value >= 1_000_000:
        return f"£{value/1_000_000:.{precision}f}M"
    elif value >= 1_000:
        return f"£{value/1_000:.{precision}f}k"
    else:
        return f"£{value:.{precision}f}"


def format_percentage(value: float, precision: int = 0, include_sign: bool = True) -> str:
    """Format as percentage with optional +/- sign"""
    if include_sign and value > 0:
        return f"+{value:.{precision}f}%"
    return f"{value:.{precision}f}%"
