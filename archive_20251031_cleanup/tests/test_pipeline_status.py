#!/usr/bin/env python3
"""
Pipeline Status Checker
Comprehensive test to verify if the UK Bus Analytics pipeline is working correctly
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

class PipelineStatusChecker:
    """Check status of all pipeline components"""

    def __init__(self):
        self.data_raw = PROJECT_ROOT / 'data_pipeline' / 'raw'
        self.data_processed = PROJECT_ROOT / 'data_pipeline' / 'processed'
        self.config_dir = PROJECT_ROOT / 'config'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'warnings': [],
            'errors': [],
            'summary': {}
        }

    def test_directory_structure(self):
        """Test 1: Verify directory structure exists"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Directory Structure")
        logger.info("="*60)

        required_dirs = [
            self.data_raw,
            self.data_processed,
            self.config_dir,
            self.data_raw / 'regions',
            self.data_raw / 'demographic',
            self.data_processed / 'regions'
        ]

        all_exist = True
        for dir_path in required_dirs:
            if dir_path.exists():
                logger.success(f"✓ {dir_path.relative_to(PROJECT_ROOT)}")
            else:
                logger.error(f"✗ Missing: {dir_path.relative_to(PROJECT_ROOT)}")
                all_exist = False
                self.results['errors'].append(f"Missing directory: {dir_path}")

        if all_exist:
            self.results['tests_passed'] += 1
            logger.success("✓ TEST PASSED: All directories exist")
        else:
            self.results['tests_failed'] += 1
            logger.error("✗ TEST FAILED: Missing directories")

        return all_exist

    def test_raw_data_availability(self):
        """Test 2: Check raw data files"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Raw Data Availability")
        logger.info("="*60)

        regions_dir = self.data_raw / 'regions'

        if not regions_dir.exists():
            logger.error("✗ Regions directory not found")
            self.results['tests_failed'] += 1
            return False

        regions = {}
        for region_dir in regions_dir.iterdir():
            if region_dir.is_dir():
                data_files = list(region_dir.glob('*.zip')) + list(region_dir.glob('*.xml'))
                regions[region_dir.name] = len(data_files)
                logger.info(f"  {region_dir.name}: {len(data_files)} files")

        total_files = sum(regions.values())
        self.results['summary']['regions_count'] = len(regions)
        self.results['summary']['total_transport_files'] = total_files

        if total_files > 0:
            logger.success(f"✓ Found {total_files} transport files across {len(regions)} regions")
            self.results['tests_passed'] += 1
            return True
        else:
            logger.error("✗ No transport data files found")
            self.results['tests_failed'] += 1
            return False

    def test_demographic_data(self):
        """Test 3: Check demographic data"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Demographic Data")
        logger.info("="*60)

        demo_dir = self.data_raw / 'demographic'

        if not demo_dir.exists():
            logger.error("✗ Demographic directory not found")
            self.results['tests_failed'] += 1
            return False

        csv_files = list(demo_dir.glob('*.csv'))
        datasets = {}

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, nrows=5)  # Just check first 5 rows
                datasets[csv_file.stem] = {
                    'file': csv_file.name,
                    'columns': len(df.columns),
                    'readable': True
                }
                logger.success(f"✓ {csv_file.stem}: {len(df.columns)} columns")
            except Exception as e:
                logger.error(f"✗ Failed to read {csv_file.name}: {e}")
                datasets[csv_file.stem] = {
                    'file': csv_file.name,
                    'readable': False,
                    'error': str(e)
                }
                self.results['errors'].append(f"Cannot read {csv_file.name}: {e}")

        self.results['summary']['demographic_datasets'] = len(datasets)
        readable_count = sum(1 for d in datasets.values() if d.get('readable', False))

        if readable_count == len(datasets) and len(datasets) > 0:
            logger.success(f"✓ All {len(datasets)} demographic datasets readable")
            self.results['tests_passed'] += 1
            return True
        elif readable_count > 0:
            logger.warning(f"⚠ Only {readable_count}/{len(datasets)} datasets readable")
            self.results['warnings'].append(f"Some demographic datasets unreadable")
            self.results['tests_failed'] += 1
            return False
        else:
            logger.error("✗ No readable demographic datasets")
            self.results['tests_failed'] += 1
            return False

    def test_processed_data(self):
        """Test 4: Check processed data"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Processed Data")
        logger.info("="*60)

        processed_regions = self.data_processed / 'regions'

        if not processed_regions.exists():
            logger.warning("⚠ No processed data directory found")
            self.results['warnings'].append("No processed data yet")
            self.results['summary']['processed_regions'] = 0
            # Not a failure - might not have run processing yet
            return True

        processed_data = {}
        total_stops = 0
        total_routes = 0

        for region_dir in processed_regions.iterdir():
            if region_dir.is_dir():
                stops_file = region_dir / f'{region_dir.name}_stops_cleaned.csv'
                routes_file = region_dir / f'{region_dir.name}_routes.csv'

                region_info = {'stops': 0, 'routes': 0}

                if stops_file.exists():
                    try:
                        df = pd.read_csv(stops_file)
                        region_info['stops'] = len(df)
                        total_stops += len(df)
                    except Exception as e:
                        logger.error(f"✗ Failed to read {stops_file.name}: {e}")

                if routes_file.exists():
                    try:
                        df = pd.read_csv(routes_file)
                        region_info['routes'] = len(df)
                        total_routes += len(df)
                    except Exception as e:
                        logger.error(f"✗ Failed to read {routes_file.name}: {e}")

                processed_data[region_dir.name] = region_info
                logger.info(f"  {region_dir.name}: {region_info['stops']} stops, {region_info['routes']} routes")

        self.results['summary']['processed_regions'] = len(processed_data)
        self.results['summary']['total_stops_processed'] = total_stops
        self.results['summary']['total_routes_processed'] = total_routes

        if total_stops > 0:
            logger.success(f"✓ Processed {total_stops} stops, {total_routes} routes across {len(processed_data)} regions")
            self.results['tests_passed'] += 1
            return True
        else:
            logger.warning("⚠ No processed data found - pipeline hasn't been run yet")
            self.results['warnings'].append("No processed data - run processing pipeline")
            return True  # Not a failure, just not run yet

    def test_config_files(self):
        """Test 5: Check configuration files"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Configuration Files")
        logger.info("="*60)

        config_file = self.config_dir / 'ingestion_config.yaml'

        if not config_file.exists():
            logger.error("✗ Configuration file not found")
            self.results['tests_failed'] += 1
            return False

        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            regions_count = len(config.get('regions', {}))
            logger.success(f"✓ Configuration loaded: {regions_count} regions defined")
            self.results['summary']['configured_regions'] = regions_count
            self.results['tests_passed'] += 1
            return True
        except Exception as e:
            logger.error(f"✗ Failed to load configuration: {e}")
            self.results['tests_failed'] += 1
            return False

    def test_parsers_importable(self):
        """Test 6: Check if parsers can be imported"""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Parser Imports")
        logger.info("="*60)

        try:
            from utils.gtfs_parser import UKTransportParser
            logger.success("✓ UKTransportParser imported successfully")
            self.results['tests_passed'] += 1
            return True
        except Exception as e:
            logger.error(f"✗ Failed to import UKTransportParser: {e}")
            self.results['errors'].append(f"Import error: {e}")
            self.results['tests_failed'] += 1
            return False

    def test_sample_file_parsing(self):
        """Test 7: Try parsing a sample file"""
        logger.info("\n" + "="*60)
        logger.info("TEST 7: Sample File Parsing")
        logger.info("="*60)

        try:
            from utils.gtfs_parser import UKTransportParser

            # Find first available data file
            regions_dir = self.data_raw / 'regions'
            sample_file = None

            for region_dir in regions_dir.iterdir():
                if region_dir.is_dir():
                    files = list(region_dir.glob('*.zip')) + list(region_dir.glob('*.xml'))
                    if files:
                        sample_file = files[0]
                        break

            if not sample_file:
                logger.warning("⚠ No sample file found to test parsing")
                return True  # Not a failure

            logger.info(f"Testing with: {sample_file.name}")

            parser = UKTransportParser(sample_file)
            format_type = parser.detect_format()
            logger.info(f"  Detected format: {format_type}")

            if format_type != 'unknown':
                logger.success(f"✓ Successfully detected format: {format_type}")
                self.results['tests_passed'] += 1
                return True
            else:
                logger.warning(f"⚠ Unknown format for {sample_file.name}")
                self.results['warnings'].append(f"Unknown format: {sample_file.name}")
                return True  # Not necessarily a failure

        except Exception as e:
            logger.error(f"✗ Parsing test failed: {e}")
            self.results['errors'].append(f"Parsing error: {e}")
            self.results['tests_failed'] += 1
            return False

    def generate_report(self):
        """Generate final status report"""
        logger.info("\n" + "="*60)
        logger.info("STATUS REPORT")
        logger.info("="*60)

        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        pass_rate = (self.results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"Tests Passed: {self.results['tests_passed']}/{total_tests} ({pass_rate:.1f}%)")
        logger.info(f"Tests Failed: {self.results['tests_failed']}")
        logger.info(f"Warnings: {len(self.results['warnings'])}")
        logger.info(f"Errors: {len(self.results['errors'])}")

        logger.info("\nData Summary:")
        for key, value in self.results['summary'].items():
            logger.info(f"  {key}: {value}")

        if self.results['warnings']:
            logger.warning("\nWarnings:")
            for warning in self.results['warnings']:
                logger.warning(f"  ⚠ {warning}")

        if self.results['errors']:
            logger.error("\nErrors:")
            for error in self.results['errors']:
                logger.error(f"  ✗ {error}")

        # Overall status
        logger.info("\n" + "="*60)
        if self.results['tests_failed'] == 0:
            logger.success("✓ OVERALL STATUS: HEALTHY")
            logger.info("Pipeline is ready to run!")
        elif self.results['tests_failed'] <= 2:
            logger.warning("⚠ OVERALL STATUS: MINOR ISSUES")
            logger.info("Pipeline may work with some limitations")
        else:
            logger.error("✗ OVERALL STATUS: CRITICAL ISSUES")
            logger.info("Pipeline needs attention before running")
        logger.info("="*60)

        # Save report
        report_file = PROJECT_ROOT / 'pipeline_status_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"\nDetailed report saved to: {report_file.name}")

        return self.results['tests_failed'] == 0

def main():
    """Run all status checks"""
    logger.info("🚀 UK Bus Analytics - Pipeline Status Checker")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    checker = PipelineStatusChecker()

    # Run all tests
    checker.test_directory_structure()
    checker.test_raw_data_availability()
    checker.test_demographic_data()
    checker.test_processed_data()
    checker.test_config_files()
    checker.test_parsers_importable()
    checker.test_sample_file_parsing()

    # Generate final report
    success = checker.generate_report()

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
