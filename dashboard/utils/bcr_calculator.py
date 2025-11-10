"""
BCR (Benefit-Cost Ratio) Calculator
Implements UK Treasury Green Book methodology for transport appraisal
Following DfT Transport Analysis Guidance (TAG) 2024

Updated: November 10, 2025
Author: UK Bus Analytics Platform - Category J Implementation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class BCRCalculator:
    """
    Calculate Benefit-Cost Ratios for bus service improvements
    following UK Treasury Green Book and DfT TAG 2024 guidelines
    """

    # DfT TAG Appraisal Values (2024 official prices)
    # Source: DfT TAG Data Book May 2024
    DFT_VALUES_2024 = {
        'bus_commuting': 9.85,      # £/hour (TAG A1.3 Table 2 - bus commuting)
        'car_commuting': 12.65,     # £/hour (TAG A1.3 Table 2 - car commuting)
        'business': 28.30,          # £/hour (TAG A1.3 Table 2 - business travel)
        'leisure': 7.85,            # £/hour (TAG A1.3 Table 2 - leisure travel)
        'accident_prevention': 1_850_000,  # £ per fatality prevented
        'carbon_value': 80.0,       # £/tonne CO₂ (TAG A3 - 2024 central estimate)
        'bus_emissions': 0.0965,    # kg CO₂e per passenger-km (BEIS 2024)
        'car_emissions': 0.171,     # kg CO₂e per passenger-km (average UK car)
        'air_quality_nox': 120,     # £/tonne NOx reduction
        'air_quality_pm': 180,      # £/tonne PM reduction
        'noise_reduction': 0.15,    # £ per trip
    }

    # Agglomeration uplift factors (TAG A2.4)
    AGGLOMERATION_UPLIFT = {
        'urban': 0.25,              # 25% uplift for urban areas
        'city_center': 0.50,        # 50% uplift for city centers
        'rural': 0.0                # No agglomeration benefit in rural areas
    }

    # BCR thresholds (HM Treasury Green Book)
    BCR_CATEGORIES = {
        'poor': (0, 1.0),
        'low': (1.0, 1.5),
        'medium': (1.5, 2.0),
        'high': (2.0, 4.0),
        'very_high': (4.0, float('inf'))
    }

    # Cost Parameters (2024 prices)
    COST_FACTORS = {
        'bus_capex_per_vehicle': 250_000,  # £ per new bus
        'stop_infrastructure': 88_000,     # £ per new stop (updated from G37)
        'annual_operating_cost_ratio': 0.12,  # 12% of CAPEX
        'maintenance_cost_ratio': 0.03,    # 3% of CAPEX annually
        'fuel_cost_per_km': 0.45,         # £/km
        'driver_salary_annual': 32_000,    # £/year
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

    def categorize_bcr(self, bcr: float) -> str:
        """
        Categorize BCR value according to HM Treasury Green Book

        Args:
            bcr: Benefit-Cost Ratio

        Returns:
            Category string ('Poor', 'Low', 'Medium', 'High', 'Very High')
        """
        if bcr < 1.0:
            return 'Poor'
        elif bcr < 1.5:
            return 'Low'
        elif bcr < 2.0:
            return 'Medium'
        elif bcr < 4.0:
            return 'High'
        else:
            return 'Very High'

    def calculate_investment_costs(
        self,
        investment_amount: float,
        region_type: str = 'urban'
    ) -> Dict[str, float]:
        """
        Calculate total costs for bus service improvement

        Args:
            investment_amount: Total investment (£)
            region_type: 'urban' or 'rural' (affects cost breakdown)

        Returns:
            Dictionary of cost components
        """
        # Capital costs breakdown
        if region_type == 'urban':
            # Urban: More infrastructure, less vehicles (routes already exist)
            capital_costs = {
                'new_buses': investment_amount * 0.40,     # 40% on vehicles
                'infrastructure': investment_amount * 0.35,  # 35% on stops/depots
                'technology': investment_amount * 0.15,     # 15% on ticketing/real-time
                'planning_design': investment_amount * 0.10,  # 10% on planning
            }
        else:
            # Rural: More vehicles needed, less infrastructure density
            capital_costs = {
                'new_buses': investment_amount * 0.60,     # 60% on vehicles
                'infrastructure': investment_amount * 0.20,  # 20% on stops
                'technology': investment_amount * 0.10,     # 10% on technology
                'planning_design': investment_amount * 0.10,  # 10% on planning
            }

        total_capex = sum(capital_costs.values())

        # Operating costs (annual)
        num_buses = capital_costs['new_buses'] / self.COST_FACTORS['bus_capex_per_vehicle']

        annual_opex = {
            'vehicle_operating': total_capex * self.COST_FACTORS['annual_operating_cost_ratio'],
            'maintenance': total_capex * self.COST_FACTORS['maintenance_cost_ratio'],
            'driver_salaries': num_buses * self.COST_FACTORS['driver_salary_annual'],
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
            'num_buses': num_buses
        }

    def calculate_time_savings_benefits(
        self,
        population: float,
        adoption_rate: float = 0.20,
        time_saved_per_trip_minutes: float = 12.0,
        commuting_proportion: float = 0.70,
        is_urban: bool = True
    ) -> Dict[str, float]:
        """
        Calculate time savings benefits from improved bus service

        Args:
            population: Total population affected
            adoption_rate: Proportion using new service (default 20%)
            time_saved_per_trip_minutes: Minutes saved per trip (default 12)
            commuting_proportion: Proportion of trips that are commuting (default 70%)
            is_urban: Urban area (affects agglomeration uplift)

        Returns:
            Time savings benefits (annual and PV)
        """
        new_passengers = population * adoption_rate
        time_saved_hours = time_saved_per_trip_minutes / 60.0

        # Trip assumptions
        trips_per_passenger_per_year = 250  # Commuting days
        leisure_trips_per_year = 100  # Weekend/leisure trips

        # Split between commuting and leisure
        commuting_passengers = new_passengers * commuting_proportion
        leisure_passengers = new_passengers * (1 - commuting_proportion)

        # Base time savings
        commuting_benefit = (
            commuting_passengers *
            trips_per_passenger_per_year *
            time_saved_hours *
            self.DFT_VALUES_2024['bus_commuting']
        )

        leisure_benefit = (
            leisure_passengers *
            leisure_trips_per_year *
            time_saved_hours *
            self.DFT_VALUES_2024['leisure']
        )

        base_annual_benefit = commuting_benefit + leisure_benefit

        # Apply agglomeration uplift for urban areas
        uplift = self.AGGLOMERATION_UPLIFT['urban'] if is_urban else self.AGGLOMERATION_UPLIFT['rural']
        agglomeration_benefit = base_annual_benefit * uplift

        total_annual_benefit = base_annual_benefit + agglomeration_benefit

        # Present value
        pv_benefit = self.calculate_present_value(total_annual_benefit)

        return {
            'new_passengers': new_passengers,
            'annual_base_benefit': base_annual_benefit,
            'annual_agglomeration_benefit': agglomeration_benefit,
            'annual_total_benefit': total_annual_benefit,
            'pv_benefit': pv_benefit,
            'time_saved_hours_per_year': new_passengers * trips_per_passenger_per_year * time_saved_hours
        }

    def calculate_carbon_benefits(
        self,
        population: float,
        adoption_rate: float = 0.20,
        modal_shift_from_car: float = 0.60,
        avg_trip_distance_km: float = 8.5
    ) -> Dict[str, float]:
        """
        Calculate carbon emission reduction benefits

        Args:
            population: Total population affected
            adoption_rate: Proportion using new service
            modal_shift_from_car: Proportion switching from car (default 60%)
            avg_trip_distance_km: Average trip distance (default 8.5 km)

        Returns:
            Carbon benefit calculations
        """
        new_passengers = population * adoption_rate
        car_switchers = new_passengers * modal_shift_from_car

        # Annual trip assumptions
        trips_per_year = 300  # Total trips (commute + leisure)
        total_passenger_km = car_switchers * trips_per_year * avg_trip_distance_km

        # Carbon emissions
        car_emissions_tonnes = (total_passenger_km * self.DFT_VALUES_2024['car_emissions']) / 1000
        bus_emissions_tonnes = (total_passenger_km * self.DFT_VALUES_2024['bus_emissions']) / 1000

        # Net carbon savings
        carbon_saved_tonnes = car_emissions_tonnes - bus_emissions_tonnes

        # Monetized value
        annual_carbon_value = carbon_saved_tonnes * self.DFT_VALUES_2024['carbon_value']
        pv_carbon_value = self.calculate_present_value(annual_carbon_value)

        return {
            'car_switchers': car_switchers,
            'car_emissions_tonnes': car_emissions_tonnes,
            'bus_emissions_tonnes': bus_emissions_tonnes,
            'carbon_saved_tonnes': carbon_saved_tonnes,
            'annual_carbon_value': annual_carbon_value,
            'pv_carbon_value': pv_carbon_value
        }

    def calculate_full_bcr(
        self,
        investment_amount: float,
        population: float,
        region_type: str = 'urban',
        adoption_rate: float = 0.20,
        time_saved_minutes: float = 12.0,
        modal_shift_from_car: float = 0.60
    ) -> Dict[str, any]:
        """
        Calculate full BCR with all benefit components

        Args:
            investment_amount: Total investment (£)
            population: Population affected
            region_type: 'urban' or 'rural'
            adoption_rate: Proportion using service
            time_saved_minutes: Minutes saved per trip
            modal_shift_from_car: Proportion switching from car

        Returns:
            Complete BCR analysis
        """
        is_urban = (region_type == 'urban')

        # Costs
        costs = self.calculate_investment_costs(investment_amount, region_type)

        # Benefits
        time_benefits = self.calculate_time_savings_benefits(
            population,
            adoption_rate,
            time_saved_minutes,
            commuting_proportion=0.70,
            is_urban=is_urban
        )

        carbon_benefits = self.calculate_carbon_benefits(
            population,
            adoption_rate,
            modal_shift_from_car
        )

        # Total benefits
        total_pv_benefits = (
            time_benefits['pv_benefit'] +
            carbon_benefits['pv_carbon_value']
        )

        # BCR calculation
        bcr = total_pv_benefits / costs['total_cost_pv']
        bcr_category = self.categorize_bcr(bcr)

        return {
            'investment_amount': investment_amount,
            'population': population,
            'region_type': region_type,
            'costs': costs,
            'time_benefits': time_benefits,
            'carbon_benefits': carbon_benefits,
            'total_pv_benefits': total_pv_benefits,
            'total_pv_costs': costs['total_cost_pv'],
            'bcr': bcr,
            'bcr_category': bcr_category,
            'net_present_value': total_pv_benefits - costs['total_cost_pv']
        }

    def calculate_economic_multiplier_effects(
        self,
        investment_amount: float,
        region_type: str = 'urban'
    ) -> Dict[str, float]:
        """
        Calculate economic multiplier effects of bus investment

        Args:
            investment_amount: Total investment (£)
            region_type: 'urban' or 'rural' (affects multiplier)

        Returns:
            Economic impact calculations
        """
        # Multiplier values (HM Treasury/ONS research)
        # Urban areas have higher multipliers due to density effects
        multipliers = {
            'urban': {
                'direct': 1.0,          # Direct investment
                'indirect': 0.85,       # Supply chain effects
                'induced': 0.55,        # Wage spending effects
            },
            'rural': {
                'direct': 1.0,
                'indirect': 0.65,       # Lower supply chain density
                'induced': 0.40,        # Lower local spending retention
            }
        }

        region_multipliers = multipliers[region_type]

        # Direct effects
        direct_output = investment_amount * region_multipliers['direct']

        # Indirect effects (supply chain)
        indirect_output = investment_amount * region_multipliers['indirect']

        # Induced effects (wage spending)
        induced_output = investment_amount * region_multipliers['induced']

        # Total economic output
        total_economic_output = direct_output + indirect_output + induced_output
        total_multiplier = total_economic_output / investment_amount

        # Employment effects (construction + operations)
        # Transport sector employment multiplier: £65K per job (ONS 2024)
        direct_jobs = investment_amount / 65_000
        indirect_jobs = direct_jobs * 0.60  # Supply chain jobs
        induced_jobs = direct_jobs * 0.40   # Spending-induced jobs
        total_jobs = direct_jobs + indirect_jobs + induced_jobs

        # GVA contribution (approximately 60% of output becomes GVA)
        gva_contribution = total_economic_output * 0.60

        return {
            'direct_output': direct_output,
            'indirect_output': indirect_output,
            'induced_output': induced_output,
            'total_economic_output': total_economic_output,
            'total_multiplier': total_multiplier,
            'direct_jobs': direct_jobs,
            'indirect_jobs': indirect_jobs,
            'induced_jobs': induced_jobs,
            'total_jobs': total_jobs,
            'gva_contribution': gva_contribution
        }

    def calculate_employment_accessibility_value(
        self,
        population: float,
        jobs_made_accessible: int,
        adoption_rate: float = 0.15,
        employment_rate_increase: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate value of improved employment accessibility

        Args:
            population: Working-age population (16-64)
            jobs_made_accessible: Number of additional jobs accessible
            adoption_rate: Proportion benefiting from improved access
            employment_rate_increase: Increase in employment rate (e.g., 0.05 = 5%)

        Returns:
            Employment accessibility benefits
        """
        # Population benefiting
        workers_affected = population * adoption_rate

        # New employment created
        additional_employed = workers_affected * employment_rate_increase

        # Economic value
        # Average salary: £33,000 (ONS 2024)
        # Economic benefit = GDP contribution (≈70% of salary)
        avg_salary = 33_000
        annual_gdp_contribution = additional_employed * avg_salary * 0.70

        # Present value
        pv_employment_benefit = self.calculate_present_value(annual_gdp_contribution)

        # Wider benefits
        # Reduced welfare costs: £8,000/year per unemployed person
        welfare_savings_annual = additional_employed * 8_000
        pv_welfare_savings = self.calculate_present_value(welfare_savings_annual)

        # Total value
        total_pv_value = pv_employment_benefit + pv_welfare_savings

        return {
            'workers_affected': workers_affected,
            'jobs_made_accessible': jobs_made_accessible,
            'additional_employed': additional_employed,
            'annual_gdp_contribution': annual_gdp_contribution,
            'pv_employment_benefit': pv_employment_benefit,
            'annual_welfare_savings': welfare_savings_annual,
            'pv_welfare_savings': pv_welfare_savings,
            'total_pv_value': total_pv_value
        }
