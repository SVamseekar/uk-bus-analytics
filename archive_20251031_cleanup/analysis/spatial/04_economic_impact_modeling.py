"""
Economic Impact Modeling
Implements Category J questions (J58-J61): Advanced Economic Impact Analysis

Addresses consulting firm gaps:
- BCR analysis (UK Treasury Green Book methodology)
- GDP multiplier effects (ONS input-output modeling)
- Employment impact assessment
- Carbon emissions quantification

Author: UK Bus Analytics Project
Date: 2025-10-29
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple
from datetime import datetime

# Import BCR calculator
from analysis.spatial.utils.bcr_calculator import BCRCalculator


class EconomicImpactAnalyzer:
    """
    Comprehensive economic impact analysis for bus service improvements
    """

    def __init__(self, lsoa_data_path: str = None):
        """
        Initialize economic impact analyzer

        Args:
            lsoa_data_path: Path to integrated LSOA data
        """
        self.bcr_calculator = BCRCalculator()
        self.lsoa_data = None

        if lsoa_data_path:
            self.load_data(lsoa_data_path)

    def load_data(self, data_path: str):
        """Load LSOA integrated data"""
        try:
            if data_path.endswith('.parquet'):
                self.lsoa_data = pd.read_parquet(data_path)
            elif data_path.endswith('.csv'):
                self.lsoa_data = pd.read_csv(data_path)
            else:
                raise ValueError("Data file must be .parquet or .csv")

            print(f"✅ Loaded {len(self.lsoa_data):,} LSOAs")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise

    def j58_bcr_investment_analysis(
        self,
        top_n_underserved: int = 10,
        investment_amount: float = 10_000_000
    ) -> Dict:
        """
        J58: Calculate BCR for investing £10M in top underserved LSOAs

        Args:
            top_n_underserved: Number of LSOAs to target
            investment_amount: Total investment (£)

        Returns:
            BCR analysis for top underserved areas
        """

        print(f"\n{'=' * 80}")
        print(f"J58: BCR Analysis for £{investment_amount:,.0f} Investment")
        print(f"{'=' * 80}\n")

        # Identify underserved LSOAs
        # Criteria: High population + Low stops + High deprivation
        underserved = self.lsoa_data.copy()

        # Calculate underserved score
        underserved['population_score'] = (
            underserved['population'] / underserved['population'].max()
        )
        underserved['stops_score'] = 1 - (
            underserved['bus_stops'] / underserved['bus_stops'].max()
        )  # Invert: lower stops = higher score

        if 'imd_decile' in underserved.columns:
            underserved['deprivation_score'] = 1 - (
                underserved['imd_decile'] / 10
            )  # Invert: lower decile = higher deprivation
        else:
            underserved['deprivation_score'] = 0.5  # Neutral if no IMD data

        # Composite underserved score
        underserved['underserved_score'] = (
            underserved['population_score'] * 0.4 +
            underserved['stops_score'] * 0.4 +
            underserved['deprivation_score'] * 0.2
        )

        # Select top N
        top_underserved = underserved.nlargest(top_n_underserved, 'underserved_score')

        print(f"Top {top_n_underserved} Underserved LSOAs:")
        print(top_underserved[['lsoa_code', 'population', 'bus_stops', 'underserved_score']].to_string())
        print()

        # Calculate BCR
        bcr_result = self.bcr_calculator.calculate_full_bcr(
            lsoa_data=top_underserved,
            investment_amount=investment_amount
        )

        # Add LSOA details
        bcr_result['target_lsoas'] = top_underserved[['lsoa_code', 'population', 'bus_stops', 'underserved_score']].to_dict('records')

        # Print summary
        print(f"BCR ANALYSIS RESULTS:")
        print(f"  Investment: £{bcr_result['summary']['investment_amount']:,.0f}")
        print(f"  Total Cost (PV): £{bcr_result['summary']['total_cost_pv']:,.0f}")
        print(f"  Total Benefits (PV): £{bcr_result['summary']['total_benefits_pv']:,.0f}")
        print(f"  BCR: {bcr_result['summary']['bcr']:.2f}")
        print(f"  NPV: £{bcr_result['summary']['npv']:,.0f}")
        print(f"  Recommendation: {bcr_result['summary']['recommendation']}")
        print()

        print(f"BENEFIT BREAKDOWN (Present Value):")
        for benefit_type, value in bcr_result['benefit_breakdown_pv'].items():
            percentage = (value / bcr_result['summary']['total_benefits_pv']) * 100
            print(f"  {benefit_type.replace('_', ' ').title()}: £{value:,.0f} ({percentage:.1f}%)")

        return bcr_result

    def j59_gdp_multiplier_analysis(
        self,
        investment_amount: float = 10_000_000,
        target_lsoas: pd.DataFrame = None
    ) -> Dict:
        """
        J59: Calculate GDP multiplier effect of bus investment

        Args:
            investment_amount: Total investment (£)
            target_lsoas: LSOAs to analyze (if None, uses top underserved)

        Returns:
            GDP multiplier analysis
        """

        print(f"\n{'=' * 80}")
        print(f"J59: GDP Multiplier Analysis")
        print(f"{'=' * 80}\n")

        if target_lsoas is None:
            # Use top 10 underserved
            underserved = self.lsoa_data.nlargest(10, 'population')
            target_lsoas = underserved

        # ONS Regional Multipliers (based on input-output tables)
        # Transport sector multipliers by component
        multipliers = {
            'direct_gdp_ratio': 0.65,      # 65% of investment → direct GDP
            'indirect_multiplier': 0.45,    # Supply chain effects
            'induced_multiplier': 0.35,     # Household spending effects
            'productivity_multiplier': 0.28,  # Business productivity gains
            'agglomeration_factor': 0.25    # Economic density benefits (deprived areas)
        }

        # Calculate GDP impacts
        gdp_impacts = {
            'direct_gdp': investment_amount * multipliers['direct_gdp_ratio'],
            'indirect_gdp': investment_amount * multipliers['indirect_multiplier'],
            'induced_gdp': investment_amount * multipliers['induced_multiplier'],
        }

        # Business productivity (if business count available)
        if 'business_count' in target_lsoas.columns:
            total_businesses = target_lsoas['business_count'].sum()
            productivity_per_business = 2500  # £2.5k per business from improved access
            gdp_impacts['productivity_gains'] = total_businesses * productivity_per_business
        else:
            gdp_impacts['productivity_gains'] = investment_amount * 0.12  # Estimate

        # Employment income (new jobs created)
        new_drivers_needed = (investment_amount / 250000) * 0.5  # Buses × driver ratio
        avg_salary = 28000
        employment_multiplier = 2.1  # Total jobs (direct + indirect)
        gdp_impacts['employment_income'] = new_drivers_needed * employment_multiplier * avg_salary

        # Agglomeration effects (higher in deprived areas)
        avg_imd = target_lsoas['imd_decile'].mean() if 'imd_decile' in target_lsoas.columns else 5
        agglomeration_factor = multipliers['agglomeration_factor'] if avg_imd <= 4 else 0.15
        gdp_impacts['agglomeration_gdp'] = investment_amount * agglomeration_factor

        # Total GDP impact
        total_gdp_impact = sum(gdp_impacts.values())
        gdp_multiplier = total_gdp_impact / investment_amount

        # Regional breakdown
        if 'region' in target_lsoas.columns:
            regional_gdp = target_lsoas.groupby('region').agg({
                'population': 'sum'
            })
            regional_gdp['gdp_impact'] = (
                regional_gdp['population'] / target_lsoas['population'].sum()
            ) * total_gdp_impact
            regional_gdp_dict = regional_gdp['gdp_impact'].to_dict()
        else:
            regional_gdp_dict = {}

        result = {
            'investment_amount': investment_amount,
            'total_gdp_impact': total_gdp_impact,
            'gdp_multiplier': gdp_multiplier,
            'gdp_impact_breakdown': gdp_impacts,
            'regional_gdp_impact': regional_gdp_dict,
            'gdp_per_capita_increase': total_gdp_impact / target_lsoas['population'].sum(),
            'interpretation': f"Every £1 invested generates £{gdp_multiplier:.2f} in GDP"
        }

        # Print summary
        print(f"GDP MULTIPLIER RESULTS:")
        print(f"  Investment: £{investment_amount:,.0f}")
        print(f"  Total GDP Impact: £{total_gdp_impact:,.0f}")
        print(f"  GDP Multiplier: {gdp_multiplier:.2f}x")
        print(f"  Interpretation: {result['interpretation']}")
        print()

        print(f"GDP IMPACT BREAKDOWN:")
        for component, value in gdp_impacts.items():
            percentage = (value / total_gdp_impact) * 100
            print(f"  {component.replace('_', ' ').title()}: £{value:,.0f} ({percentage:.1f}%)")

        return result

    def j60_employment_impact_analysis(
        self,
        frequency_increase_pct: float = 0.20
    ) -> Dict:
        """
        J60: Calculate jobs created by 20% frequency increase

        Args:
            frequency_increase_pct: Service frequency increase (e.g., 0.20 = 20%)

        Returns:
            Employment impact analysis
        """

        print(f"\n{'=' * 80}")
        print(f"J60: Employment Impact Analysis ({frequency_increase_pct * 100:.0f}% Frequency Increase)")
        print(f"{'=' * 80}\n")

        # Current service baseline (from data)
        if 'routes' in self.lsoa_data.columns:
            current_routes = self.lsoa_data['routes'].sum()
        else:
            current_routes = 3578  # From project data

        # Estimate current trips
        avg_trips_per_route_per_day = 42
        current_trips_per_day = current_routes * avg_trips_per_route_per_day

        # Increased service
        new_trips = current_trips_per_day * frequency_increase_pct

        # Job creation calculation
        jobs_created = {
            # Direct transport jobs
            'bus_drivers': new_trips / 40,  # 40 trips per driver per day
            'supervisors': (new_trips / 40) * 0.10,  # 1 supervisor per 10 drivers

            # Support jobs
            'mechanics': (new_trips / 40) * 0.15,  # 1 mechanic per 6-7 drivers
            'admin_staff': (new_trips / 40) * 0.08,
            'customer_service': (new_trips / 40) * 0.05,

            # Indirect jobs (supply chain)
            'bus_manufacturing': (new_trips / 40) * 0.20,
            'fuel_supply': (new_trips / 40) * 0.05,
            'parts_suppliers': (new_trips / 40) * 0.10,

            # Induced jobs (multiplier effect)
            'retail_hospitality': (new_trips / 40) * 0.35,
            'other_services': (new_trips / 40) * 0.20
        }

        total_jobs = sum(jobs_created.values())
        direct_jobs = jobs_created['bus_drivers'] + jobs_created['supervisors']
        indirect_jobs = sum([
            jobs_created[k] for k in ['mechanics', 'admin_staff', 'customer_service',
                                      'bus_manufacturing', 'fuel_supply', 'parts_suppliers']
        ])
        induced_jobs = jobs_created['retail_hospitality'] + jobs_created['other_services']

        # Economic value
        avg_salary = 28000
        total_income_generated = total_jobs * avg_salary
        tax_revenue = total_income_generated * 0.25  # 25% effective tax rate

        # Regional distribution (based on population)
        if 'region' in self.lsoa_data.columns:
            regional_pop = self.lsoa_data.groupby('region')['population'].sum()
            regional_jobs = (regional_pop / regional_pop.sum() * total_jobs).to_dict()
        else:
            # Default UK distribution
            regional_jobs = {
                'London': total_jobs * 0.25,
                'South East': total_jobs * 0.15,
                'North West': total_jobs * 0.12,
                'West Midlands': total_jobs * 0.10,
                'Yorkshire and The Humber': total_jobs * 0.10,
                'East Midlands': total_jobs * 0.08,
                'South West': total_jobs * 0.08,
                'East of England': total_jobs * 0.07,
                'North East': total_jobs * 0.05
            }

        result = {
            'frequency_increase_pct': frequency_increase_pct * 100,
            'new_trips_per_day': new_trips,
            'total_jobs_created': int(total_jobs),
            'direct_jobs': int(direct_jobs),
            'indirect_jobs': int(indirect_jobs),
            'induced_jobs': int(induced_jobs),
            'jobs_breakdown': {k: int(v) for k, v in jobs_created.items()},
            'total_income_generated': total_income_generated,
            'tax_revenue_generated': tax_revenue,
            'regional_jobs': {k: int(v) for k, v in regional_jobs.items()},
            'employment_multiplier': total_jobs / direct_jobs
        }

        # Print summary
        print(f"EMPLOYMENT IMPACT RESULTS:")
        print(f"  Frequency Increase: {frequency_increase_pct * 100:.0f}%")
        print(f"  Total Jobs Created: {int(total_jobs):,}")
        print(f"    - Direct: {int(direct_jobs):,}")
        print(f"    - Indirect: {int(indirect_jobs):,}")
        print(f"    - Induced: {int(induced_jobs):,}")
        print(f"  Employment Multiplier: {result['employment_multiplier']:.2f}x")
        print(f"  Total Income Generated: £{total_income_generated:,.0f}")
        print(f"  Tax Revenue: £{tax_revenue:,.0f}")
        print()

        print(f"JOBS BY TYPE:")
        for job_type, count in sorted(jobs_created.items(), key=lambda x: x[1], reverse=True):
            print(f"  {job_type.replace('_', ' ').title()}: {int(count):,}")

        return result

    def j61_carbon_reduction_analysis(self) -> Dict:
        """
        J61: Calculate carbon emissions reduction potential

        Returns:
            Carbon reduction analysis for 3 scenarios
        """

        print(f"\n{'=' * 80}")
        print(f"J61: Carbon Emissions Reduction Analysis")
        print(f"{'=' * 80}\n")

        # Current bus network capacity
        if 'bus_stops' in self.lsoa_data.columns:
            total_bus_stops = self.lsoa_data['bus_stops'].sum()
        else:
            total_bus_stops = 3_040_885  # From project data

        avg_population_per_stop = 100  # Within 400m radius
        potential_bus_users = total_bus_stops * avg_population_per_stop

        # Modal shift scenarios
        modal_shift_scenarios = {
            'optimistic': 0.15,
            'realistic': 0.08,
            'conservative': 0.04
        }

        results = {}

        for scenario, shift_rate in modal_shift_scenarios.items():
            switchers = potential_bus_users * shift_rate
            avg_car_trips_per_year = 250
            avg_trip_distance_km = 12

            # Emissions (BEIS 2025 factors)
            car_emissions_kg_per_km = 0.171  # Average UK car
            bus_emissions_kg_per_passenger_km = 0.089

            # Total emissions
            car_emissions_total = switchers * avg_car_trips_per_year * avg_trip_distance_km * car_emissions_kg_per_km
            bus_emissions_total = switchers * avg_car_trips_per_year * avg_trip_distance_km * bus_emissions_kg_per_passenger_km
            emissions_saved_tonnes = (car_emissions_total - bus_emissions_total) / 1000

            # Monetize (BEIS carbon values)
            carbon_value_per_tonne = 250  # £250/tonne CO2
            carbon_value_30yr = emissions_saved_tonnes * carbon_value_per_tonne * 30

            # Additional environmental benefits
            air_quality_improvement = emissions_saved_tonnes * 120 * 30  # NOx/PM reduction
            noise_reduction_value = switchers * avg_car_trips_per_year * 0.15 * 30

            results[scenario] = {
                'modal_shift_percentage': shift_rate * 100,
                'people_switching': int(switchers),
                'car_trips_replaced_per_year': int(switchers * avg_car_trips_per_year),
                'co2_saved_tonnes_per_year': emissions_saved_tonnes,
                'co2_saved_30yr_tonnes': emissions_saved_tonnes * 30,
                'carbon_value_30yr': carbon_value_30yr,
                'air_quality_benefit': air_quality_improvement,
                'noise_reduction_benefit': noise_reduction_value,
                'total_environmental_benefit': carbon_value_30yr + air_quality_improvement + noise_reduction_value,
                'equivalent_cars_off_road': int(switchers * 0.85)
            }

        # Print summary
        print(f"CARBON REDUCTION RESULTS:\n")
        for scenario, data in results.items():
            print(f"{scenario.upper()} SCENARIO:")
            print(f"  Modal Shift: {data['modal_shift_percentage']:.1f}%")
            print(f"  People Switching: {data['people_switching']:,}")
            print(f"  CO2 Saved (annual): {data['co2_saved_tonnes_per_year']:,.0f} tonnes")
            print(f"  CO2 Saved (30-year): {data['co2_saved_30yr_tonnes']:,.0f} tonnes")
            print(f"  Carbon Value (30-year): £{data['carbon_value_30yr']:,.0f}")
            print(f"  Cars Off Road: {data['equivalent_cars_off_road']:,}")
            print()

        final_result = {
            'scenarios': results,
            'uk_transport_co2_target': 'Net Zero by 2050',
            'bus_contribution_to_target': f"{results['realistic']['co2_saved_30yr_tonnes'] / 1_000_000:.2f}M tonnes over 30 years"
        }

        return final_result

    def compute_all_category_j_questions(self, output_dir: str = 'analysis/spatial/outputs') -> Dict:
        """
        Compute all Category J questions and save results

        Args:
            output_dir: Directory to save results

        Returns:
            Complete Category J results
        """

        print(f"\n{'#' * 80}")
        print(f"# CATEGORY J: ADVANCED ECONOMIC IMPACT ANALYSIS")
        print(f"# Computing all 4 questions (J58-J61)")
        print(f"{'#' * 80}\n")

        results = {}

        # J58: BCR Analysis
        results['J58'] = self.j58_bcr_investment_analysis()

        # J59: GDP Multiplier
        results['J59'] = self.j59_gdp_multiplier_analysis()

        # J60: Employment Impact
        results['J60'] = self.j60_employment_impact_analysis()

        # J61: Carbon Reduction
        results['J61'] = self.j61_carbon_reduction_analysis()

        # Save results
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        output_file = output_path / f'category_j_economic_impact_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        # Convert numpy types to native Python for JSON serialization
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):
                return None
            else:
                return obj

        results_serializable = convert_types(results)

        with open(output_file, 'w') as f:
            json.dump(results_serializable, f, indent=2)

        print(f"\n{'=' * 80}")
        print(f"✅ Category J results saved to: {output_file}")
        print(f"{'=' * 80}\n")

        return results


# Main execution
if __name__ == '__main__':
    print("=" * 80)
    print("ECONOMIC IMPACT MODELING - CATEGORY J QUESTIONS")
    print("=" * 80)

    # Initialize analyzer
    analyzer = EconomicImpactAnalyzer()

    # Check for data file
    data_paths = [
        'data/processed/lsoa_integrated.parquet',
        'data/processed/spatial/lsoa_metrics.parquet',
    ]

    data_loaded = False
    for path in data_paths:
        if Path(path).exists():
            print(f"Loading data from: {path}")
            analyzer.load_data(path)
            data_loaded = True
            break

    if not data_loaded:
        print("⚠️  No LSOA data found. Creating sample data for demonstration.")

        # Create sample data
        sample_data = pd.DataFrame({
            'lsoa_code': [f'E0100000{i}' for i in range(1, 51)],
            'population': np.random.randint(1500, 3500, 50),
            'bus_stops': np.random.randint(2, 25, 50),
            'routes': np.random.randint(1, 8, 50),
            'imd_decile': np.random.randint(1, 11, 50),
            'unemployment_rate': np.random.uniform(4.0, 15.0, 50),
            'region': np.random.choice(['London', 'South East', 'North West'], 50)
        })

        analyzer.lsoa_data = sample_data
        print(f"✅ Created sample data: {len(sample_data)} LSOAs\n")

    # Run all Category J analyses
    results = analyzer.compute_all_category_j_questions()

    print("\n" + "=" * 80)
    print("✅ ECONOMIC IMPACT ANALYSIS COMPLETE")
    print("=" * 80)
