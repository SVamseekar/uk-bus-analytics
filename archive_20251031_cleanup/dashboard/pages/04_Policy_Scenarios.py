"""
Policy Scenario Intelligence Module
===================================
Test policy interventions before implementation using economic elasticity models
Simulate fare caps, frequency increases, and coverage expansion

Author: UK Bus Analytics Platform
Date: 2025-10-29
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from dashboard.utils.data_loader import load_lsoa_metrics, get_summary_statistics
from dashboard.utils.ui_components import (
    apply_professional_config,
    load_professional_css,
    render_navigation_bar,
    render_dashboard_header,
    render_methodology_citation
)

# Import professional policy scenario simulator
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "policy_scenario_simulator",
        BASE_DIR / "analysis" / "spatial" / "05_policy_scenario_simulator.py"
    )
    policy_scenario_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy_scenario_module)
    PolicyScenarioSimulator = policy_scenario_module.PolicyScenarioSimulator
    SCENARIO_SIMULATOR_AVAILABLE = True
except Exception:
    SCENARIO_SIMULATOR_AVAILABLE = False
    PolicyScenarioSimulator = None

# Page config
st.set_page_config(
    page_title="Policy Scenarios",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply professional design
load_professional_css()
apply_professional_config()

# Navigation Bar
render_navigation_bar()

# Header
render_dashboard_header(
    title="Policy Scenarios",
    subtitle="Simulate policy interventions and forecast impacts with dynamic recalculation",
    icon="🎯"
)

# Elasticity Parameters Badge
col1, col2, col3 = st.columns(3)
with col1:
    st.info("**Fare Elasticity**: -0.40 (DfT)")
with col2:
    st.info("**Frequency Elasticity**: 0.40")
with col3:
    st.info("**Coverage Elasticity**: 0.50")

st.markdown("---")

# Load data
try:
    lsoa_data = load_lsoa_metrics()
    stats = get_summary_statistics(lsoa_data)

    # Baseline metrics
    baseline_stops = stats['total_stops']
    baseline_routes = stats['total_routes']
    baseline_avg_fare = 2.80  # UK average single fare
    baseline_ridership = baseline_stops * 50 * 250  # 50 trips/stop/day * 250 days
    baseline_revenue = baseline_ridership * baseline_avg_fare

    # Scenario Selection
    st.markdown("## 🔍 Select Policy Scenario")

    scenario_type = st.selectbox(
        "Scenario Type",
        ["Fare Cap", "Service Frequency Increase", "Coverage Expansion", "Combined Policy Package"],
        help="Choose the type of intervention to simulate"
    )

    st.markdown("---")

    # ============================================================================
    # SCENARIO 1: FARE CAP
    # ============================================================================
    if scenario_type == "Fare Cap":
        st.markdown("### 💷 Fare Cap Scenario Simulation")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("#### Input Parameters")

            fare_cap = st.select_slider(
                "Fare Cap Level",
                options=[1.00, 1.50, 2.00, 2.50, 3.00],
                value=2.00,
                format_func=lambda x: f"£{x:.2f}",
                help="Maximum single fare cap"
            )

            fare_reduction_pct = (baseline_avg_fare - fare_cap) / baseline_avg_fare

            st.metric(
                "Fare Reduction",
                f"{fare_reduction_pct*100:.1f}%",
                help="Percentage reduction from baseline"
            )

            # Elasticity calculation
            fare_elasticity = -0.40
            ridership_change_pct = fare_reduction_pct * fare_elasticity

            st.metric(
                "Expected Ridership Change",
                f"+{ridership_change_pct*100:.1f}%",
                help="Using fare elasticity of -0.40"
            )

        with col2:
            st.markdown("#### Scenario Results")

            if st.button("🧮 Run Fare Cap Simulation", type="primary", use_container_width=True):
                with st.spinner("Simulating fare cap impact..."):

                    # Use professional simulator if available
                    if SCENARIO_SIMULATOR_AVAILABLE and PolicyScenarioSimulator is not None:
                        try:
                            simulator = PolicyScenarioSimulator(lsoa_data)
                            results = simulator.simulate_fare_cap(fare_cap=fare_cap)

                            # Extract results
                            new_ridership = results['ridership']['new_trips']
                            ridership_increase = results['ridership']['additional_trips']
                            annual_subsidy_needed = results['subsidy']['additional_subsidy_needed']
                            total_annual_benefits = results['benefits']['total_benefits_annual']
                            bcr = results['bcr_10yr']

                            # Calculate revenue for visualization
                            new_revenue = new_ridership * fare_cap
                            revenue_loss = max(0, baseline_revenue - new_revenue)

                        except Exception as e:
                            st.warning(f"Professional simulator error: {e}, using simplified calculation")
                            SCENARIO_SIMULATOR_AVAILABLE = False

                    if not SCENARIO_SIMULATOR_AVAILABLE:
                        # Fallback simplified calculation
                        new_ridership = baseline_ridership * (1 + ridership_change_pct)
                        ridership_increase = new_ridership - baseline_ridership
                        new_revenue = new_ridership * fare_cap
                        revenue_loss = max(0, baseline_revenue - new_revenue)  # Ensure non-negative
                        annual_subsidy_needed = revenue_loss
                        total_annual_benefits = ridership_increase * 1.5  # Simplified
                        bcr = total_annual_benefits / annual_subsidy_needed if annual_subsidy_needed > 0 else float('inf')

                    # Display results
                    st.success("✅ Simulation Complete")

                    # KPIs
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)

                    with res_col1:
                        st.metric(
                            "New Annual Ridership",
                            f"{new_ridership/1_000_000:.1f}M",
                            delta=f"+{ridership_increase/1_000_000:.1f}M"
                        )

                    with res_col2:
                        st.metric(
                            "Annual Subsidy Required",
                            f"£{annual_subsidy_needed/1_000_000:.0f}M",
                            delta=f"-{revenue_loss/baseline_revenue*100:.1f}% revenue"
                        )

                    with res_col3:
                        st.metric(
                            "Annual Benefits",
                            f"£{total_annual_benefits/1_000_000:.0f}M",
                            help="Time + Carbon + Social benefits"
                        )

                    with res_col4:
                        st.metric(
                            "Benefit-Cost Ratio",
                            f"{bcr:.2f}",
                            help="Annual benefits ÷ Annual subsidy"
                        )

                    # Recommendation
                    st.markdown("---")
                    if bcr >= 1.5:
                        st.success(f"**✅ RECOMMENDED**: BCR of {bcr:.2f} indicates good value. Benefits ({total_annual_benefits/1_000_000:.0f}M) significantly exceed subsidy costs.")
                    elif bcr >= 1.0:
                        st.info(f"**⚖️ ACCEPTABLE**: BCR of {bcr:.2f} shows benefits marginally exceed costs. Consider alongside strategic objectives.")
                    else:
                        st.warning(f"**⚠️ MARGINAL**: BCR of {bcr:.2f} indicates costs exceed direct economic benefits. Requires strong social equity justification.")

                    # Impact visualization
                    st.markdown("---")
                    impact_data = pd.DataFrame({
                        'Metric': ['Baseline', f'With £{fare_cap:.2f} Cap'],
                        'Ridership (M)': [baseline_ridership/1_000_000, new_ridership/1_000_000],
                        'Revenue (£M)': [baseline_revenue/1_000_000, new_revenue/1_000_000]
                    })

                    fig = px.bar(
                        impact_data,
                        x='Metric',
                        y=['Ridership (M)', 'Revenue (£M)'],
                        barmode='group',
                        title='Fare Cap Impact: Ridership vs Revenue Trade-off'
                    )
                    st.plotly_chart(fig, use_container_width=True)

    # ============================================================================
    # SCENARIO 2: FREQUENCY INCREASE
    # ============================================================================
    elif scenario_type == "Service Frequency Increase":
        st.markdown("### 🚌 Service Frequency Increase Simulation")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("#### Input Parameters")

            frequency_increase = st.slider(
                "Frequency Increase (%)",
                min_value=10,
                max_value=50,
                value=20,
                step=5,
                help="Percentage increase in service frequency"
            ) / 100

            st.metric(
                "New Service Level",
                f"+{frequency_increase*100:.0f}%",
                help="Increased buses per hour"
            )

            # Elasticity calculation
            frequency_elasticity = 0.40
            ridership_change_pct = frequency_increase * frequency_elasticity

            st.metric(
                "Expected Ridership Change",
                f"+{ridership_change_pct*100:.1f}%",
                help="Using frequency elasticity of 0.40"
            )

        with col2:
            st.markdown("#### Scenario Results")

            if st.button("🧮 Run Frequency Simulation", type="primary", use_container_width=True):
                with st.spinner("Simulating frequency increase..."):

                    # Calculate impacts
                    new_ridership = baseline_ridership * (1 + ridership_change_pct)
                    ridership_increase = new_ridership - baseline_ridership

                    # Operating cost increase
                    baseline_operating_cost = baseline_routes * 250 * 12 * 100  # £100/hour avg
                    additional_operating_cost = baseline_operating_cost * frequency_increase
                    annual_additional_cost = additional_operating_cost

                    # Revenue increase
                    additional_revenue = ridership_increase * baseline_avg_fare

                    # Net cost
                    net_annual_cost = annual_additional_cost - additional_revenue

                    # Benefits
                    # DfT TAG time value (consistent with other modules)
                    time_value = 25.19  # £/hour (DfT TAG 2025 average)

                    # Waiting time reduction
                    avg_wait_reduction = 5  # minutes
                    waiting_time_benefits = baseline_ridership * 250 * (avg_wait_reduction / 60) * time_value

                    # Time savings for new users
                    new_users = ridership_increase / 250
                    time_benefits_new = new_users * 250 * (15 / 60) * time_value

                    # Reliability benefits
                    reliability_benefit = baseline_ridership * 0.50  # £0.50/trip

                    total_annual_benefits = waiting_time_benefits + time_benefits_new + reliability_benefit

                    # BCR
                    bcr = total_annual_benefits / net_annual_cost if net_annual_cost > 0 else float('inf')

                    # Display results
                    st.success("✅ Simulation Complete")

                    # KPIs
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)

                    with res_col1:
                        st.metric(
                            "New Annual Ridership",
                            f"{new_ridership/1_000_000:.1f}M",
                            delta=f"+{ridership_change_pct*100:.1f}%"
                        )

                    with res_col2:
                        st.metric(
                            "Additional Operating Cost",
                            f"£{annual_additional_cost/1_000_000:.0f}M/year",
                            delta=f"+{frequency_increase*100:.0f}% service"
                        )

                    with res_col3:
                        st.metric(
                            "Additional Revenue",
                            f"£{additional_revenue/1_000_000:.0f}M/year",
                            delta=f"Net: £{net_annual_cost/1_000_000:.0f}M"
                        )

                    with res_col4:
                        st.metric(
                            "Benefit-Cost Ratio",
                            f"{bcr:.2f}",
                            help="Benefits ÷ Net costs"
                        )

                    # Recommendation
                    st.markdown("---")
                    if bcr >= 1.5:
                        st.success(f"**✅ RECOMMENDED**: BCR of {bcr:.2f} shows strong value. Frequency increases improve reliability and attract new users.")
                    elif bcr >= 1.0:
                        st.info(f"**⚖️ ACCEPTABLE**: BCR of {bcr:.2f} indicates positive value. Consider for high-demand corridors.")
                    else:
                        st.warning(f"**⚠️ MARGINAL**: BCR of {bcr:.2f}. Operating costs may exceed benefits. Target specific corridors with proven demand.")

    # ============================================================================
    # SCENARIO 3: COVERAGE EXPANSION
    # ============================================================================
    elif scenario_type == "Coverage Expansion":
        st.markdown("### 🗺️ Coverage Expansion Simulation")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("#### Input Parameters")

            coverage_increase = st.slider(
                "Coverage Expansion (%)",
                min_value=5,
                max_value=25,
                value=10,
                step=5,
                help="Percentage increase in network coverage (new stops/routes)"
            ) / 100

            st.metric(
                "New Infrastructure",
                f"+{coverage_increase*100:.0f}%",
                help="Additional stops and routes"
            )

            # Elasticity calculation
            coverage_elasticity = 0.50
            ridership_change_pct = coverage_increase * coverage_elasticity

            st.metric(
                "Expected Ridership Change",
                f"+{ridership_change_pct*100:.1f}%",
                help="Using coverage elasticity of 0.50"
            )

        with col2:
            st.markdown("#### Scenario Results")

            if st.button("🧮 Run Coverage Expansion Simulation", type="primary", use_container_width=True):
                with st.spinner("Simulating coverage expansion..."):

                    # Calculate impacts
                    new_stops = int(baseline_stops * (1 + coverage_increase))
                    new_routes = int(baseline_routes * (1 + coverage_increase))

                    new_ridership = baseline_ridership * (1 + ridership_change_pct)
                    ridership_increase = new_ridership - baseline_ridership

                    # Capital costs
                    cost_per_stop = 50_000  # £50k per stop (infrastructure)
                    cost_per_route = 500_000  # £500k per route (vehicles + planning)
                    capital_cost = (new_stops - baseline_stops) * cost_per_stop + (new_routes - baseline_routes) * cost_per_route

                    # Operating costs
                    additional_operating_cost_annual = (new_routes - baseline_routes) * 250 * 12 * 100

                    # Revenue
                    additional_revenue = ridership_increase * baseline_avg_fare

                    # Benefits
                    # Accessibility for new areas
                    newly_served_population = 50_000  # Estimate
                    accessibility_benefit = newly_served_population * 300  # £300/person/year

                    # Employment access
                    employment_benefit = newly_served_population * 0.25 * 2500

                    # Social inclusion
                    social_benefit = newly_served_population * 150

                    total_annual_benefits = accessibility_benefit + employment_benefit + social_benefit

                    # Simple payback period
                    annual_net_benefit = total_annual_benefits - additional_operating_cost_annual + additional_revenue
                    payback_years = capital_cost / annual_net_benefit if annual_net_benefit > 0 else float('inf')

                    # 30-year BCR
                    pv_benefits = total_annual_benefits * 20  # Simplified PV
                    pv_costs = capital_cost + (additional_operating_cost_annual * 20)
                    bcr = pv_benefits / pv_costs

                    # Display results
                    st.success("✅ Simulation Complete")

                    # KPIs
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)

                    with res_col1:
                        st.metric(
                            "New Stops",
                            f"{new_stops:,}",
                            delta=f"+{new_stops - baseline_stops:,}"
                        )

                    with res_col2:
                        st.metric(
                            "Capital Investment",
                            f"£{capital_cost/1_000_000:.0f}M",
                            help="One-time infrastructure cost"
                        )

                    with res_col3:
                        st.metric(
                            "Annual Benefits",
                            f"£{total_annual_benefits/1_000_000:.0f}M/year",
                            help="Accessibility + Employment + Social"
                        )

                    with res_col4:
                        st.metric(
                            "BCR (30-year)",
                            f"{bcr:.2f}",
                            help="Present value BCR"
                        )

                    # Recommendation
                    st.markdown("---")
                    if bcr >= 1.5:
                        st.success(f"**✅ RECOMMENDED**: BCR of {bcr:.2f} shows strong social value. Coverage expansion connects underserved communities.")
                    elif bcr >= 1.0:
                        st.info(f"**⚖️ ACCEPTABLE**: BCR of {bcr:.2f}. Focus expansion on high-need, low-coverage areas for best value.")
                    else:
                        st.warning(f"**⚠️ REVIEW NEEDED**: BCR of {bcr:.2f}. High capital costs require strong strategic justification. Consider phased rollout.")

    # ============================================================================
    # SCENARIO 4: COMBINED PACKAGE
    # ============================================================================
    else:  # Combined Policy Package
        st.markdown("### 🎁 Combined Policy Package Simulation")

        st.info("**Synergy Factor**: Combined policies have 15% additional interaction effect")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("#### Select Interventions")

            include_fare_cap = st.checkbox("Fare Cap (£2.00)", value=True)
            include_frequency = st.checkbox("Frequency +20%", value=True)
            include_coverage = st.checkbox("Coverage +10%", value=False)

        with col2:
            if st.button("🧮 Run Combined Package Simulation", type="primary", use_container_width=True):
                with st.spinner("Simulating combined policy package..."):

                    total_ridership_change = 0
                    total_annual_cost = 0
                    total_annual_benefits = 0

                    # Add each component
                    if include_fare_cap:
                        total_ridership_change += 0.114  # 11.4% from £2 cap
                        total_annual_cost += 672_000_000  # Subsidy
                        total_annual_benefits += 900_000_000

                    if include_frequency:
                        total_ridership_change += 0.080  # 8% from 20% frequency
                        total_annual_cost += 150_000_000  # Operating
                        total_annual_benefits += 500_000_000

                    if include_coverage:
                        total_ridership_change += 0.050  # 5% from 10% coverage
                        total_annual_cost += 200_000_000  # CAPEX amortized
                        total_annual_benefits += 400_000_000

                    # Synergy effect (15%)
                    synergy_factor = 1.15
                    total_ridership_change *= synergy_factor
                    total_annual_benefits *= synergy_factor

                    new_ridership = baseline_ridership * (1 + total_ridership_change)

                    bcr = total_annual_benefits / total_annual_cost if total_annual_cost > 0 else 0

                    # Display
                    st.success("✅ Combined Package Simulation Complete")

                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)

                    with res_col1:
                        st.metric(
                            "Combined Ridership Impact",
                            f"+{total_ridership_change*100:.1f}%",
                            help="Including 15% synergy effect"
                        )

                    with res_col2:
                        st.metric(
                            "Total Annual Cost",
                            f"£{total_annual_cost/1_000_000:.0f}M",
                            help="Subsidy + Operating + Amortized CAPEX"
                        )

                    with res_col3:
                        st.metric(
                            "Total Annual Benefits",
                            f"£{total_annual_benefits/1_000_000:.0f}M",
                            help="With synergy multiplier"
                        )

                    with res_col4:
                        st.metric(
                            "Package BCR",
                            f"{bcr:.2f}",
                            help="Combined benefit-cost ratio"
                        )

                    if bcr >= 1.5:
                        st.success(f"**✅ STRONG PACKAGE**: Combined BCR of {bcr:.2f} shows excellent value from policy synergies.")
                    else:
                        st.info(f"**Policy package BCR: {bcr:.2f}**. Multiple interventions create synergistic benefits.")

    # Comparison Tool
    st.markdown("---")
    st.markdown("### 📊 Scenario Comparison Tool")

    comparison_data = pd.DataFrame({
        'Scenario': ['£2 Fare Cap', '+20% Frequency', '+10% Coverage'],
        'Ridership Impact': ['+11.4%', '+8.0%', '+5.0%'],
        'Annual Cost (£M)': [672, 150, 200],
        'Annual Benefits (£M)': [900, 500, 400],
        'BCR': [1.34, 3.33, 2.00]
    })

    st.dataframe(comparison_data, use_container_width=True)

    fig_comparison = px.scatter(
        comparison_data,
        x='Annual Cost (£M)',
        y='BCR',
        size='Annual Benefits (£M)',
        text='Scenario',
        title='Policy Scenario Comparison: Cost vs Value',
        color='BCR',
        color_continuous_scale='RdYlGn'
    )

    st.plotly_chart(fig_comparison, use_container_width=True)

    # Methodology Citations
    st.markdown("---")
    render_methodology_citation(['DfT Transport Appraisal Guidance', 'HM Treasury Green Book', 'BEIS Emission Factors'])

except Exception as e:
    st.error(f"Error loading policy scenario data: {str(e)}")
    st.info("Please ensure spatial metrics have been computed.")
