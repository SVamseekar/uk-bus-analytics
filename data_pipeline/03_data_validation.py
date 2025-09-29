"""
UK Bus Analytics - Data Validation & Quality Assessment
Validates processed data against quality thresholds
Generates comprehensive quality reports
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
import json

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DATA_PROCESSED, DATA_QUALITY_THRESHOLDS,
    VALIDATION_PATTERNS, LOGS_DIR
)

logger.add(LOGS_DIR / "validation_{time}.log",
          rotation="1 day", retention="30 days")


class DataQualityValidator:
    """
    Comprehensive data quality validation for UK transport data
    Checks completeness, accuracy, consistency, and validity
    """
    
    def __init__(self):
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'checks_passed': 0,
            'checks_failed': 0,
            'checks_warned': 0,
            'stop_validation': {},
            'route_validation': {},
            'demographic_validation': {},
            'overall_quality_score': 0.0
        }
        self.data = {}
    
    def load_processed_data(self):
        """Load processed data for validation"""
        logger.info("Loading processed data for validation")
        
        required_files = {
            'stops': DATA_PROCESSED / 'stops_processed.csv',
            'routes': DATA_PROCESSED / 'routes_processed.csv',
            'services': DATA_PROCESSED / 'services_processed.csv'
        }
        
        for data_type, file_path in required_files.items():
            if file_path.exists():
                try:
                    self.data[data_type] = pd.read_csv(file_path)
                    logger.info(f"Loaded {data_type}: {len(self.data[data_type])} records")
                except Exception as e:
                    logger.error(f"Failed to load {data_type}: {e}")
            else:
                logger.warning(f"File not found: {file_path}")
        
        return len(self.data) > 0
    
    def validate_stops_completeness(self):
        """Validate stops data completeness"""
        logger.info("Validating stops completeness")
        
        if 'stops' not in self.data:
            self._record_check('stops_available', False, 'critical',
                             "No stops data available")
            return
        
        stops_df = self.data['stops']
        results = {}
        
        # Check minimum record count
        min_stops = DATA_QUALITY_THRESHOLDS['gtfs']['min_stops_total']
        results['sufficient_records'] = len(stops_df) >= min_stops
        
        if results['sufficient_records']:
            self._record_check('stops_count', True, 'info',
                             f"Sufficient stops: {len(stops_df)}")
        else:
            self._record_check('stops_count', False, 'warning',
                             f"Low stop count: {len(stops_df)} < {min_stops}")
        
        # Check required fields
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            field_present = field in stops_df.columns
            results[f'{field}_present'] = field_present
            
            if field_present:
                missing_count = stops_df[field].isna().sum()
                missing_pct = (missing_count / len(stops_df)) * 100
                
                results[f'{field}_completeness'] = 100 - missing_pct
                
                if missing_pct == 0:
                    self._record_check(f'{field}_complete', True, 'info',
                                     f"No missing {field} values")
                elif missing_pct < 5:
                    self._record_check(f'{field}_complete', True, 'warning',
                                     f"{missing_pct:.1f}% missing {field}")
                else:
                    self._record_check(f'{field}_complete', False, 'critical',
                                     f"{missing_pct:.1f}% missing {field}")
            else:
                self._record_check(f'{field}_present', False, 'critical',
                                 f"Required field missing: {field}")
        
        # Check for duplicates
        if 'stop_id' in stops_df.columns:
            duplicate_count = stops_df['stop_id'].duplicated().sum()
            results['duplicates'] = duplicate_count
            
            if duplicate_count == 0:
                self._record_check('stops_unique', True, 'info',
                                 "No duplicate stop IDs")
            else:
                self._record_check('stops_unique', False, 'warning',
                                 f"{duplicate_count} duplicate stop IDs found")
        
        self.validation_results['stop_validation']['completeness'] = results
    
    def validate_stops_accuracy(self):
        """Validate stops coordinate accuracy"""
        logger.info("Validating stops coordinate accuracy")
        
        if 'stops' not in self.data:
            return
        
        stops_df = self.data['stops']
        results = {}
        
        if 'latitude' not in stops_df.columns or 'longitude' not in stops_df.columns:
            self._record_check('coordinates_available', False, 'critical',
                             "Coordinate columns missing")
            return
        
        # Check UK coordinate bounds
        uk_bounds = DATA_QUALITY_THRESHOLDS['gtfs']['coordinate_bounds']
        
        valid_lat = (
            (stops_df['latitude'] >= uk_bounds['min_lat']) &
            (stops_df['latitude'] <= uk_bounds['max_lat'])
        )
        valid_lon = (
            (stops_df['longitude'] >= uk_bounds['min_lon']) &
            (stops_df['longitude'] <= uk_bounds['max_lon'])
        )
        valid_coords = valid_lat & valid_lon
        
        invalid_count = (~valid_coords).sum()
        invalid_pct = (invalid_count / len(stops_df)) * 100
        
        results['valid_uk_coordinates'] = 100 - invalid_pct
        
        if invalid_pct == 0:
            self._record_check('coordinate_bounds', True, 'info',
                             "All coordinates within UK bounds")
        elif invalid_pct < 1:
            self._record_check('coordinate_bounds', True, 'warning',
                             f"{invalid_pct:.2f}% coordinates outside UK bounds")
        else:
            self._record_check('coordinate_bounds', False, 'critical',
                             f"{invalid_pct:.1f}% coordinates outside UK bounds")
        
        # Check coordinate precision
        if valid_coords.any():
            lat_precision = stops_df.loc[valid_coords, 'latitude'].apply(
                lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0
            ).mean()
            lon_precision = stops_df.loc[valid_coords, 'longitude'].apply(
                lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0
            ).mean()
            
            results['avg_coordinate_precision'] = (lat_precision + lon_precision) / 2
            
            min_precision = DATA_QUALITY_THRESHOLDS['geographic']['coordinate_precision']
            if results['avg_coordinate_precision'] >= min_precision:
                self._record_check('coordinate_precision', True, 'info',
                                 f"Good coordinate precision: {results['avg_coordinate_precision']:.1f} decimals")
            else:
                self._record_check('coordinate_precision', False, 'warning',
                                 f"Low coordinate precision: {results['avg_coordinate_precision']:.1f} decimals")
        
        self.validation_results['stop_validation']['accuracy'] = results
    
    def validate_stops_consistency(self):
        """Validate internal consistency of stops data"""
        logger.info("Validating stops consistency")
        
        if 'stops' not in self.data:
            return
        
        stops_df = self.data['stops']
        results = {}
        
        # Check for stops with same coordinates
        if 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
            coord_duplicates = stops_df.duplicated(subset=['latitude', 'longitude']).sum()
            results['coordinate_duplicates'] = coord_duplicates
            
            if coord_duplicates == 0:
                self._record_check('unique_locations', True, 'info',
                                 "All stops have unique coordinates")
            elif coord_duplicates < len(stops_df) * 0.05:  # Less than 5%
                self._record_check('unique_locations', True, 'warning',
                                 f"{coord_duplicates} stops share coordinates")
            else:
                self._record_check('unique_locations', False, 'warning',
                                 f"{coord_duplicates} stops share coordinates (>5%)")
        
        # Check name consistency
        if 'name' in stops_df.columns or 'stop_name' in stops_df.columns:
            name_col = 'name' if 'name' in stops_df.columns else 'stop_name'
            
            missing_names = stops_df[name_col].isna().sum()
            missing_names_pct = (missing_names / len(stops_df)) * 100
            
            results['missing_names_pct'] = missing_names_pct
            
            if missing_names_pct < 10:
                self._record_check('stop_names', True, 'info',
                                 f"{100 - missing_names_pct:.1f}% stops have names")
            else:
                self._record_check('stop_names', False, 'warning',
                                 f"{missing_names_pct:.1f}% stops missing names")
        
        self.validation_results['stop_validation']['consistency'] = results
    
    def validate_routes(self):
        """Validate routes data"""
        logger.info("Validating routes data")
        
        if 'routes' not in self.data:
            logger.warning("No routes data to validate")
            return
        
        routes_df = self.data['routes']
        results = {}
        
        # Basic counts
        results['total_routes'] = len(routes_df)
        
        if len(routes_df) > 0:
            self._record_check('routes_available', True, 'info',
                             f"{len(routes_df)} routes found")
        else:
            self._record_check('routes_available', False, 'warning',
                             "No routes data available")
            return
        
        # Check for route identifiers
        id_columns = ['route_id', 'service_code']
        for col in id_columns:
            if col in routes_df.columns:
                unique_count = routes_df[col].nunique()
                results[f'unique_{col}'] = unique_count
                self._record_check(f'{col}_present', True, 'info',
                                 f"{unique_count} unique {col}s")
                break
        
        self.validation_results['route_validation'] = results
    
    def validate_demographic_data(self):
        """Validate demographic data integration"""
        logger.info("Validating demographic data")
        
        if 'stops' not in self.data:
            return
        
        stops_df = self.data['stops']
        results = {}
        
        # Check for LSOA codes
        lsoa_columns = ['lsoa_code', 'LSOA21CD', 'LSOA11CD']
        lsoa_col = None
        
        for col in lsoa_columns:
            if col in stops_df.columns:
                lsoa_col = col
                break
        
        if lsoa_col:
            lsoa_coverage = stops_df[lsoa_col].notna().sum()
            lsoa_pct = (lsoa_coverage / len(stops_df)) * 100
            
            results['lsoa_coverage_pct'] = lsoa_pct
            
            if lsoa_pct > 80:
                self._record_check('lsoa_coverage', True, 'info',
                                 f"{lsoa_pct:.1f}% stops have LSOA codes")
            elif lsoa_pct > 50:
                self._record_check('lsoa_coverage', True, 'warning',
                                 f"{lsoa_pct:.1f}% stops have LSOA codes")
            else:
                self._record_check('lsoa_coverage', False, 'warning',
                                 f"Low LSOA coverage: {lsoa_pct:.1f}%")
        else:
            self._record_check('lsoa_available', False, 'warning',
                             "No LSOA codes found in stops data")
        
        # Check for demographic indicators
        demographic_indicators = [
            'population', 'total_population', 'imd_score', 
            'imd_rank', 'income', 'unemployment'
        ]
        
        found_indicators = []
        for indicator in demographic_indicators:
            if indicator in stops_df.columns:
                found_indicators.append(indicator)
                
                non_null = stops_df[indicator].notna().sum()
                coverage_pct = (non_null / len(stops_df)) * 100
                
                if coverage_pct > 50:
                    self._record_check(f'{indicator}_available', True, 'info',
                                     f"{indicator}: {coverage_pct:.1f}% coverage")
        
        results['demographic_indicators_found'] = found_indicators
        results['demographic_indicators_count'] = len(found_indicators)
        
        if len(found_indicators) > 0:
            self._record_check('demographic_integration', True, 'info',
                             f"Found {len(found_indicators)} demographic indicators")
        else:
            self._record_check('demographic_integration', False, 'warning',
                             "No demographic indicators found")
        
        self.validation_results['demographic_validation'] = results
    
    def calculate_quality_score(self):
        """Calculate overall data quality score"""
        logger.info("Calculating overall quality score")
        
        total_checks = (self.validation_results['checks_passed'] + 
                       self.validation_results['checks_failed'] +
                       self.validation_results['checks_warned'])
        
        if total_checks == 0:
            self.validation_results['overall_quality_score'] = 0.0
            return
        
        # Weighted scoring
        # Passed checks: 100% weight
        # Warnings: 50% weight
        # Failed checks: 0% weight
        
        weighted_score = (
            self.validation_results['checks_passed'] * 1.0 +
            self.validation_results['checks_warned'] * 0.5 +
            self.validation_results['checks_failed'] * 0.0
        )
        
        quality_score = (weighted_score / total_checks) * 100
        self.validation_results['overall_quality_score'] = round(quality_score, 2)
        
        logger.info(f"Overall quality score: {quality_score:.2f}%")
    
    def _convert_to_serializable(self, obj):
        """Convert numpy/pandas types to JSON-serializable Python types"""
        if isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def _record_check(self, check_name: str, passed: bool, level: str, message: str):
        """Record validation check result"""
        if passed:
            if level == 'warning':
                self.validation_results['checks_warned'] += 1
                logger.warning(f"⚠️  {check_name}: {message}")
            else:
                self.validation_results['checks_passed'] += 1
                logger.info(f"✓ {check_name}: {message}")
        else:
            self.validation_results['checks_failed'] += 1
            logger.error(f"✗ {check_name}: {message}")
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        logger.info("Generating validation report")
        
        report = {
            'validation_summary': {
                'timestamp': self.validation_results['timestamp'],
                'checks_passed': int(self.validation_results['checks_passed']),
                'checks_failed': int(self.validation_results['checks_failed']),
                'checks_warned': int(self.validation_results['checks_warned']),
                'quality_score': float(self.validation_results['overall_quality_score'])
            },
            'stop_validation': self._convert_to_serializable(self.validation_results.get('stop_validation', {})),
            'route_validation': self._convert_to_serializable(self.validation_results.get('route_validation', {})),
            'demographic_validation': self._convert_to_serializable(self.validation_results.get('demographic_validation', {}))
        }
        
        # Save report
        report_path = DATA_PROCESSED / 'validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.success(f"Validation report saved: {report_path}")
        
        # Create human-readable summary
        summary_path = DATA_PROCESSED / 'validation_summary.txt'
        with open(summary_path, 'w') as f:
            f.write("UK BUS ANALYTICS - DATA VALIDATION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Validation Date: {self.validation_results['timestamp']}\n")
            f.write(f"Quality Score: {self.validation_results['overall_quality_score']}%\n\n")
            
            f.write("Check Results:\n")
            f.write(f"  ✓ Passed: {self.validation_results['checks_passed']}\n")
            f.write(f"  ⚠️  Warnings: {self.validation_results['checks_warned']}\n")
            f.write(f"  ✗ Failed: {self.validation_results['checks_failed']}\n\n")
            
            if 'stops' in self.data:
                f.write(f"Stops Data:\n")
                f.write(f"  Total records: {len(self.data['stops'])}\n")
                
                if 'stop_validation' in self.validation_results:
                    sv = self.validation_results['stop_validation']
                    if 'completeness' in sv:
                        f.write(f"  Completeness checks: {len(sv['completeness'])}\n")
                    if 'accuracy' in sv:
                        f.write(f"  Accuracy checks: {len(sv['accuracy'])}\n")
            
            if 'routes' in self.data:
                f.write(f"\nRoutes Data:\n")
                f.write(f"  Total routes: {len(self.data['routes'])}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        logger.success(f"Validation summary saved: {summary_path}")
        
        return report
    
    def run_full_validation(self):
        """Run complete validation pipeline"""
        logger.info("Starting data validation pipeline")
        start_time = datetime.now()
        
        # Load data
        if not self.load_processed_data():
            logger.error("Failed to load processed data")
            return None
        
        # Run all validation checks
        self.validate_stops_completeness()
        self.validate_stops_accuracy()
        self.validate_stops_consistency()
        self.validate_routes()
        self.validate_demographic_data()
        
        # Calculate quality score
        self.calculate_quality_score()
        
        # Generate report
        report = self.generate_report()
        
        duration = datetime.now() - start_time
        logger.info(f"Validation completed in {duration}")
        
        return report


def main():
    """Run data validation"""
    try:
        validator = DataQualityValidator()
        report = validator.run_full_validation()
        
        if report is None:
            print("\n❌ Validation failed - no data to validate")
            sys.exit(1)
        
        # Print summary
        print("\n" + "="*60)
        print("UK TRANSPORT DATA VALIDATION SUMMARY")
        print("="*60)
        
        summary = report['validation_summary']
        print(f"\nQuality Score: {summary['quality_score']}%")
        print(f"\nCheck Results:")
        print(f"  ✓ Passed: {summary['checks_passed']}")
        print(f"  ⚠️  Warnings: {summary['checks_warned']}")
        print(f"  ✗ Failed: {summary['checks_failed']}")
        
        # Quality assessment
        score = summary['quality_score']
        if score >= 90:
            status = "🎉 EXCELLENT"
            color = "green"
        elif score >= 75:
            status = "✅ GOOD"
            color = "yellow"
        elif score >= 60:
            status = "⚠️  ACCEPTABLE"
            color = "orange"
        else:
            status = "❌ POOR"
            color = "red"
        
        print(f"\nOverall Assessment: {status}")
        
        if 'stop_validation' in report and report['stop_validation']:
            print(f"\nStop Validation:")
            if 'completeness' in report['stop_validation']:
                comp = report['stop_validation']['completeness']
                print(f"  Completeness: {len([k for k in comp.keys() if comp[k]])} checks passed")
            if 'accuracy' in report['stop_validation']:
                acc = report['stop_validation']['accuracy']
                if 'valid_uk_coordinates' in acc:
                    print(f"  UK Coordinates: {acc['valid_uk_coordinates']:.1f}% valid")
        
        if 'route_validation' in report and report['route_validation']:
            print(f"\nRoute Validation:")
            if 'total_routes' in report['route_validation']:
                print(f"  Total routes: {report['route_validation']['total_routes']}")
        
        if 'demographic_validation' in report and report['demographic_validation']:
            print(f"\nDemographic Integration:")
            demo = report['demographic_validation']
            if 'lsoa_coverage_pct' in demo:
                print(f"  LSOA coverage: {demo['lsoa_coverage_pct']:.1f}%")
            if 'demographic_indicators_count' in demo:
                print(f"  Indicators found: {demo['demographic_indicators_count']}")
        
        print("\n" + "="*60)
        print("\nDetailed reports saved:")
        print("  - data_pipeline/processed/validation_report.json")
        print("  - data_pipeline/processed/validation_summary.txt")
        
        if score >= 60:
            print("\n✅ Data quality acceptable - ready for analysis")
            print("\nNext steps:")
            print("1. Review validation report for warnings")
            print("2. Proceed to descriptive analysis")
            print("3. Compute KPIs and correlations")
        else:
            print("\n⚠️  Data quality needs improvement")
            print("\nRecommended actions:")
            print("1. Review validation report for critical issues")
            print("2. Re-run data ingestion if needed")
            print("3. Address data quality issues before analysis")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        logger.exception("Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()