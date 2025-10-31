"""
Policy Scenario Simulator
Interactive "what-if" analysis for government policy decisions

Scenarios Supported:
1. Fare Cap Impact (£1, £2, £3)
2. Frequency Increase (10%, 20%, 30%)
3. Coverage Expansion (5%, 10%, 15%)
4. Combined Multi-Policy Scenarios

Output: BCR, Ridership Impact, Revenue Analysis, Government Subsidy Required

Author: UK Bus Analytics Project
Date: 2025-10-29
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple
from datetime import datetime

from analysis.spatial.utils.bcr_calculator import BCRCalculator


class PolicyScenarioSimulator:
    """
    Simulate policy interventions and calculate impacts
    """

    # Baseline UK bus statistics (2025)
    BASELINE = {
        'avg_fare': 2.80,  # £ average single fare
        'annual_trips_per_capita': 68,  # UK average
        'total_bus_passengers_uk': 3_500_000_000,  # Annual journeys
        'operator_revenue_uk': 7_200_000_000,  # £7.2B annual revenue
        'government_subsidy_uk': 2_500_000_000,  # £2.5B subsidy
        'avg_trip_distance_km': 6.5,
    }

    # Elasticity parameters (from DfT research)
    ELASTICITIES = {
        'fare_elasticity': -0.40,  # -0.4: 10% fare decrease → 4% ridership increase
        'frequency_elasticity': 0.40,  # 0.4: 10% frequency increase → 4% ridership increase
        'coverage_elasticity': 0.50,  # 0.5: 10% coverage increase → 5% ridership increase
    }

    def __init__(self, lsoa_data: pd.DataFrame = None):
        """
        Initialize policy simulator

        Args:
            lsoa_data: LSOA-level data for regional analysis
        """
        self.lsoa_data = lsoa_data
        self.bcr_calculator = BCRCalculator()

    def simulate_fare_cap(
        self,
        fare_cap: float,
        regions: List[str] = None
    ) -> Dict:
        """
        Simulate fare cap policy impact

        Args:
            fare_cap: Maximum fare (£)
            regions: Regions to apply policy (None = nationwide)

        Returns:
            Policy impact analysis
        """

        print(f"\n{'=' * 80}")
        print(f"POLICY SCENARIO: £{fare_cap:.2f} Fare Cap")
        print(f"{'=' * 80}\n")

        baseline_fare = self.BASELINE['avg_fare']
        fare_reduction_pct = (baseline_fare - fare_cap) / baseline_fare

        # Ridership impact (using fare elasticity)
        ridership_change_pct = fare_reduction_pct * self.ELASTICITIES['fare_elasticity']
        new_trips = self.BASELINE['total_bus_passengers_uk'] * (1 + ridership_change_pct)
        additional_trips = new_trips - self.BASELINE['total_bus_passengers_uk']

        # Revenue impact
        # Old revenue: baseline fare × baseline trips
        # New revenue: capped fare × new trips
        baseline_revenue = self.BASELINE['operator_revenue_uk']
        new_revenue = (fare_cap / baseline_fare) * baseline_revenue * (1 + ridership_change_pct)
        revenue_loss = baseline_revenue - new_revenue

        # Government subsidy required
        current_subsidy = self.BASELINE['government_subsidy_uk']
        additional_subsidy_needed = revenue_loss
        total_subsidy_required = current_subsidy + additional_subsidy_needed

        # Economic benefits (BCR components)
        # Time savings from reduced waiting (more passengers = better frequencies)
        time_savings_per_passenger = 0.20  # £ per trip
        time_savings_benefit = additional_trips * time_savings_per_passenger

        # Social inclusion benefits
        social_inclusion_benefit = additional_trips * 0.35  # £0.35 per trip

        # Carbon savings (car-to-bus shift)
        modal_shift_rate = 0.30  # 30% of new trips from car switchers
        car_trips_replaced = additional_trips * modal_shift_rate
        carbon_savings_kg = car_trips_replaced * self.BASELINE['avg_trip_distance_km'] * 0.082  # Net CO2 saving
        carbon_benefit = (carbon_savings_kg / 1000) * 250  # £250/tonne

        total_benefits_annual = time_savings_benefit + social_inclusion_benefit + carbon_benefit

        # 10-year BCR (simplified)
        total_cost_10yr = additional_subsidy_needed * 10
        total_benefits_10yr = total_benefits_annual * 10
        bcr = total_benefits_10yr / total_cost_10yr if total_cost_10yr > 0 else 0

        result = {
            'policy': f'£{fare_cap:.2f} Fare Cap',
            'baseline_fare': baseline_fare,
            'fare_reduction_pct': fare_reduction_pct * 100,
            'ridership': {
                'baseline_trips': self.BASELINE['total_bus_passengers_uk'],
                'new_trips': new_trips,
                'additional_trips': additional_trips,
                'ridership_change_pct': ridership_change_pct * 100,
            },
            'revenue': {
                'baseline_revenue': baseline_revenue,
                'new_revenue': new_revenue,
                'revenue_loss': revenue_loss,
            },
            'subsidy': {
                'current_subsidy': current_subsidy,
                'additional_subsidy_needed': additional_subsidy_needed,
                'total_subsidy_required': total_subsidy_required,
                'subsidy_increase_pct': (additional_subsidy_needed / current_subsidy) * 100,
            },
            'benefits': {
                'time_savings_benefit': time_savings_benefit,
                'social_inclusion_benefit': social_inclusion_benefit,
                'carbon_benefit': carbon_benefit,
                'total_benefits_annual': total_benefits_annual,
            },
            'bcr_10yr': bcr,
            'recommendation': self._get_recommendation(bcr),
        }

        # Print summary
        print(f"RIDERSHIP IMPACT:")
        print(f"  Baseline Trips: {result['ridership']['baseline_trips']:,.0f}")
        print(f"  New Trips: {result['ridership']['new_trips']:,.0f}")
        print(f"  Additional Trips: {result['ridership']['additional_trips']:,.0f} (+{result['ridership']['ridership_change_pct']:.1f}%)")
        print()

        print(f"REVENUE IMPACT:")
        print(f"  Baseline Revenue: £{result['revenue']['baseline_revenue']:,.0f}")
        print(f"  New Revenue: £{result['revenue']['new_revenue']:,.0f}")
        print(f"  Revenue Loss: £{result['revenue']['revenue_loss']:,.0f}")
        print()

        print(f"SUBSIDY REQUIREMENT:")
        print(f"  Current Subsidy: £{result['subsidy']['current_subsidy']:,.0f}")
        print(f"  Additional Subsidy Needed: £{result['subsidy']['additional_subsidy_needed']:,.0f}")
        print(f"  Total Subsidy Required: £{result['subsidy']['total_subsidy_required']:,.0f}")
        print(f"  Subsidy Increase: +{result['subsidy']['subsidy_increase_pct']:.1f}%")
        print()

        print(f"ECONOMIC BENEFITS (Annual):")
        print(f"  Time Savings: £{result['benefits']['time_savings_benefit']:,.0f}")
        print(f"  Social Inclusion: £{result['benefits']['social_inclusion_benefit']:,.0f}")
        print(f"  Carbon Savings: £{result['benefits']['carbon_benefit']:,.0f}")
        print(f"  Total Benefits: £{result['benefits']['total_benefits_annual']:,.0f}")
        print()

        print(f"10-YEAR BCR: {result['bcr_10yr']:.2f}")
        print(f"RECOMMENDATION: {result['recommendation']}")

        return result

    def simulate_frequency_increase(
        self,
        frequency_increase_pct: float,
        regions: List[str] = None
    ) -> Dict:
        """
        Simulate service frequency increase

        Args:
            frequency_increase_pct: Frequency increase (e.g., 0.20 = 20%)
            regions: Regions to apply policy

        Returns:
            Policy impact analysis
        """

        print(f"\n{'=' * 80}")
        print(f"POLICY SCENARIO: {frequency_increase_pct * 100:.0f}% Frequency Increase")
        print(f"{'=' * 80}\n")

        # Ridership impact
        ridership_change_pct = frequency_increase_pct * self.ELASTICITIES['frequency_elasticity']
        new_trips = self.BASELINE['total_bus_passengers_uk'] * (1 + ridership_change_pct)
        additional_trips = new_trips - self.BASELINE['total_bus_passengers_uk']

        # Cost calculation
        # More frequency = more buses = more drivers = more fuel
        baseline_opex = 5_000_000_000  # £5B UK bus operating costs
        additional_opex = baseline_opex * frequency_increase_pct * 1.1  # 10% efficiency gain

        # Revenue increase (more trips × avg fare)
        avg_fare = self.BASELINE['avg_fare']
        additional_revenue = additional_trips * avg_fare

        # Net subsidy requirement
        net_subsidy_change = additional_opex - additional_revenue

        # Benefits
        # Reduced waiting time
        avg_waiting_reduction_minutes = (1 / (1 + frequency_increase_pct)) - 1  # Shorter waits
        waiting_time_value = 12.85  # £/hour
        waiting_time_benefit = self.BASELINE['total_bus_passengers_uk'] * abs(avg_waiting_reduction_minutes) / 60 * waiting_time_value * 250  # trips/year

        # Reliability improvement
        reliability_benefit = new_trips * 0.25  # £0.25 per trip reliability value

        # Carbon savings (induced trips replace car journeys)
        car_trips_replaced = additional_trips * 0.35
        carbon_savings_kg = car_trips_replaced * self.BASELINE['avg_trip_distance_km'] * 0.082
        carbon_benefit = (carbon_savings_kg / 1000) * 250

        total_benefits_annual = waiting_time_benefit + reliability_benefit + carbon_benefit

        # 10-year BCR
        total_cost_10yr = additional_opex * 10
        total_benefits_10yr = total_benefits_annual * 10
        bcr = total_benefits_10yr / total_cost_10yr if total_cost_10yr > 0 else 0

        result = {
            'policy': f'{frequency_increase_pct * 100:.0f}% Frequency Increase',
            'frequency_increase_pct': frequency_increase_pct * 100,
            'ridership': {
                'baseline_trips': self.BASELINE['total_bus_passengers_uk'],
                'new_trips': new_trips,
                'additional_trips': additional_trips,
                'ridership_change_pct': ridership_change_pct * 100,
            },
            'costs': {
                'baseline_opex': baseline_opex,
                'additional_opex': additional_opex,
                'additional_revenue': additional_revenue,
                'net_subsidy_change': net_subsidy_change,
            },
            'benefits': {
                'waiting_time_benefit': waiting_time_benefit,
                'reliability_benefit': reliability_benefit,
                'carbon_benefit': carbon_benefit,
                'total_benefits_annual': total_benefits_annual,
            },
            'bcr_10yr': bcr,
            'recommendation': self._get_recommendation(bcr),
        }

        # Print summary
        print(f"RIDERSHIP IMPACT:")
        print(f"  Additional Trips: {result['ridership']['additional_trips']:,.0f} (+{result['ridership']['ridership_change_pct']:.1f}%)")
        print()

        print(f"COST-REVENUE IMPACT:")
        print(f"  Additional Operating Cost: £{result['costs']['additional_opex']:,.0f}")
        print(f"  Additional Revenue: £{result['costs']['additional_revenue']:,.0f}")
        print(f"  Net Subsidy Change: £{result['costs']['net_subsidy_change']:,.0f}")
        print()

        print(f"ECONOMIC BENEFITS (Annual):")
        print(f"  Waiting Time Savings: £{result['benefits']['waiting_time_benefit']:,.0f}")
        print(f"  Reliability Improvement: £{result['benefits']['reliability_benefit']:,.0f}")
        print(f"  Carbon Savings: £{result['benefits']['carbon_benefit']:,.0f}")
        print(f"  Total Benefits: £{result['benefits']['total_benefits_annual']:,.0f}")
        print()

        print(f"10-YEAR BCR: {result['bcr_10yr']:.2f}")
        print(f"RECOMMENDATION: {result['recommendation']}")

        return result

    def simulate_coverage_expansion(
        self,
        coverage_increase_pct: float,
        target_underserved: bool = True
    ) -> Dict:
        """
        Simulate network coverage expansion

        Args:
            coverage_increase_pct: Coverage increase (e.g., 0.10 = 10%)
            target_underserved: Focus on underserved areas

        Returns:
            Policy impact analysis
        """

        print(f"\n{'=' * 80}")
        print(f"POLICY SCENARIO: {coverage_increase_pct * 100:.0f}% Coverage Expansion")
        if target_underserved:
            print("(Targeting Underserved Areas)")
        print(f"{'=' * 80}\n")

        # Ridership impact
        ridership_change_pct = coverage_increase_pct * self.ELASTICITIES['coverage_elasticity']
        new_trips = self.BASELINE['total_bus_passengers_uk'] * (1 + ridership_change_pct)
        additional_trips = new_trips - self.BASELINE['total_bus_passengers_uk']

        # Investment cost
        cost_per_new_stop = 15_000  # Infrastructure
        cost_per_new_route = 500_000  # Vehicles + planning
        current_stops = 400_000  # UK estimate
        current_routes = 35_000  # UK estimate

        new_stops = current_stops * coverage_increase_pct
        new_routes = current_routes * coverage_increase_pct * 0.5  # Fewer new routes needed

        capex = (new_stops * cost_per_new_stop) + (new_routes * cost_per_new_route)

        # Operating costs
        additional_annual_opex = capex * 0.15  # 15% of CAPEX annually

        # Revenue
        additional_revenue = additional_trips * self.BASELINE['avg_fare']

        # Net subsidy
        net_annual_subsidy = additional_annual_opex - additional_revenue

        # Benefits
        # Social inclusion (connecting isolated communities)
        if target_underserved:
            social_inclusion_multiplier = 1.5  # 50% higher value in deprived areas
        else:
            social_inclusion_multiplier = 1.0

        social_inclusion_benefit = additional_trips * 0.50 * social_inclusion_multiplier

        # Employment access
        employment_benefit = additional_trips * 0.30 * 250  # Access to jobs

        # Carbon savings
        car_trips_replaced = additional_trips * 0.40  # Higher modal shift for new routes
        carbon_savings_kg = car_trips_replaced * self.BASELINE['avg_trip_distance_km'] * 0.082
        carbon_benefit = (carbon_savings_kg / 1000) * 250

        # Agglomeration benefits (economic density)
        agglomeration_benefit = capex * 0.20  # 20% of investment

        total_benefits_annual = social_inclusion_benefit + employment_benefit + carbon_benefit + (agglomeration_benefit / 30)  # Spread over 30 years

        # 30-year BCR (infrastructure projects)
        total_cost_30yr = capex + (additional_annual_opex * 30)
        total_benefits_30yr = (total_benefits_annual * 30) + agglomeration_benefit
        bcr = total_benefits_30yr / total_cost_30yr if total_cost_30yr > 0 else 0

        result = {
            'policy': f'{coverage_increase_pct * 100:.0f}% Coverage Expansion',
            'coverage_increase_pct': coverage_increase_pct * 100,
            'target_underserved': target_underserved,
            'infrastructure': {
                'new_stops': new_stops,
                'new_routes': new_routes,
                'capex': capex,
            },
            'ridership': {
                'baseline_trips': self.BASELINE['total_bus_passengers_uk'],
                'new_trips': new_trips,
                'additional_trips': additional_trips,
                'ridership_change_pct': ridership_change_pct * 100,
            },
            'costs': {
                'capex': capex,
                'additional_annual_opex': additional_annual_opex,
                'additional_revenue': additional_revenue,
                'net_annual_subsidy': net_annual_subsidy,
            },
            'benefits': {
                'social_inclusion_benefit': social_inclusion_benefit,
                'employment_benefit': employment_benefit,
                'carbon_benefit': carbon_benefit,
                'agglomeration_benefit': agglomeration_benefit,
                'total_benefits_annual': total_benefits_annual,
            },
            'bcr_30yr': bcr,
            'recommendation': self._get_recommendation(bcr),
        }

        # Print summary
        print(f"INFRASTRUCTURE:")
        print(f"  New Stops: {result['infrastructure']['new_stops']:,.0f}")
        print(f"  New Routes: {result['infrastructure']['new_routes']:,.0f}")
        print(f"  Capital Investment: £{result['infrastructure']['capex']:,.0f}")
        print()

        print(f"RIDERSHIP IMPACT:")
        print(f"  Additional Trips: {result['ridership']['additional_trips']:,.0f} (+{result['ridership']['ridership_change_pct']:.1f}%)")
        print()

        print(f"COST-REVENUE IMPACT:")
        print(f"  CAPEX: £{result['costs']['capex']:,.0f}")
        print(f"  Annual OPEX: £{result['costs']['additional_annual_opex']:,.0f}")
        print(f"  Annual Revenue: £{result['costs']['additional_revenue']:,.0f}")
        print(f"  Net Annual Subsidy: £{result['costs']['net_annual_subsidy']:,.0f}")
        print()

        print(f"ECONOMIC BENEFITS (Annual):")
        print(f"  Social Inclusion: £{result['benefits']['social_inclusion_benefit']:,.0f}")
        print(f"  Employment Access: £{result['benefits']['employment_benefit']:,.0f}")
        print(f"  Carbon Savings: £{result['benefits']['carbon_benefit']:,.0f}")
        print(f"  Total Annual Benefits: £{result['benefits']['total_benefits_annual']:,.0f}")
        print()

        print(f"30-YEAR BCR: {result['bcr_30yr']:.2f}")
        print(f"RECOMMENDATION: {result['recommendation']}")

        return result

    def simulate_combined_scenario(
        self,
        fare_cap: float = None,
        frequency_increase_pct: float = None,
        coverage_increase_pct: float = None
    ) -> Dict:
        """
        Simulate combined multi-policy scenario

        Args:
            fare_cap: Fare cap (£)
            frequency_increase_pct: Frequency increase
            coverage_increase_pct: Coverage increase

        Returns:
            Combined policy impact
        """

        print(f"\n{'=' * 80}")
        print(f"COMBINED POLICY SCENARIO")
        print(f"{'=' * 80}\n")

        policies = []
        if fare_cap:
            policies.append(f"£{fare_cap:.2f} Fare Cap")
        if frequency_increase_pct:
            policies.append(f"{frequency_increase_pct * 100:.0f}% Frequency Increase")
        if coverage_increase_pct:
            policies.append(f"{coverage_increase_pct * 100:.0f}% Coverage Expansion")

        print(f"Policies: {' + '.join(policies)}\n")

        # Run individual scenarios
        results = {}
        if fare_cap:
            results['fare_cap'] = self.simulate_fare_cap(fare_cap)
        if frequency_increase_pct:
            results['frequency'] = self.simulate_frequency_increase(frequency_increase_pct)
        if coverage_increase_pct:
            results['coverage'] = self.simulate_coverage_expansion(coverage_increase_pct)

        # Aggregate impacts (with interaction effects)
        interaction_factor = 1.15  # 15% synergy benefit from combined policies

        total_ridership_change = sum([r['ridership']['additional_trips'] for r in results.values()])
        total_ridership_change *= interaction_factor

        total_costs = sum([
            r.get('costs', {}).get('additional_opex', 0) +
            r.get('costs', {}).get('capex', 0) +
            r.get('subsidy', {}).get('additional_subsidy_needed', 0)
            for r in results.values()
        ])

        total_benefits = sum([r['benefits']['total_benefits_annual'] for r in results.values()])
        total_benefits *= interaction_factor

        combined_bcr = (total_benefits * 10) / (total_costs * 10) if total_costs > 0 else 0

        combined_result = {
            'policies': policies,
            'individual_results': results,
            'combined_impact': {
                'total_additional_trips': total_ridership_change,
                'total_costs_annual': total_costs,
                'total_benefits_annual': total_benefits,
                'interaction_factor': interaction_factor,
                'combined_bcr_10yr': combined_bcr,
                'recommendation': self._get_recommendation(combined_bcr),
            }
        }

        print(f"\nCOMBINED IMPACT:")
        print(f"  Total Additional Trips: {total_ridership_change:,.0f}")
        print(f"  Total Annual Costs: £{total_costs:,.0f}")
        print(f"  Total Annual Benefits: £{total_benefits:,.0f}")
        print(f"  Synergy Factor: {interaction_factor:.2f}x")
        print(f"  Combined BCR: {combined_bcr:.2f}")
        print(f"  Recommendation: {combined_result['combined_impact']['recommendation']}")

        return combined_result

    def _get_recommendation(self, bcr: float) -> str:
        """Get policy recommendation based on BCR"""
        if bcr >= 2.0:
            return 'STRONGLY RECOMMENDED - High Value for Money'
        elif bcr >= 1.5:
            return 'RECOMMENDED - Good Value for Money'
        elif bcr >= 1.0:
            return 'NEUTRAL - Marginal Value for Money'
        else:
            return 'NOT RECOMMENDED - Poor Value for Money'


# Main execution
if __name__ == '__main__':
    print("=" * 80)
    print("POLICY SCENARIO SIMULATOR")
    print("=" * 80)

    simulator = PolicyScenarioSimulator()

    # Scenario 1: £2 Fare Cap
    result_fare = simulator.simulate_fare_cap(fare_cap=2.00)

    # Scenario 2: 20% Frequency Increase
    result_freq = simulator.simulate_frequency_increase(frequency_increase_pct=0.20)

    # Scenario 3: 10% Coverage Expansion
    result_coverage = simulator.simulate_coverage_expansion(coverage_increase_pct=0.10, target_underserved=True)

    # Scenario 4: Combined Policy
    result_combined = simulator.simulate_combined_scenario(
        fare_cap=2.00,
        frequency_increase_pct=0.20,
        coverage_increase_pct=0.10
    )

    print("\n" + "=" * 80)
    print("✅ POLICY SCENARIO ANALYSIS COMPLETE")
    print("=" * 80)
