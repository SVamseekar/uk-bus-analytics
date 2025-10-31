"""
Dynamic UK Bus Analytics - Descriptive Analytics Pipeline
Computes comprehensive KPIs and metrics across all regions
Answers key questions about coverage, accessibility, and service quality
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DATA_PROCESSED, LOGS_DIR
)

logger.add(LOGS_DIR / "analytics_{time}.log", rotation="1 day", retention="30 days")


class DescriptiveAnalyticsPipeline:
    """
    Comprehensive descriptive analytics for UK bus networks
    Computes KPIs to answer critical policy and planning questions
    """

    def __init__(self):
        """Initialize analytics pipeline"""
        self.processed_dir = DATA_PROCESSED / 'regions'
        self.analytics_output = Path('analytics')
        self.analytics_output.mkdir(exist_ok=True)

        # Data containers
        self.regional_data = {}
        self.kpis = {}
        self.summary_stats = {}

        # Results storage
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'regions_analyzed': 0,
            'total_stops': 0,
            'total_routes': 0,
            'kpis_by_region': {},
            'national_summary': {}
        }

    def discover_processed_files(self) -> Dict[str, Dict[str, Path]]:
        """
        Discover all processed data files across regions
        """
        logger.info("Discovering processed data files...")

        discovered = {}

        for region_dir in self.processed_dir.iterdir():
            if region_dir.is_dir():
                region_code = region_dir.name

                stops_file = region_dir / 'stops_processed.csv'
                routes_file = region_dir / 'routes_processed.csv'

                if stops_file.exists() and routes_file.exists():
                    discovered[region_code] = {
                        'stops': stops_file,
                        'routes': routes_file
                    }
                    logger.info(f"✓ {region_code}: Found processed files")

        logger.success(f"Discovered {len(discovered)} regions with processed data")
        return discovered

    def load_regional_data(self, region_code: str, file_paths: Dict[str, Path]) -> Dict:
        """
        Load processed data for a specific region
        """
        logger.info(f"Loading data for {region_code}...")

        data = {
            'region_code': region_code,
            'stops': None,
            'routes': None
        }

        try:
            # Try to load enriched data first (stops_processed_processed.csv)
            region_dir = self.processed_dir / region_code
            enriched_file = region_dir / 'stops_processed_processed.csv'

            if enriched_file.exists():
                data['stops'] = pd.read_csv(enriched_file)
                logger.info(f"  Loaded {len(data['stops'])} stops (enriched data with demographics)")
            elif file_paths['stops'].exists():
                data['stops'] = pd.read_csv(file_paths['stops'])
                logger.info(f"  Loaded {len(data['stops'])} stops (basic data)")

            # Load routes data
            if file_paths['routes'].exists():
                data['routes'] = pd.read_csv(file_paths['routes'])
                logger.info(f"  Loaded {len(data['routes'])} routes")

        except Exception as e:
            logger.error(f"Error loading data for {region_code}: {e}")

        return data

    def compute_coverage_metrics(self, region_code: str, data: Dict) -> Dict:
        """
        Compute coverage and accessibility metrics

        Answers questions:
        - How many bus stops exist per region?
        - What is the density of bus stops?
        - What is the LSOA coverage?
        """
        logger.info(f"Computing coverage metrics for {region_code}...")

        stops_df = data['stops']
        routes_df = data['routes']

        metrics = {
            'region': region_code,
            'total_stops': 0,
            'total_routes': 0,
            'unique_lsoas': 0,
            'stops_with_coordinates': 0,
            'stops_with_demographics': 0,
            'lsoa_coverage_pct': 0.0
        }

        if stops_df is not None and not stops_df.empty:
            metrics['total_stops'] = len(stops_df)

            # Count stops with valid coordinates
            if 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
                valid_coords = stops_df[
                    (stops_df['latitude'].notna()) &
                    (stops_df['longitude'].notna())
                ]
                metrics['stops_with_coordinates'] = len(valid_coords)

            # Count unique LSOAs
            if 'lsoa_code' in stops_df.columns:
                metrics['unique_lsoas'] = stops_df['lsoa_code'].nunique()

            # Check demographic integration
            demo_cols = ['OBS_VALUE_population_2021', 'OBS_VALUE_unemployment_2024']
            demo_present = [col for col in demo_cols if col in stops_df.columns]
            if demo_present:
                metrics['stops_with_demographics'] = stops_df[demo_present[0]].notna().sum()

        if routes_df is not None and not routes_df.empty:
            metrics['total_routes'] = len(routes_df)

        # Calculate coverage percentage
        if metrics['total_stops'] > 0:
            metrics['lsoa_coverage_pct'] = (
                metrics['stops_with_demographics'] / metrics['total_stops'] * 100
            )

        return metrics

    def compute_service_metrics(self, region_code: str, data: Dict) -> Dict:
        """
        Compute service quality and frequency metrics

        Answers questions:
        - How many routes serve each area?
        - What is the average route length?
        - What is the route density?
        """
        logger.info(f"Computing service metrics for {region_code}...")

        routes_df = data['routes']

        metrics = {
            'region': region_code,
            'total_routes': 0,
            'avg_route_length': 0.0,
            'routes_with_operator': 0,
            'unique_operators': 0
        }

        if routes_df is not None and not routes_df.empty:
            metrics['total_routes'] = len(routes_df)

            # Average route characteristics
            if 'route_name' in routes_df.columns:
                metrics['unique_route_names'] = routes_df['route_name'].nunique()

            if 'operator' in routes_df.columns:
                metrics['routes_with_operator'] = routes_df['operator'].notna().sum()
                metrics['unique_operators'] = routes_df['operator'].nunique()

        return metrics

    def compute_demographic_correlations(self, region_code: str, data: Dict) -> Dict:
        """
        Compute correlations between bus coverage and demographics

        Answers questions:
        - Is there correlation between population and bus coverage?
        - Do high unemployment areas have good bus access?
        - Are demographic factors related to service provision?
        """
        logger.info(f"Computing demographic correlations for {region_code}...")

        stops_df = data['stops']

        correlations = {
            'region': region_code,
            'population_coverage_corr': None,
            'unemployment_coverage_corr': None,
            'avg_population_per_stop': None,
            'high_unemployment_stops_pct': None
        }

        if stops_df is not None and not stops_df.empty:
            # Population analysis
            if 'OBS_VALUE_population_2021' in stops_df.columns:
                pop_data = stops_df['OBS_VALUE_population_2021'].dropna()
                if len(pop_data) > 0:
                    correlations['avg_population_per_stop'] = float(pop_data.mean())

            # Unemployment analysis
            if 'OBS_VALUE_unemployment_2024' in stops_df.columns:
                unemp_data = stops_df['OBS_VALUE_unemployment_2024'].dropna()
                if len(unemp_data) > 0:
                    # Calculate percentage of stops in high unemployment areas (>5%)
                    high_unemp = (unemp_data > 5).sum()
                    correlations['high_unemployment_stops_pct'] = (
                        high_unemp / len(unemp_data) * 100
                    )

        return correlations

    def compute_accessibility_metrics(self, region_code: str, data: Dict) -> Dict:
        """
        Compute accessibility and equity metrics

        Answers questions:
        - Which areas lack bus service?
        - What is the spatial distribution of stops?
        - Are there coverage gaps?
        """
        logger.info(f"Computing accessibility metrics for {region_code}...")

        stops_df = data['stops']

        metrics = {
            'region': region_code,
            'coordinate_coverage_pct': 0.0,
            'lsoa_with_stops': 0,
            'avg_stops_per_lsoa': 0.0,
            'max_stops_per_lsoa': 0,
            'min_stops_per_lsoa': 0
        }

        if stops_df is not None and not stops_df.empty:
            # Coordinate coverage
            if 'latitude' in stops_df.columns:
                valid_coords = stops_df['latitude'].notna().sum()
                metrics['coordinate_coverage_pct'] = (
                    valid_coords / len(stops_df) * 100
                )

            # LSOA-level analysis
            if 'lsoa_code' in stops_df.columns:
                lsoa_counts = stops_df.groupby('lsoa_code').size()
                metrics['lsoa_with_stops'] = len(lsoa_counts)
                metrics['avg_stops_per_lsoa'] = float(lsoa_counts.mean())
                metrics['max_stops_per_lsoa'] = int(lsoa_counts.max())
                metrics['min_stops_per_lsoa'] = int(lsoa_counts.min())

        return metrics

    def generate_regional_summary(self, region_code: str, data: Dict) -> Dict:
        """
        Generate comprehensive summary for a region
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"ANALYZING: {region_code.upper().replace('_', ' ')}")
        logger.info(f"{'='*60}")

        summary = {
            'region_code': region_code,
            'coverage': self.compute_coverage_metrics(region_code, data),
            'service': self.compute_service_metrics(region_code, data),
            'demographics': self.compute_demographic_correlations(region_code, data),
            'accessibility': self.compute_accessibility_metrics(region_code, data)
        }

        # Log key findings
        logger.info(f"\nKey Metrics:")
        logger.info(f"  Stops: {summary['coverage']['total_stops']:,}")
        logger.info(f"  Routes: {summary['service']['total_routes']:,}")
        logger.info(f"  LSOAs Covered: {summary['coverage']['unique_lsoas']:,}")
        logger.info(f"  Coordinate Coverage: {summary['accessibility']['coordinate_coverage_pct']:.1f}%")

        return summary

    def compute_national_aggregates(self) -> Dict:
        """
        Compute national-level aggregate statistics
        """
        logger.info("\n" + "="*60)
        logger.info("COMPUTING NATIONAL AGGREGATES")
        logger.info("="*60)

        aggregates = {
            'total_regions': len(self.kpis),
            'total_stops': 0,
            'total_routes': 0,
            'total_lsoas': 0,
            'avg_stops_per_region': 0.0,
            'avg_routes_per_region': 0.0,
            'national_coordinate_coverage': 0.0,
            'regions_analyzed': list(self.kpis.keys())
        }

        if not self.kpis:
            logger.warning("No regional KPIs available for aggregation")
            return aggregates

        # Aggregate totals
        total_stops = sum(kpi['coverage']['total_stops'] for kpi in self.kpis.values())
        total_routes = sum(kpi['service']['total_routes'] for kpi in self.kpis.values())
        total_lsoas = sum(kpi['coverage']['unique_lsoas'] for kpi in self.kpis.values())

        aggregates['total_stops'] = total_stops
        aggregates['total_routes'] = total_routes
        aggregates['total_lsoas'] = total_lsoas

        # Averages
        if aggregates['total_regions'] > 0:
            aggregates['avg_stops_per_region'] = total_stops / aggregates['total_regions']
            aggregates['avg_routes_per_region'] = total_routes / aggregates['total_regions']

        # Weighted coordinate coverage
        total_coords = sum(
            kpi['coverage']['stops_with_coordinates']
            for kpi in self.kpis.values()
        )
        if total_stops > 0:
            aggregates['national_coordinate_coverage'] = (
                total_coords / total_stops * 100
            )

        logger.success(f"\nNational Summary:")
        logger.success(f"  Total Stops: {aggregates['total_stops']:,}")
        logger.success(f"  Total Routes: {aggregates['total_routes']:,}")
        logger.success(f"  Total LSOAs: {aggregates['total_lsoas']:,}")
        logger.success(f"  Regions: {aggregates['total_regions']}")
        logger.success(f"  Coordinate Coverage: {aggregates['national_coordinate_coverage']:.1f}%")

        return aggregates

    def save_results(self):
        """
        Save all results to JSON and CSV files
        """
        logger.info("Saving analytics results...")

        # Save comprehensive JSON results
        results_file = self.analytics_output / f'analytics_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        self.results['kpis_by_region'] = self.kpis
        self.results['national_summary'] = self.summary_stats
        self.results['regions_analyzed'] = len(self.kpis)
        self.results['total_stops'] = self.summary_stats.get('total_stops', 0)
        self.results['total_routes'] = self.summary_stats.get('total_routes', 0)

        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.success(f"Results saved to: {results_file}")

        # Save regional KPIs to CSV
        regional_summary = []
        for region, kpis in self.kpis.items():
            row = {
                'region': region,
                'total_stops': kpis['coverage']['total_stops'],
                'total_routes': kpis['service']['total_routes'],
                'unique_lsoas': kpis['coverage']['unique_lsoas'],
                'coordinate_coverage_pct': kpis['accessibility']['coordinate_coverage_pct'],
                'avg_stops_per_lsoa': kpis['accessibility']['avg_stops_per_lsoa'],
                'unique_operators': kpis['service'].get('unique_operators', 0)
            }
            regional_summary.append(row)

        if regional_summary:
            summary_df = pd.DataFrame(regional_summary)
            summary_file = self.analytics_output / 'regional_summary.csv'
            summary_df.to_csv(summary_file, index=False)
            logger.success(f"Regional summary saved to: {summary_file}")

    def run_analytics(self):
        """
        Main analytics pipeline execution
        """
        logger.info("\n" + "="*60)
        logger.info("UK BUS ANALYTICS - DESCRIPTIVE ANALYTICS PIPELINE")
        logger.info("="*60)

        # Discover processed files
        discovered = self.discover_processed_files()

        if not discovered:
            logger.error("No processed data files found!")
            return

        logger.info(f"\nAnalyzing {len(discovered)} regions...\n")

        # Process each region
        for region_code, file_paths in discovered.items():
            try:
                # Load data
                data = self.load_regional_data(region_code, file_paths)

                # Generate comprehensive summary
                summary = self.generate_regional_summary(region_code, data)

                # Store KPIs
                self.kpis[region_code] = summary
                self.regional_data[region_code] = data

            except Exception as e:
                logger.error(f"Error analyzing {region_code}: {e}")
                import traceback
                traceback.print_exc()

        # Compute national aggregates
        self.summary_stats = self.compute_national_aggregates()

        # Save all results
        self.save_results()

        logger.success("\n" + "="*60)
        logger.success("ANALYTICS PIPELINE COMPLETE")
        logger.success("="*60)


def main():
    """Main execution function"""
    pipeline = DescriptiveAnalyticsPipeline()
    pipeline.run_analytics()


if __name__ == "__main__":
    main()
