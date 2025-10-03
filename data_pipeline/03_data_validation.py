"""
Dynamic UK Bus Analytics Data Validation Pipeline
Validates all processed data without hardcoding
Generates quality reports for all regions and datasets
"""
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DATA_PROCESSED, DATA_QUALITY_THRESHOLDS,
    VALIDATION_PATTERNS, LOGS_DIR
)

logger.add(LOGS_DIR / "validation_{time}.log", rotation="1 day", retention="30 days")


class DynamicDataValidationPipeline:
    """
    Fully dynamic data validation pipeline
    Discovers and validates all processed data
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize validation pipeline"""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'ingestion_config.yaml'
        self.config = self._load_config()
        
        # Validation results
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'regions': {},
            'overall': {
                'checks_passed': 0,
                'checks_failed': 0,
                'checks_warned': 0
            },
            'quality_scores': {},
            'summary': {}
        }
    
    def _load_config(self) -> Dict:
        """Load configuration"""
        if not self.config_path.exists():
            return {'regions': {}}
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def discover_processed_files(self) -> Dict[str, Dict[str, Path]]:
        """
        Dynamically discover all processed data files
        """
        logger.info("Discovering processed data files...")
        
        regions_dir = DATA_PROCESSED / 'regions'
        if not regions_dir.exists():
            logger.error(f"Processed regions directory not found: {regions_dir}")
            return {}
        
        discovered = {}
        
        for region_dir in regions_dir.iterdir():
            if region_dir.is_dir():
                region_code = region_dir.name
                region_files = {}
                
                for file in region_dir.glob('*_processed.csv'):
                    data_type = file.stem.replace('_processed', '')
                    region_files[data_type] = file
                
                if region_files:
                    discovered[region_code] = region_files
                    logger.info(f"✓ {region_code}: {len(region_files)} processed files")
        
        logger.success(f"Discovered {len(discovered)} regions with processed data")
        return discovered
    
    def validate_data_completeness(self, df: pd.DataFrame, data_type: str, 
                                   region_code: str) -> Dict:
        """
        Validate data completeness dynamically
        Checks for missing values and record counts
        """
        results = {
            'total_records': len(df),
            'column_count': len(df.columns),
            'missing_data': {},
            'issues': []
        }
        
        # Check each column for completeness
        for column in df.columns:
            missing_count = df[column].isna().sum()
            missing_pct = (missing_count / len(df)) * 100 if len(df) > 0 else 0
            
            if missing_pct > 0:
                results['missing_data'][column] = {
                    'count': int(missing_count),
                    'percentage': round(missing_pct, 2)
                }
                
                # Flag high missing data
                if missing_pct > 50:
                    results['issues'].append(f"{column}: {missing_pct:.1f}% missing (critical)")
                    self._record_check(
                        f"{region_code}_{data_type}_{column}_completeness",
                        False, 'critical',
                        f"{column} has {missing_pct:.1f}% missing data"
                    )
                elif missing_pct > 20:
                    results['issues'].append(f"{column}: {missing_pct:.1f}% missing (warning)")
                    self._record_check(
                        f"{region_code}_{data_type}_{column}_completeness",
                        True, 'warning',
                        f"{column} has {missing_pct:.1f}% missing data"
                    )
        
        # Check minimum record threshold
        min_records = self._get_min_records_threshold(data_type)
        if len(df) < min_records:
            results['issues'].append(f"Low record count: {len(df)} < {min_records}")
            self._record_check(
                f"{region_code}_{data_type}_record_count",
                False, 'warning',
                f"Only {len(df)} records (expected >{min_records})"
            )
        else:
            self._record_check(
                f"{region_code}_{data_type}_record_count",
                True, 'info',
                f"Sufficient records: {len(df)}"
            )
        
        return results
    
    def _get_min_records_threshold(self, data_type: str) -> int:
        """Get minimum record threshold dynamically"""
        thresholds = {
            'stops': DATA_QUALITY_THRESHOLDS.get('gtfs', {}).get('min_stops_total', 100),
            'routes': 5,
            'services': 5,
            'trips': 10
        }
        return thresholds.get(data_type, 1)
    
    def validate_stops_coordinates(self, df: pd.DataFrame, region_code: str) -> Dict:
        """
        Validate stop coordinates dynamically
        """
        results = {
            'has_coordinates': False,
            'valid_coordinates': 0,
            'invalid_coordinates': 0,
            'coordinate_precision': 0,
            'issues': []
        }
        
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            results['issues'].append("Missing coordinate columns")
            self._record_check(
                f"{region_code}_stops_coordinates_present",
                False, 'critical',
                "No coordinate columns found"
            )
            return results
        
        results['has_coordinates'] = True
        
        # Validate UK bounds
        uk_bounds = DATA_QUALITY_THRESHOLDS['gtfs']['coordinate_bounds']
        
        valid_mask = (
            (df['latitude'] >= uk_bounds['min_lat']) &
            (df['latitude'] <= uk_bounds['max_lat']) &
            (df['longitude'] >= uk_bounds['min_lon']) &
            (df['longitude'] <= uk_bounds['max_lon']) &
            df['latitude'].notna() &
            df['longitude'].notna()
        )
        
        results['valid_coordinates'] = int(valid_mask.sum())
        results['invalid_coordinates'] = int((~valid_mask).sum())
        
        valid_pct = (results['valid_coordinates'] / len(df)) * 100 if len(df) > 0 else 0
        
        if valid_pct < 50:
            results['issues'].append(f"Only {valid_pct:.1f}% have valid UK coordinates")
            self._record_check(
                f"{region_code}_stops_coordinate_validity",
                False, 'critical',
                f"Only {valid_pct:.1f}% valid coordinates"
            )
        elif valid_pct < 80:
            self._record_check(
                f"{region_code}_stops_coordinate_validity",
                True, 'warning',
                f"{valid_pct:.1f}% valid coordinates"
            )
        else:
            self._record_check(
                f"{region_code}_stops_coordinate_validity",
                True, 'info',
                f"{valid_pct:.1f}% valid coordinates"
            )
        
        # Check coordinate precision
        valid_coords = df[valid_mask]
        if len(valid_coords) > 0:
            lat_precision = valid_coords['latitude'].apply(
                lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0
            ).mean()
            lon_precision = valid_coords['longitude'].apply(
                lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0
            ).mean()
            
            results['coordinate_precision'] = round((lat_precision + lon_precision) / 2, 2)
            
            min_precision = DATA_QUALITY_THRESHOLDS['geographic']['coordinate_precision']
            if results['coordinate_precision'] >= min_precision:
                self._record_check(
                    f"{region_code}_stops_coordinate_precision",
                    True, 'info',
                    f"Good precision: {results['coordinate_precision']} decimals"
                )
            else:
                self._record_check(
                    f"{region_code}_stops_coordinate_precision",
                    False, 'warning',
                    f"Low precision: {results['coordinate_precision']} decimals"
                )
        
        return results
    
    def validate_lsoa_coverage(self, df: pd.DataFrame, region_code: str) -> Dict:
        """
        Validate LSOA code coverage dynamically
        """
        results = {
            'has_lsoa': False,
            'lsoa_coverage': 0,
            'valid_lsoa_codes': 0,
            'issues': []
        }
        
        lsoa_column = None
        for col in ['lsoa_code', 'LSOA21CD', 'LSOA11CD']:
            if col in df.columns:
                lsoa_column = col
                break
        
        if not lsoa_column:
            results['issues'].append("No LSOA code column found")
            self._record_check(
                f"{region_code}_lsoa_present",
                False, 'warning',
                "No LSOA codes found"
            )
            return results
        
        results['has_lsoa'] = True
        
        # Calculate coverage
        lsoa_coverage = df[lsoa_column].notna().sum()
        coverage_pct = (lsoa_coverage / len(df)) * 100 if len(df) > 0 else 0
        results['lsoa_coverage'] = round(coverage_pct, 2)
        
        if coverage_pct < 50:
            results['issues'].append(f"Low LSOA coverage: {coverage_pct:.1f}%")
            self._record_check(
                f"{region_code}_lsoa_coverage",
                False, 'warning',
                f"Low LSOA coverage: {coverage_pct:.1f}%"
            )
        elif coverage_pct < 80:
            self._record_check(
                f"{region_code}_lsoa_coverage",
                True, 'warning',
                f"Moderate LSOA coverage: {coverage_pct:.1f}%"
            )
        else:
            self._record_check(
                f"{region_code}_lsoa_coverage",
                True, 'info',
                f"Good LSOA coverage: {coverage_pct:.1f}%"
            )
        
        # Validate LSOA code format
        if lsoa_column and df[lsoa_column].notna().any():
            valid_pattern = VALIDATION_PATTERNS.get('lsoa_code_2021', r'^E0[12]\d{6}')
            
            valid_codes = df[df[lsoa_column].notna()][lsoa_column].apply(
                lambda x: bool(pd.Series(str(x)).str.match(valid_pattern).iloc[0])
            )
            
            results['valid_lsoa_codes'] = int(valid_codes.sum())
            valid_pct = (results['valid_lsoa_codes'] / lsoa_coverage) * 100 if lsoa_coverage > 0 else 0
            
            if valid_pct < 50:
                results['issues'].append(f"Invalid LSOA format: {100-valid_pct:.1f}%")
        
        return results
    
    def validate_demographic_integration(self, df: pd.DataFrame, region_code: str) -> Dict:
        """
        Validate demographic data integration dynamically
        """
        results = {
            'demographic_indicators_found': [],
            'coverage_by_indicator': {},
            'issues': []
        }
        
        # Dynamically detect demographic columns
        demographic_patterns = {
            'population': ['population', 'pop_', 'resident'],
            'income': ['income', 'median_income', 'household_income'],
            'unemployment': ['unemployment', 'jobless', 'claimant'],
            'deprivation': ['imd', 'deprivation', 'index_multiple'],
            'age': ['age', 'elderly', 'young'],
            'car_ownership': ['car', 'vehicle', 'ownership']
        }
        
        for indicator_type, patterns in demographic_patterns.items():
            matching_cols = [col for col in df.columns 
                           if any(pattern.lower() in col.lower() for pattern in patterns)]
            
            if matching_cols:
                results['demographic_indicators_found'].append(indicator_type)
                
                # Calculate coverage for first matching column
                col = matching_cols[0]
                coverage = df[col].notna().sum()
                coverage_pct = (coverage / len(df)) * 100 if len(df) > 0 else 0
                results['coverage_by_indicator'][indicator_type] = round(coverage_pct, 2)
                
                if coverage_pct > 50:
                    self._record_check(
                        f"{region_code}_demographic_{indicator_type}",
                        True, 'info',
                        f"{indicator_type}: {coverage_pct:.1f}% coverage"
                    )
        
        if not results['demographic_indicators_found']:
            results['issues'].append("No demographic indicators found")
            self._record_check(
                f"{region_code}_demographic_integration",
                False, 'warning',
                "No demographic data integrated"
            )
        else:
            self._record_check(
                f"{region_code}_demographic_integration",
                True, 'info',
                f"Found {len(results['demographic_indicators_found'])} indicators"
            )
        
        return results
    
    def validate_region(self, region_code: str, region_files: Dict[str, Path]) -> Dict:
        """
        Validate all data for a specific region
        """
        region_config = self.config['regions'].get(region_code, {})
        region_name = region_config.get('name', region_code)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"VALIDATING: {region_name}")
        logger.info(f"{'='*60}")
        
        region_validation = {
            'region_code': region_code,
            'region_name': region_name,
            'files_validated': [],
            'data_types': {}
        }
        
        for data_type, file_path in region_files.items():
            try:
                logger.info(f"\nValidating: {data_type}")
                
                # Load data
                df = pd.read_csv(file_path)
                
                validation = {
                    'file_path': str(file_path),
                    'completeness': self.validate_data_completeness(df, data_type, region_code)
                }
                
                # Type-specific validations
                if data_type == 'stops':
                    validation['coordinates'] = self.validate_stops_coordinates(df, region_code)
                    validation['lsoa'] = self.validate_lsoa_coverage(df, region_code)
                    validation['demographics'] = self.validate_demographic_integration(df, region_code)
                
                region_validation['data_types'][data_type] = validation
                region_validation['files_validated'].append(data_type)
                
                logger.success(f"✓ Validated {data_type}: {len(df)} records")
                
            except Exception as e:
                logger.error(f"Failed to validate {data_type}: {e}")
                region_validation['data_types'][data_type] = {
                    'error': str(e),
                    'file_path': str(file_path)
                }
        
        return region_validation
    
    def calculate_quality_score(self, region_code: str) -> float:
        """
        Calculate overall quality score for a region
        Based on all validation checks
        """
        region_checks = {
            k: v for k, v in self.validation_results.items()
            if isinstance(k, str) and k.startswith(region_code)
        }
        
        if not region_checks:
            return 0.0
        
        # Count check results
        passed = sum(1 for v in region_checks.values() if v.get('passed', False) and v.get('level') == 'info')
        warned = sum(1 for v in region_checks.values() if v.get('passed', False) and v.get('level') == 'warning')
        failed = sum(1 for v in region_checks.values() if not v.get('passed', True))
        
        total = passed + warned + failed
        
        if total == 0:
            return 0.0
        
        # Weighted scoring
        score = (passed * 1.0 + warned * 0.5) / total * 100
        return round(score, 2)
    
    def _record_check(self, check_name: str, passed: bool, level: str, message: str):
        """
        Record validation check result
        """
        self.validation_results[check_name] = {
            'passed': passed,
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if passed:
            if level == 'warning':
                self.validation_results['overall']['checks_warned'] += 1
                logger.warning(f"⚠️  {check_name}: {message}")
            else:
                self.validation_results['overall']['checks_passed'] += 1
                logger.info(f"✓ {check_name}: {message}")
        else:
            self.validation_results['overall']['checks_failed'] += 1
            logger.error(f"✗ {check_name}: {message}")
    
    def generate_validation_report(self) -> Dict:
        """
        Generate comprehensive validation report
        """
        logger.info("\n" + "="*60)
        logger.info("GENERATING VALIDATION REPORT")
        logger.info("="*60)
        
        # Calculate overall statistics
        total_checks = (
            self.validation_results['overall']['checks_passed'] +
            self.validation_results['overall']['checks_failed'] +
            self.validation_results['overall']['checks_warned']
        )
        
        overall_score = 0.0
        if total_checks > 0:
            weighted_score = (
                self.validation_results['overall']['checks_passed'] * 1.0 +
                self.validation_results['overall']['checks_warned'] * 0.5
            )
            overall_score = round((weighted_score / total_checks) * 100, 2)
        
        report = {
            'validation_summary': {
                'timestamp': self.validation_results['timestamp'],
                'total_regions': len(self.validation_results['regions']),
                'total_checks': total_checks,
                'checks_passed': self.validation_results['overall']['checks_passed'],
                'checks_warned': self.validation_results['overall']['checks_warned'],
                'checks_failed': self.validation_results['overall']['checks_failed'],
                'overall_quality_score': overall_score
            },
            'regional_validation': self.validation_results['regions'],
            'quality_scores': self.validation_results['quality_scores']
        }
        
        # Save detailed report
        report_path = DATA_PROCESSED / 'validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.success(f"Validation report saved: {report_path}")
        
        # Generate human-readable summary
        self._generate_text_summary(report)
        
        return report
    
    def _generate_text_summary(self, report: Dict):
        """
        Generate human-readable validation summary
        """
        summary_path = DATA_PROCESSED / 'validation_summary.txt'
        
        with open(summary_path, 'w') as f:
            f.write("="*60 + "\n")
            f.write("UK BUS ANALYTICS - VALIDATION SUMMARY\n")
            f.write("="*60 + "\n\n")
            
            summary = report['validation_summary']
            f.write(f"Validation Date: {summary['timestamp']}\n")
            f.write(f"Overall Quality Score: {summary['overall_quality_score']}%\n\n")
            
            f.write("Check Results:\n")
            f.write(f"  ✓ Passed: {summary['checks_passed']}\n")
            f.write(f"  ⚠️  Warnings: {summary['checks_warned']}\n")
            f.write(f"  ✗ Failed: {summary['checks_failed']}\n\n")
            
            f.write(f"Regional Breakdown:\n")
            f.write(f"{'Region':<25} {'Quality Score':<15} {'Status'}\n")
            f.write("-"*60 + "\n")
            
            for region_code, score in report['quality_scores'].items():
                region_name = self.config['regions'].get(region_code, {}).get('name', region_code)
                status = "✓ Excellent" if score >= 90 else "✓ Good" if score >= 75 else "⚠ Acceptable" if score >= 60 else "✗ Poor"
                f.write(f"{region_name:<25} {score:>6.1f}%        {status}\n")
            
            f.write("\n" + "="*60 + "\n")
        
        logger.success(f"Summary saved: {summary_path}")
    
    def validate_all_regions(self) -> Dict:
        """
        Validate all processed regions
        Fully dynamic workflow
        """
        logger.info("\n" + "="*60)
        logger.info("DYNAMIC DATA VALIDATION PIPELINE")
        logger.info("="*60)
        
        # Discover processed files
        processed_files = self.discover_processed_files()
        
        if not processed_files:
            logger.error("No processed data files found")
            return {
                'success': False,
                'error': 'No processed data discovered'
            }
        
        logger.info(f"\nValidating {len(processed_files)} regions")
        
        # Validate each region
        for region_code, region_files in processed_files.items():
            region_validation = self.validate_region(region_code, region_files)
            self.validation_results['regions'][region_code] = region_validation
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(region_code)
            self.validation_results['quality_scores'][region_code] = quality_score
            
            logger.info(f"\nQuality Score for {region_code}: {quality_score}%")
        
        # Generate comprehensive report
        report = self.generate_validation_report()
        
        return {
            'success': True,
            'report': report
        }


def main():
    """
    Execute dynamic data validation pipeline
    """
    print("\n" + "="*60)
    print("UK BUS ANALYTICS - DYNAMIC DATA VALIDATION")
    print("="*60)
    print("\nValidating all processed data dynamically\n")
    
    # Initialize pipeline
    pipeline = DynamicDataValidationPipeline()
    
    # Validate all regions
    results = pipeline.validate_all_regions()
    
    if not results['success']:
        print(f"\n❌ Validation failed: {results.get('error')}")
        return
    
    # Print summary
    report = results['report']
    summary = report['validation_summary']
    
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)
    
    print(f"\nOverall Quality Score: {summary['overall_quality_score']}%")
    print(f"\nCheck Results:")
    print(f"  ✓ Passed: {summary['checks_passed']}")
    print(f"  ⚠️  Warnings: {summary['checks_warned']}")
    print(f"  ✗ Failed: {summary['checks_failed']}")
    
    print(f"\nRegions Validated: {summary['total_regions']}")
    
    # Quality assessment
    score = summary['overall_quality_score']
    if score >= 90:
        status = "🎉 EXCELLENT"
    elif score >= 75:
        status = "✅ GOOD"
    elif score >= 60:
        status = "⚠️  ACCEPTABLE"
    else:
        status = "❌ POOR"
    
    print(f"\nOverall Assessment: {status}")
    
    print("\nTop Regions by Quality:")
    sorted_regions = sorted(
        report['quality_scores'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for i, (region_code, score) in enumerate(sorted_regions[:5], 1):
        region_name = pipeline.config['regions'].get(region_code, {}).get('name', region_code)
        print(f"  {i}. {region_name}: {score:.1f}%")
    
    print("\nReports saved:")
    print("  - data_pipeline/processed/validation_report.json")
    print("  - data_pipeline/processed/validation_summary.txt")
    
    if score >= 60:
        print("\n✅ Data quality acceptable - ready for analysis")
        print("\nNext steps:")
        print("1. python analysis/descriptive_analysis.py")
        print("2. python ml_models/train_models.py")
        print("3. python dashboard/deploy.py")
    else:
        print("\n⚠️  Data quality needs improvement")
        print("\nRecommended actions:")
        print("1. Review validation report for issues")
        print("2. Address critical failures")
        print("3. Re-run processing pipeline")


if __name__ == "__main__":
    main()