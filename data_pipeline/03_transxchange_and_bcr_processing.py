"""
TransXChange Route Extraction and BCR Analysis Pipeline
Part of UK Bus Analytics Data Pipeline

Integrates:
1. TransXChange XML extraction (trips, routes, frequencies)
2. BCR calculation setup with 2024 TAG values
3. Route geometry processing

Author: UK Bus Analytics Project
Date: 2025-11-02
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import DATA_RAW, DATA_PROCESSED, LOGS_DIR
from utils.transxchange_schedule_extractor import process_all_transxchange_files
from archive_20251031_cleanup.analysis.spatial.utils.bcr_calculator import BCRCalculator

logger.add(LOGS_DIR / "transxchange_bcr_{time}.log", rotation="1 day", retention="30 days")


class TransXChangeAndBCRPipeline:
    """
    Pipeline for processing TransXChange data and BCR calculations
    """

    def __init__(self):
        """Initialize pipeline"""
        self.stats = {
            'start_time': datetime.now(),
            'transxchange_files_processed': 0,
            'route_links_extracted': 0,
            'trips_extracted': 0,
            'regions_processed': {},
            'bcr_ready': False,
            'errors': []
        }

        # Initialize BCR calculator
        self.bcr_calculator = BCRCalculator()
        logger.info("BCR Calculator initialized with 2024 TAG values")

    def run_transxchange_extraction(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Extract all TransXChange data from XML files

        Returns:
            Tuple of (trips_df, routes_df, frequencies_df)
        """
        logger.info("=" * 80)
        logger.info("TRANSXCHANGE EXTRACTION PIPELINE")
        logger.info("=" * 80)

        # Check if already extracted
        output_dir = DATA_PROCESSED / 'outputs'
        route_geometries_file = output_dir / 'route_geometries.csv'

        if route_geometries_file.exists():
            logger.info("TransXChange data already extracted. Loading from cache...")
            try:
                routes_df = pd.read_csv(route_geometries_file)
                trips_df = pd.read_csv(output_dir / 'trips_schedule.csv') if (output_dir / 'trips_schedule.csv').exists() else pd.DataFrame()
                freq_df = pd.read_csv(output_dir / 'service_frequencies.csv') if (output_dir / 'service_frequencies.csv').exists() else pd.DataFrame()

                logger.success(f"✓ Loaded {len(routes_df):,} route links from cache")
                self.stats['route_links_extracted'] = len(routes_df)
                self.stats['trips_extracted'] = len(trips_df)

                return trips_df, routes_df, freq_df

            except Exception as e:
                logger.warning(f"Failed to load cached data: {e}")
                logger.info("Re-extracting TransXChange data...")

        # Run extraction
        input_dir = DATA_RAW / 'transxchange_extracted'

        if not input_dir.exists():
            logger.warning(f"TransXChange directory not found: {input_dir}")
            logger.info("Run utils/extract_all_transxchange.py first to extract XML files from zips")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        trips_df, routes_df, freq_df = process_all_transxchange_files(
            input_dir=str(input_dir),
            output_dir=str(output_dir)
        )

        # Update stats
        self.stats['transxchange_files_processed'] = len(list(input_dir.rglob('*.xml')))
        self.stats['route_links_extracted'] = len(routes_df)
        self.stats['trips_extracted'] = len(trips_df)

        if not routes_df.empty:
            # Regional breakdown
            for region, count in routes_df.groupby('region').size().items():
                self.stats['regions_processed'][region] = {
                    'route_links': count
                }

        logger.success("TransXChange extraction complete")
        return trips_df, routes_df, freq_df

    def calculate_route_statistics(self, routes_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate statistics from route geometry data

        Args:
            routes_df: DataFrame with route links

        Returns:
            DataFrame with route statistics by region/operator
        """
        if routes_df.empty:
            logger.warning("No route data available for statistics")
            return pd.DataFrame()

        logger.info("Calculating route statistics...")

        # Group by region and operator
        stats = []

        for (region, operator), group in routes_df.groupby(['region', 'operator']):
            # Calculate statistics
            total_links = len(group)
            unique_routes = group['section_id'].nunique()

            # Average run times
            avg_run_time = group['run_time_min'].mean() if 'run_time_min' in group.columns else None

            # Distance statistics
            total_distance_km = group['distance_m'].sum() / 1000 if 'distance_m' in group.columns else None
            avg_link_distance_m = group['distance_m'].mean() if 'distance_m' in group.columns else None

            stats.append({
                'region': region,
                'operator': operator,
                'total_route_links': total_links,
                'unique_routes': unique_routes,
                'avg_run_time_min': avg_run_time,
                'total_distance_km': total_distance_km,
                'avg_link_distance_m': avg_link_distance_m
            })

        stats_df = pd.DataFrame(stats)

        # Save statistics
        output_file = DATA_PROCESSED / 'outputs' / 'route_statistics.csv'
        stats_df.to_csv(output_file, index=False)
        logger.success(f"✓ Saved route statistics to {output_file}")

        return stats_df

    def prepare_bcr_analysis_data(self) -> bool:
        """
        Prepare data for BCR analysis by combining stops with demographics

        Returns:
            bool: Success status
        """
        logger.info("Preparing data for BCR analysis...")

        try:
            # Load processed stops data (already has demographics integrated)
            regions_dir = DATA_PROCESSED / 'regions'

            if not regions_dir.exists():
                logger.error("Processed regions directory not found")
                return False

            # Check for stops_processed.csv in each region
            all_stops = []
            regions_found = []

            for region_dir in regions_dir.iterdir():
                if region_dir.is_dir():
                    stops_file = region_dir / 'stops_processed.csv'
                    if stops_file.exists():
                        try:
                            stops_df = pd.read_csv(stops_file)
                            stops_df['region'] = region_dir.name
                            all_stops.append(stops_df)
                            regions_found.append(region_dir.name)
                            logger.info(f"  ✓ Loaded {len(stops_df):,} stops from {region_dir.name}")
                        except Exception as e:
                            logger.error(f"  ✗ Failed to load {region_dir.name}: {e}")

            if not all_stops:
                logger.error("No processed stops data found")
                return False

            # Combine all regions
            combined_stops = pd.concat(all_stops, ignore_index=True)
            logger.success(f"Combined {len(combined_stops):,} stops from {len(regions_found)} regions")

            # Save combined file for BCR analysis
            output_file = DATA_PROCESSED / 'outputs' / 'stops_with_demographics_all_regions.csv'
            combined_stops.to_csv(output_file, index=False)
            logger.success(f"✓ Saved combined stops to {output_file}")

            self.stats['bcr_ready'] = True
            return True

        except Exception as e:
            logger.error(f"Failed to prepare BCR data: {e}")
            self.stats['errors'].append(f"BCR prep: {e}")
            return False

    def run_sample_bcr_calculation(self) -> Dict:
        """
        Run a sample BCR calculation to verify the calculator works

        Returns:
            Dict with BCR results
        """
        logger.info("Running sample BCR calculation...")

        try:
            # Load combined stops data
            stops_file = DATA_PROCESSED / 'outputs' / 'stops_with_demographics_all_regions.csv'

            if not stops_file.exists():
                logger.warning("Combined stops file not found. Run prepare_bcr_analysis_data() first")
                return {}

            stops_df = pd.read_csv(stops_file)

            # Select a sample of LSOAs for demonstration
            # Filter to get LSOAs with population data
            sample_lsoas = stops_df[
                stops_df['total_population'].notna() &
                (stops_df['total_population'] > 0)
            ].head(1000)  # Sample first 1000 stops

            if sample_lsoas.empty:
                logger.warning("No valid LSOA data for BCR calculation")
                return {}

            # Aggregate by LSOA
            lsoa_data = sample_lsoas.groupby('lsoa_code').agg({
                'total_population': 'first',
                'Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)': 'first',
                'Employment Score (rate)': 'first'
            }).reset_index()

            lsoa_data.columns = ['lsoa_code', 'population', 'imd_decile', 'unemployment_rate']

            # Run BCR calculation
            investment_amount = 10_000_000  # £10M sample investment

            result = self.bcr_calculator.calculate_full_bcr(
                lsoa_data=lsoa_data,
                investment_amount=investment_amount,
                adoption_rate=0.25,
                modal_shift_from_car=0.70
            )

            # Log results
            logger.info("=" * 80)
            logger.info("SAMPLE BCR CALCULATION RESULTS")
            logger.info("=" * 80)
            logger.info(f"Investment: £{result['summary']['investment_amount']:,.0f}")
            logger.info(f"LSOAs analyzed: {result['summary']['num_lsoas']}")
            logger.info(f"Population served: {result['summary']['total_population_served']:,.0f}")
            logger.info(f"BCR: {result['summary']['bcr']:.2f}")
            logger.info(f"NPV: £{result['summary']['npv']:,.0f}")
            logger.info(f"Recommendation: {result['summary']['recommendation']}")
            logger.info("=" * 80)

            # Save sample results
            output_file = DATA_PROCESSED / 'outputs' / 'sample_bcr_results.json'
            import json
            with open(output_file, 'w') as f:
                # Convert to JSON-serializable format
                result_json = {k: str(v) if isinstance(v, (pd.DataFrame, np.ndarray)) else v
                              for k, v in result.items()}
                json.dump(result_json, f, indent=2, default=str)

            logger.success(f"✓ Saved sample BCR results to {output_file}")

            return result

        except Exception as e:
            logger.error(f"Sample BCR calculation failed: {e}")
            self.stats['errors'].append(f"BCR calculation: {e}")
            return {}

    def run_full_pipeline(self):
        """
        Run the complete TransXChange and BCR pipeline
        """
        logger.info("=" * 80)
        logger.info("STARTING TRANSXCHANGE + BCR PIPELINE")
        logger.info("=" * 80)

        # Step 1: Extract TransXChange data
        trips_df, routes_df, freq_df = self.run_transxchange_extraction()

        # Step 2: Calculate route statistics
        if not routes_df.empty:
            route_stats = self.calculate_route_statistics(routes_df)
        else:
            logger.warning("Skipping route statistics (no data)")

        # Step 3: Prepare BCR analysis data
        bcr_prep_success = self.prepare_bcr_analysis_data()

        # Step 4: Run sample BCR calculation
        if bcr_prep_success:
            bcr_result = self.run_sample_bcr_calculation()
        else:
            logger.warning("Skipping BCR calculation (preparation failed)")

        # Generate final report
        self.generate_pipeline_report()

    def generate_pipeline_report(self):
        """
        Generate pipeline execution report
        """
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE EXECUTION REPORT")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time']}")
        logger.info(f"End time: {end_time}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("")
        logger.info("RESULTS:")
        logger.info(f"  TransXChange files processed: {self.stats['transxchange_files_processed']}")
        logger.info(f"  Route links extracted: {self.stats['route_links_extracted']:,}")
        logger.info(f"  Trips extracted: {self.stats['trips_extracted']:,}")
        logger.info(f"  Regions processed: {len(self.stats['regions_processed'])}")
        logger.info(f"  BCR calculator ready: {self.stats['bcr_ready']}")

        if self.stats['errors']:
            logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.warning(f"  - {error}")
        else:
            logger.success("\n✓ Pipeline completed successfully with no errors")

        logger.info("=" * 80)


def main():
    """
    Main execution function
    """
    pipeline = TransXChangeAndBCRPipeline()
    pipeline.run_full_pipeline()


if __name__ == '__main__':
    main()
