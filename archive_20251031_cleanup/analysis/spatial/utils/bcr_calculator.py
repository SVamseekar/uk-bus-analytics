"""
BCR (Benefit-Cost Ratio) Calculator
Implements UK Treasury Green Book methodology for transport appraisal
Following DfT Transport Analysis Guidance (TAG)

Author: UK Bus Analytics Project
Date: 2025-10-29
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class BCRCalculator:
    """
    Calculate Benefit-Cost Ratios for bus service improvements
    following UK Treasury Green Book and DfT TAG guidelines
    """

    # DfT TAG Appraisal Values (2025 prices)
    DFT_VALUES_2025 = {
        'commuting_time_value': 25.19,  # £/hour
        'leisure_time_value': 12.85,    # £/hour
        'business_time_value': 47.32,   # £/hour
        'accident_prevention': 1_850_000,  # £ per fatality prevented
        'carbon_value': 250,  # £/tonne CO2
        'air_quality_nox': 120,  # £/tonne NOx reduction
        'air_quality_pm': 180,  # £/tonne PM reduction
        'noise_reduction': 0.15,  # £ per trip
    }

    # Cost Parameters
    COST_FACTORS = {
        'bus_capex_per_vehicle': 250_000,  # £ per new bus
        'stop_infrastructure': 15_000,  # £ per new stop
        'annual_operating_cost_ratio': 0.12,  # 12% of CAPEX
        'maintenance_cost_ratio': 0.03,  # 3% of CAPEX annually
        'fuel_cost_per_km': 0.45,  # £/km
        'driver_salary_annual': 32_000,  # £/year
    }

    # Appraisal Parameters
    APPRAISAL_PERIOD = 30  # years (DfT standard)
    DISCOUNT_RATE = 0.035  # 3.5% (Green Book social discount rate)

    def __init__(self):
        """Initialize BCR calculator"""
        pass

    def calculate_present_value(self, annual_value: float, years: int = None) -> float:
        """
        Calculate present value of future cash flows
        Using Green Book discount rate (3.5% for years 0-30)

        Args:
            annual_value: Annual cost or benefit
            years: Number of years (default: APPRAISAL_PERIOD)

        Returns:
            Present value (discounted)
        """
        if years is None:
            years = self.APPRAISAL_PERIOD

        discount_factors = [(1 / (1 + self.DISCOUNT_RATE) ** year) for year in range(1, years + 1)]
        present_value = annual_value * sum(discount_factors)
        return present_value

    def calculate_investment_costs(
        self,
        lsoa_data: pd.DataFrame,
        investment_amount: float
    ) -> Dict[str, float]:
        """
        Calculate total costs for bus service improvement

        Args:
            lsoa_data: DataFrame with LSOA details
            investment_amount: Total investment (£)

        Returns:
            Dictionary of cost components
        """
        num_lsoas = len(lsoa_data)
        cost_per_lsoa = investment_amount / num_lsoas

        # Capital costs
        capital_costs = {
            'new_buses': cost_per_lsoa * 0.60,  # 60% on vehicles
            'infrastructure': cost_per_lsoa * 0.25,  # 25% on stops/depots
            'technology': cost_per_lsoa * 0.10,  # 10% on ticketing/real-time info
            'planning_design': cost_per_lsoa * 0.05,  # 5% on planning
        }

        total_capex = sum(capital_costs.values())

        # Operating costs (annual)
        annual_opex = {
            'vehicle_operating': total_capex * self.COST_FACTORS['annual_operating_cost_ratio'],
            'maintenance': total_capex * self.COST_FACTORS['maintenance_cost_ratio'],
            'driver_salaries': (total_capex / self.COST_FACTORS['bus_capex_per_vehicle']) * self.COST_FACTORS['driver_salary_annual'],
            'administration': total_capex * 0.08,  # 8% admin overhead
        }

        total_annual_opex = sum(annual_opex.values())

        # Present value of operating costs
        pv_opex = self.calculate_present_value(total_annual_opex)

        total_cost_pv = total_capex + pv_opex

        return {
            'capital_costs': capital_costs,
            'total_capex': total_capex,
            'annual_opex': annual_opex,
            'total_annual_opex': total_annual_opex,
            'pv_opex': pv_opex,
            'total_cost_pv': total_cost_pv,
        }

    def calculate_time_savings_benefits(
        self,
        lsoa_data: pd.DataFrame,
        adoption_rate: float = 0.25
    ) -> Dict[str, float]:
        """
        Calculate time savings benefits from improved bus service

        Args:
            lsoa_data: DataFrame with population data
            adoption_rate: Proportion of population using new service

        Returns:
            Time savings benefits (annual and PV)
        """
        total_population = lsoa_data['population'].sum()
        new_passengers = total_population * adoption_rate

        # Trip assumptions
        trips_per_passenger_per_year = 250  # Commuting days
        time_saved_per_trip_hours = 0.25  # 15 minutes saved per trip

        # Benefit calculation
        # Assume 80% commuting, 20% leisure
        commuting_passengers = new_passengers * 0.80
        leisure_passengers = new_passengers * 0.20

        annual_time_savings = (
            commuting_passengers * trips_per_passenger_per_year * time_saved_per_trip_hours * self.DFT_VALUES_2025['commuting_time_value'] +
            leisure_passengers * trips_per_passenger_per_year * time_saved_per_trip_hours * self.DFT_VALUES_2025['leisure_time_value']
        )

        pv_time_savings = self.calculate_present_value(annual_time_savings)

        return {
            'new_passengers': new_passengers,
            'annual_time_savings_benefit': annual_time_savings,
            'pv_time_savings_benefit': pv_time_savings,
            'time_saved_hours_per_year': new_passengers * trips_per_passenger_per_year * time_saved_per_trip_hours
        }

    def calculate_carbon_benefits(
        self,
        lsoa_data: pd.DataFrame,
        adoption_rate: float = 0.25,
        modal_shift_from_car: float = 0.70
    ) -> Dict[str, float]:
        """
        Calculate carbon emission reduction benefits

        Args:
            lsoa_data: DataFrame with population data
            adoption_rate: Proportion using new service
            modal_shift_from_car: Proportion switching from car to bus

        Returns:
            Carbon benefit calculations
        """
        total_population = lsoa_data['population'].sum()
        new_passengers = total_population * adoption_rate
        car_switchers = new_passengers * modal_shift_from_car

        # Emissions (kg CO2 per km)
        car_emissions_per_km = 0.171  # Average UK car
        bus_emissions_per_passenger_km = 0.089  # Per passenger

        # Trip assumptions
        trips_per_year = 250
        avg_trip_distance_km = 12

        # Annual CO2 saved
        car_emissions_annual = car_switchers * trips_per_year * avg_trip_distance_km * car_emissions_per_km
        bus_emissions_annual = car_switchers * trips_per_year * avg_trip_distance_km * bus_emissions_per_passenger_km
        co2_saved_tonnes_annual = (car_emissions_annual - bus_emissions_annual) / 1000

        # Monetize carbon savings
        annual_carbon_benefit = co2_saved_tonnes_annual * self.DFT_VALUES_2025['carbon_value']
        pv_carbon_benefit = self.calculate_present_value(annual_carbon_benefit)

        return {
            'car_switchers': car_switchers,
            'co2_saved_tonnes_annual': co2_saved_tonnes_annual,
            'annual_carbon_benefit': annual_carbon_benefit,
            'pv_carbon_benefit': pv_carbon_benefit,
        }

    def calculate_health_benefits(
        self,
        lsoa_data: pd.DataFrame,
        adoption_rate: float = 0.25
    ) -> Dict[str, float]:
        """
        Calculate health benefits from reduced air pollution and active travel

        Args:
            lsoa_data: DataFrame with population data
            adoption_rate: Proportion using new service

        Returns:
            Health benefit calculations
        """
        total_population = lsoa_data['population'].sum()
        new_passengers = total_population * adoption_rate

        # Health benefit components
        # 1. Air quality improvement (reduced car emissions)
        air_quality_benefit_per_passenger = 45  # £/passenger/year

        # 2. Active travel (walking to bus stops increases physical activity)
        active_travel_benefit_per_passenger = 28  # £/passenger/year

        annual_health_benefit = new_passengers * (air_quality_benefit_per_passenger + active_travel_benefit_per_passenger)
        pv_health_benefit = self.calculate_present_value(annual_health_benefit)

        return {
            'annual_health_benefit': annual_health_benefit,
            'pv_health_benefit': pv_health_benefit,
            'air_quality_component': new_passengers * air_quality_benefit_per_passenger,
            'active_travel_component': new_passengers * active_travel_benefit_per_passenger,
        }

    def calculate_agglomeration_benefits(
        self,
        total_cost_pv: float,
        lsoa_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate agglomeration (economic density) benefits

        Args:
            total_cost_pv: Total project cost (present value)
            lsoa_data: DataFrame with LSOA details

        Returns:
            Agglomeration benefit calculations
        """
        # Agglomeration elasticity (DfT TAG guidance)
        # Higher in deprived areas (greater potential for economic growth)
        avg_imd_decile = lsoa_data['imd_decile'].mean() if 'imd_decile' in lsoa_data.columns else 5

        if avg_imd_decile <= 3:
            agglomeration_factor = 0.20  # 20% for deprived areas
        elif avg_imd_decile <= 7:
            agglomeration_factor = 0.15  # 15% for mid-range
        else:
            agglomeration_factor = 0.10  # 10% for affluent areas

        agglomeration_benefit = total_cost_pv * agglomeration_factor

        return {
            'agglomeration_factor': agglomeration_factor,
            'agglomeration_benefit': agglomeration_benefit,
            'avg_imd_decile': avg_imd_decile
        }

    def calculate_employment_access_benefits(
        self,
        lsoa_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate benefits from improved access to employment

        Args:
            lsoa_data: DataFrame with unemployment data

        Returns:
            Employment access benefit calculations
        """
        if 'unemployment_rate' not in lsoa_data.columns:
            return {'annual_employment_benefit': 0, 'pv_employment_benefit': 0}

        total_unemployed = (lsoa_data['population'] * lsoa_data['unemployment_rate'] / 100).sum()

        # Assume 5% of unemployed gain employment due to improved transport access
        employment_gain_rate = 0.05
        new_jobs = total_unemployed * employment_gain_rate

        # Average salary benefit
        avg_uk_salary = 28_000  # £/year
        annual_employment_benefit = new_jobs * avg_uk_salary * 0.75  # 75% gross value of employment

        pv_employment_benefit = self.calculate_present_value(annual_employment_benefit)

        return {
            'total_unemployed': total_unemployed,
            'new_jobs_created': new_jobs,
            'annual_employment_benefit': annual_employment_benefit,
            'pv_employment_benefit': pv_employment_benefit,
        }

    def calculate_accident_reduction_benefits(
        self,
        lsoa_data: pd.DataFrame,
        adoption_rate: float = 0.25,
        modal_shift_from_car: float = 0.70
    ) -> Dict[str, float]:
        """
        Calculate benefits from reduced road accidents

        Args:
            lsoa_data: DataFrame with population data
            adoption_rate: Proportion using new service
            modal_shift_from_car: Proportion switching from car

        Returns:
            Accident reduction benefit calculations
        """
        total_population = lsoa_data['population'].sum()
        new_passengers = total_population * adoption_rate
        car_switchers = new_passengers * modal_shift_from_car

        # Accident statistics
        trips_per_year = 250
        accident_rate_per_million_car_km = 5.6  # UK average
        avg_trip_distance_km = 12

        total_car_km_avoided = car_switchers * trips_per_year * avg_trip_distance_km
        accidents_avoided = (total_car_km_avoided / 1_000_000) * accident_rate_per_million_car_km

        # Average cost per accident (mix of fatal, serious, slight)
        avg_accident_cost = 85_000  # £ (weighted average from DfT)

        annual_accident_benefit = accidents_avoided * avg_accident_cost
        pv_accident_benefit = self.calculate_present_value(annual_accident_benefit)

        return {
            'accidents_avoided_annual': accidents_avoided,
            'annual_accident_benefit': annual_accident_benefit,
            'pv_accident_benefit': pv_accident_benefit,
        }

    def calculate_full_bcr(
        self,
        lsoa_data: pd.DataFrame,
        investment_amount: float = 10_000_000,
        adoption_rate: float = 0.25,
        modal_shift_from_car: float = 0.70
    ) -> Dict:
        """
        Calculate comprehensive BCR analysis

        Args:
            lsoa_data: DataFrame with LSOA details (must include: population, imd_decile, unemployment_rate)
            investment_amount: Total investment (£)
            adoption_rate: Proportion of population using service
            modal_shift_from_car: Proportion switching from car

        Returns:
            Complete BCR analysis with all components
        """

        # Validate required columns
        required_cols = ['population']
        missing_cols = [col for col in required_cols if col not in lsoa_data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Calculate costs
        costs = self.calculate_investment_costs(lsoa_data, investment_amount)

        # Calculate benefits
        time_savings = self.calculate_time_savings_benefits(lsoa_data, adoption_rate)
        carbon = self.calculate_carbon_benefits(lsoa_data, adoption_rate, modal_shift_from_car)
        health = self.calculate_health_benefits(lsoa_data, adoption_rate)
        agglomeration = self.calculate_agglomeration_benefits(costs['total_cost_pv'], lsoa_data)
        employment = self.calculate_employment_access_benefits(lsoa_data)
        accidents = self.calculate_accident_reduction_benefits(lsoa_data, adoption_rate, modal_shift_from_car)

        # Total benefits
        total_benefits_pv = (
            time_savings['pv_time_savings_benefit'] +
            carbon['pv_carbon_benefit'] +
            health['pv_health_benefit'] +
            agglomeration['agglomeration_benefit'] +
            employment['pv_employment_benefit'] +
            accidents['pv_accident_benefit']
        )

        # BCR calculation
        bcr = total_benefits_pv / costs['total_cost_pv']
        npv = total_benefits_pv - costs['total_cost_pv']

        # Recommendation based on DfT guidance
        if bcr >= 2.0:
            recommendation = 'HIGH VALUE FOR MONEY'
            priority = 'HIGH'
        elif bcr >= 1.5:
            recommendation = 'MEDIUM-HIGH VALUE FOR MONEY'
            priority = 'MEDIUM-HIGH'
        elif bcr >= 1.0:
            recommendation = 'LOW-MEDIUM VALUE FOR MONEY'
            priority = 'MEDIUM'
        else:
            recommendation = 'POOR VALUE FOR MONEY'
            priority = 'LOW'

        return {
            'summary': {
                'investment_amount': investment_amount,
                'num_lsoas': len(lsoa_data),
                'total_population_served': lsoa_data['population'].sum(),
                'total_cost_pv': costs['total_cost_pv'],
                'total_benefits_pv': total_benefits_pv,
                'bcr': bcr,
                'npv': npv,
                'recommendation': recommendation,
                'priority': priority,
            },
            'costs': costs,
            'benefits': {
                'time_savings': time_savings,
                'carbon': carbon,
                'health': health,
                'agglomeration': agglomeration,
                'employment': employment,
                'accidents': accidents,
            },
            'benefit_breakdown_pv': {
                'time_savings': time_savings['pv_time_savings_benefit'],
                'carbon': carbon['pv_carbon_benefit'],
                'health': health['pv_health_benefit'],
                'agglomeration': agglomeration['agglomeration_benefit'],
                'employment': employment['pv_employment_benefit'],
                'accidents': accidents['pv_accident_benefit'],
            },
            'methodology': {
                'appraisal_period_years': self.APPRAISAL_PERIOD,
                'discount_rate': self.DISCOUNT_RATE,
                'framework': 'UK Treasury Green Book + DfT TAG',
                'values_year': '2025 prices',
            }
        }


# Example usage
if __name__ == '__main__':
    # Example LSOA data
    example_data = pd.DataFrame({
        'lsoa_code': ['E01000001', 'E01000002', 'E01000003'],
        'population': [2000, 2500, 1800],
        'imd_decile': [2, 3, 1],
        'unemployment_rate': [8.5, 9.2, 12.1]
    })

    calculator = BCRCalculator()
    result = calculator.calculate_full_bcr(
        lsoa_data=example_data,
        investment_amount=3_000_000  # £3M for 3 LSOAs
    )

    print("=" * 80)
    print("BCR CALCULATION SUMMARY")
    print("=" * 80)
    print(f"Investment Amount: £{result['summary']['investment_amount']:,.0f}")
    print(f"Total Cost (PV): £{result['summary']['total_cost_pv']:,.0f}")
    print(f"Total Benefits (PV): £{result['summary']['total_benefits_pv']:,.0f}")
    print(f"\nBCR: {result['summary']['bcr']:.2f}")
    print(f"NPV: £{result['summary']['npv']:,.0f}")
    print(f"\nRecommendation: {result['summary']['recommendation']}")
    print(f"Priority: {result['summary']['priority']}")
    print("=" * 80)
