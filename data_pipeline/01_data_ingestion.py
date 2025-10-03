"""
Dynamic UK Bus Analytics Data Ingestion Pipeline
No hardcoding - fully configurable and scalable to all UK regions
Addresses all 57 analytical questions
"""
import os
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import DATA_RAW, API_ENDPOINTS, LOGS_DIR
from utils.api_client import BODSClient, ONSClient, NomisClient

logger.add(LOGS_DIR / "ingestion_{time}.log", rotation="1 day", retention="30 days")


class DynamicDataIngestionPipeline:
    """
    Fully dynamic data ingestion pipeline
    Configurable via YAML files - no hardcoded values
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize with optional configuration file
        Falls back to auto-discovery if no config provided
        """
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'ingestion_config.yaml'
        self.config = self._load_configuration()
        
        # Initialize API clients
        self.bods_client = self._init_bods_client()
        self.ons_client = ONSClient()
        self.nomis_client = NomisClient()
        
        # Statistics tracking
        self.stats = {
            'start_time': datetime.now(),
            'regions_processed': [],
            'datasets_downloaded': {},
            'demographic_datasets': [],
            'errors': [],
            'warnings': []
        }
    
    def _load_configuration(self) -> Dict:
        """
        Load configuration from YAML file
        Auto-generates default config if missing
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            logger.info("Generating default configuration...")
            return self._generate_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.success(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._generate_default_config()
    
    def _generate_default_config(self) -> Dict:
        """
        Generate comprehensive default configuration
        Covers all UK regions and data requirements
        """
        default_config = {
            'regions': {
                'north_east': {
                    'enabled': True,
                    'name': 'North East England',
                    'major_cities': ['Newcastle', 'Sunderland', 'Middlesbrough', 'Durham'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 10,
                    'priority': 'medium'
                },
                'north_west': {
                    'enabled': True,
                    'name': 'North West England',
                    'major_cities': ['Manchester', 'Liverpool', 'Preston', 'Blackpool'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 15,
                    'priority': 'high'
                },
                'yorkshire': {
                    'enabled': True,
                    'name': 'Yorkshire and Humber',
                    'major_cities': ['Leeds', 'Sheffield', 'Bradford', 'Hull'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 12,
                    'priority': 'high'
                },
                'east_midlands': {
                    'enabled': True,
                    'name': 'East Midlands',
                    'major_cities': ['Nottingham', 'Derby', 'Leicester', 'Lincoln'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 10,
                    'priority': 'high'
                },
                'west_midlands': {
                    'enabled': True,
                    'name': 'West Midlands',
                    'major_cities': ['Birmingham', 'Coventry', 'Wolverhampton'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 15,
                    'priority': 'high'
                },
                'east_england': {
                    'enabled': True,
                    'name': 'East of England',
                    'major_cities': ['Norwich', 'Cambridge', 'Ipswich', 'Peterborough'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 10,
                    'priority': 'medium'
                },
                'london': {
                    'enabled': True,
                    'name': 'Greater London',
                    'major_cities': ['London'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 20,
                    'priority': 'critical',
                    'special_handling': 'tfl_unified'
                },
                'south_east': {
                    'enabled': True,
                    'name': 'South East England',
                    'major_cities': ['Brighton', 'Reading', 'Oxford', 'Southampton'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 12,
                    'priority': 'high'
                },
                'south_west': {
                    'enabled': True,
                    'name': 'South West England',
                    'major_cities': ['Bristol', 'Plymouth', 'Bournemouth', 'Exeter'],
                    'lsoa_prefix': 'E01',
                    'max_datasets': 10,
                    'priority': 'medium'
                }
            },
            'demographic_sources': {
                'imd_2019': {
                    'enabled': True,
                    'name': 'Index of Multiple Deprivation 2019',
                    'source': 'arcgis',
                    'url': 'https://www.arcgis.com/sharing/rest/content/items/80592949bebd4390b2cbe29159a75ef4/data',
                    'questions_addressed': ['D24', 'D30', 'F37', 'G43', 'G50'],
                    'priority': 'critical'
                },
                'population_2021': {
                    'enabled': True,
                    'name': 'Census 2021 Population',
                    'source': 'nomis',
                    'dataset_id': 'NM_2010_1',
                    'geography': 'TYPE297',
                    'time': '2021',
                    'questions_addressed': ['A1', 'A2', 'A3', 'D24', 'E32'],
                    'priority': 'critical'
                },
                'income_2022': {
                    'enabled': True,
                    'name': 'Median Income by LSOA',
                    'source': 'nomis',
                    'dataset_id': 'NM_30_1',
                    'geography': 'TYPE297',
                    'time': 'latest',
                    'questions_addressed': ['D24', 'D28', 'I55', 'I56'],
                    'priority': 'high'
                },
                'unemployment_2024': {
                    'enabled': True,
                    'name': 'Unemployment Rate',
                    'source': 'nomis',
                    'dataset_id': 'NM_162_1',
                    'geography': 'TYPE297',
                    'time': 'latest',
                    'questions_addressed': ['D25', 'B14', 'H52'],
                    'priority': 'high'
                },
                'car_ownership': {
                    'enabled': True,
                    'name': 'Car/Van Ownership',
                    'source': 'nomis',
                    'dataset_id': 'NM_2027_1',
                    'geography': 'TYPE297',
                    'time': '2021',
                    'questions_addressed': ['D28'],
                    'priority': 'medium'
                },
                'age_structure': {
                    'enabled': True,
                    'name': 'Age Structure by LSOA',
                    'source': 'nomis',
                    'dataset_id': 'NM_2010_1',
                    'geography': 'TYPE297',
                    'measures': '20100',
                    'time': '2021',
                    'questions_addressed': ['D27'],
                    'priority': 'medium'
                },
                'schools_2024': {
                    'enabled': True,
                    'name': 'UK Schools Database',
                    'source': 'manual',
                    'url': 'https://get-information-schools.service.gov.uk/Downloads',
                    'instructions': 'Download "Establishment fields" CSV',
                    'questions_addressed': ['C22', 'D29', 'F39', 'H51'],
                    'priority': 'high'
                },
                'business_counts': {
                    'enabled': True,
                    'name': 'Business Enterprises by LSOA',
                    'source': 'nomis',
                    'dataset_id': 'NM_142_1',
                    'geography': 'TYPE297',
                    'time': 'latest',
                    'questions_addressed': ['I55'],
                    'priority': 'medium'
                }
            },
            'ingestion_settings': {
                'parallel_downloads': 3,
                'retry_attempts': 3,
                'timeout_seconds': 300,
                'cache_duration_days': 7,
                'validate_downloads': True,
                'min_file_size_bytes': 1000
            }
        }
        
        # Save default config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        
        logger.success(f"Generated default config: {self.config_path}")
        return default_config
    
    def _init_bods_client(self) -> Optional[BODSClient]:
        """Initialize BODS client with validation"""
        api_key = API_ENDPOINTS['bods']['api_key']
        
        if not api_key or api_key == 'your_actual_bods_api_key_here':
            logger.error("BODS API key not configured")
            self.stats['errors'].append("Missing BODS API key")
            return None
        
        try:
            client = BODSClient(
                API_ENDPOINTS['bods']['base_url'],
                api_key=api_key
            )
            logger.success("BODS client initialized")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize BODS client: {e}")
            self.stats['errors'].append(f"BODS client init failed: {e}")
            return None
    
    def discover_operators_for_region(self, region_code: str) -> List[Dict]:
        """
        Dynamically discover operators serving a region
        Uses BODS API metadata and city names
        """
        region_config = self.config['regions'].get(region_code)
        if not region_config or not region_config.get('enabled'):
            logger.warning(f"Region {region_code} is disabled or not configured")
            return []
        
        if not self.bods_client:
            logger.error("BODS client not available")
            return []
        
        logger.info(f"Discovering operators for {region_config['name']}")
        
        try:
            # Get all datasets
            all_datasets = self.bods_client.get_datasets(limit=1000)
            
            # Filter by region using city names and operator metadata
            regional_datasets = []
            major_cities = [city.lower() for city in region_config['major_cities']]
            
            for dataset in all_datasets.get('results', []):
                operator_name = dataset.get('operatorName', '').lower()
                description = dataset.get('description', '').lower()
                
                # Check if any major city is mentioned
                if any(city in operator_name or city in description for city in major_cities):
                    regional_datasets.append(dataset)
                    continue
                
                # Check for regional operators
                if region_config['name'].lower().replace(' england', '') in operator_name:
                    regional_datasets.append(dataset)
            
            logger.success(f"Found {len(regional_datasets)} operators for {region_config['name']}")
            return regional_datasets[:region_config.get('max_datasets', 10)]
            
        except Exception as e:
            logger.error(f"Failed to discover operators for {region_code}: {e}")
            self.stats['errors'].append(f"Region {region_code} discovery failed: {e}")
            return []
    
    def ingest_transport_data_for_region(self, region_code: str) -> Dict:
        """
        Ingest transport data for a specific region
        Fully dynamic based on configuration
        """
        region_config = self.config['regions'].get(region_code)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"INGESTING: {region_config['name']}")
        logger.info(f"{'='*60}")
        
        # Create region directory
        region_dir = DATA_RAW / 'regions' / region_code
        region_dir.mkdir(parents=True, exist_ok=True)
        
        # Discover operators
        datasets = self.discover_operators_for_region(region_code)
        
        if not datasets:
            logger.warning(f"No datasets found for {region_code}")
            return {
                'success': False,
                'region': region_code,
                'datasets_downloaded': 0,
                'reason': 'No datasets found'
            }
        
        # Download datasets
        downloaded = 0
        failed = 0
        
        for i, dataset in enumerate(datasets):
            try:
                dataset_id = dataset.get('id', f'unknown_{i}')
                operator_name = dataset.get('operatorName', 'Unknown').replace(' ', '_').replace('/', '_')
                dataset_url = dataset.get('url')
                
                if not dataset_url:
                    logger.warning(f"No download URL for dataset {dataset_id}")
                    failed += 1
                    continue
                
                output_path = region_dir / f"{operator_name}_{dataset_id}.zip"
                
                # Skip if already downloaded and valid
                if output_path.exists() and output_path.stat().st_size > self.config['ingestion_settings']['min_file_size_bytes']:
                    logger.info(f"Skipping (cached): {operator_name}")
                    downloaded += 1
                    continue
                
                # Download
                logger.info(f"Downloading: {operator_name}")
                if self.bods_client.download_dataset_file(dataset_url, str(output_path)):
                    downloaded += 1
                    logger.success(f"✓ {operator_name}")
                else:
                    failed += 1
                    logger.error(f"✗ {operator_name}")
                
            except Exception as e:
                logger.error(f"Failed to download dataset {i}: {e}")
                failed += 1
                continue
        
        result = {
            'success': downloaded > 0,
            'region': region_code,
            'region_name': region_config['name'],
            'datasets_discovered': len(datasets),
            'datasets_downloaded': downloaded,
            'datasets_failed': failed,
            'output_directory': str(region_dir)
        }
        
        self.stats['datasets_downloaded'][region_code] = result
        self.stats['regions_processed'].append(region_code)
        
        logger.success(f"✓ {region_config['name']}: {downloaded}/{len(datasets)} datasets")
        return result
    
    def ingest_all_transport_data(self) -> Dict:
        """
        Ingest transport data for all enabled regions
        Fully dynamic based on configuration
        """
        logger.info("\n" + "="*60)
        logger.info("NATIONAL TRANSPORT DATA INGESTION")
        logger.info("="*60 + "\n")
        
        enabled_regions = {
            code: config for code, config in self.config['regions'].items()
            if config.get('enabled', False)
        }
        
        logger.info(f"Processing {len(enabled_regions)} enabled regions")
        
        # Process by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_regions = sorted(
            enabled_regions.items(),
            key=lambda x: priority_order.get(x[1].get('priority', 'medium'), 2)
        )
        
        results = {}
        for region_code, region_config in sorted_regions:
            logger.info(f"\nPriority: {region_config.get('priority', 'medium').upper()}")
            result = self.ingest_transport_data_for_region(region_code)
            results[region_code] = result
        
        return results
    
    def download_demographic_dataset(self, dataset_key: str, config: Dict) -> bool:
        """
        Download a single demographic dataset
        Handles multiple source types dynamically
        """
        if not config.get('enabled', True):
            logger.info(f"Skipping disabled dataset: {dataset_key}")
            return False
        
        logger.info(f"Processing: {config['name']}")
        
        source_type = config.get('source', 'unknown')
        demo_dir = DATA_RAW / 'demographics'
        demo_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = demo_dir / f"{dataset_key}.csv"
        
        # Check cache
        if output_path.exists():
            file_age_days = (datetime.now().timestamp() - output_path.stat().st_mtime) / 86400
            cache_duration = self.config['ingestion_settings'].get('cache_duration_days', 7)
            
            if file_age_days < cache_duration:
                logger.info(f"Using cached data (age: {file_age_days:.1f} days)")
                self.stats['demographic_datasets'].append(dataset_key)
                return True
        
        try:
            if source_type == 'nomis':
                # NOMIS API download
                dataset_id = config.get('dataset_id')
                geography = config.get('geography', 'TYPE297')
                time_period = config.get('time', 'latest')
                measures = config.get('measures', None)
                
                url = f"https://www.nomisweb.co.uk/api/v01/dataset/{dataset_id}.bulk.csv"
                params = {
                    'geography': geography,
                    'time': time_period
                }
                if measures:
                    params['measures'] = measures
                
                response = requests.get(url, params=params, timeout=300)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    logger.success(f"✓ {config['name']}: {len(response.content)} bytes")
                    self.stats['demographic_datasets'].append(dataset_key)
                    return True
                else:
                    logger.error(f"✗ {config['name']}: HTTP {response.status_code}")
                    return False
                    
            elif source_type == 'arcgis':
                # ArcGIS direct download
                url = config.get('url')
                response = requests.get(url, timeout=300, stream=True)
                
                if response.status_code == 200:
                    # Handle ZIP files
                    if 'zip' in response.headers.get('content-type', '').lower():
                        import zipfile
                        import io
                        
                        zip_path = demo_dir / f"{dataset_key}.zip"
                        with open(zip_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        # Extract CSV
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                            if csv_files:
                                zip_ref.extract(csv_files[0], demo_dir)
                                extracted_path = demo_dir / csv_files[0]
                                extracted_path.rename(output_path)
                        
                        zip_path.unlink()
                    else:
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    
                    logger.success(f"✓ {config['name']}")
                    self.stats['demographic_datasets'].append(dataset_key)
                    return True
                else:
                    logger.error(f"✗ {config['name']}: HTTP {response.status_code}")
                    return False
                    
            elif source_type == 'manual':
                logger.warning(f"⚠ {config['name']} requires manual download")
                logger.info(f"  URL: {config.get('url')}")
                logger.info(f"  Instructions: {config.get('instructions', 'Download CSV')}")
                self.stats['warnings'].append(f"Manual download needed: {dataset_key}")
                return False
            
            else:
                logger.error(f"Unknown source type: {source_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download {dataset_key}: {e}")
            self.stats['errors'].append(f"Demographic {dataset_key} failed: {e}")
            return False
    
    def ingest_all_demographic_data(self) -> Dict:
        """
        Ingest all demographic datasets
        Fully dynamic based on configuration
        """
        logger.info("\n" + "="*60)
        logger.info("DEMOGRAPHIC DATA INGESTION")
        logger.info("="*60 + "\n")
        
        enabled_datasets = {
            key: config for key, config in self.config['demographic_sources'].items()
            if config.get('enabled', True)
        }
        
        logger.info(f"Processing {len(enabled_datasets)} demographic datasets")
        
        # Process by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_datasets = sorted(
            enabled_datasets.items(),
            key=lambda x: priority_order.get(x[1].get('priority', 'medium'), 2)
        )
        
        successful = 0
        failed = 0
        manual = 0
        
        for dataset_key, dataset_config in sorted_datasets:
            logger.info(f"\nPriority: {dataset_config.get('priority', 'medium').upper()}")
            
            if dataset_config.get('source') == 'manual':
                self.download_demographic_dataset(dataset_key, dataset_config)
                manual += 1
            elif self.download_demographic_dataset(dataset_key, dataset_config):
                successful += 1
            else:
                failed += 1
        
        return {
            'total_datasets': len(enabled_datasets),
            'successful': successful,
            'failed': failed,
            'manual_required': manual,
            'downloaded_datasets': self.stats['demographic_datasets']
        }
    
    def generate_ingestion_report(self) -> Dict:
        """
        Generate comprehensive ingestion report
        """
        duration = datetime.now() - self.stats['start_time']
        
        report = {
            'ingestion_summary': {
                'start_time': self.stats['start_time'].isoformat(),
                'duration': str(duration),
                'total_regions_processed': len(self.stats['regions_processed']),
                'total_demographic_datasets': len(self.stats['demographic_datasets'])
            },
            'regional_breakdown': self.stats['datasets_downloaded'],
            'demographic_datasets': self.stats['demographic_datasets'],
            'errors': self.stats['errors'],
            'warnings': self.stats['warnings']
        }
        
        # Save report
        report_path = DATA_RAW / 'ingestion_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.success(f"Ingestion report saved: {report_path}")
        return report
    
    def run_full_ingestion(self) -> Dict:
        """
        Execute complete ingestion pipeline
        Fully dynamic and configurable
        """
        logger.info("\n" + "="*60)
        logger.info("DYNAMIC DATA INGESTION PIPELINE")
        logger.info("="*60)
        
        logger.info(f"\nConfiguration: {self.config_path}")
        logger.info(f"Enabled regions: {sum(1 for r in self.config['regions'].values() if r.get('enabled'))}")
        logger.info(f"Enabled demographics: {sum(1 for d in self.config['demographic_sources'].values() if d.get('enabled'))}")
        
        # Step 1: Transport data
        logger.info("\n" + "="*60)
        logger.info("STEP 1: TRANSPORT DATA")
        logger.info("="*60)
        transport_results = self.ingest_all_transport_data()
        
        # Step 2: Demographic data
        logger.info("\n" + "="*60)
        logger.info("STEP 2: DEMOGRAPHIC DATA")
        logger.info("="*60)
        demographic_results = self.ingest_all_demographic_data()
        
        # Step 3: Generate report
        logger.info("\n" + "="*60)
        logger.info("STEP 3: INGESTION REPORT")
        logger.info("="*60)
        report = self.generate_ingestion_report()
        
        return {
            'transport_results': transport_results,
            'demographic_results': demographic_results,
            'report': report,
            'success': len(self.stats['errors']) == 0
        }


def main():
    """
    Execute dynamic data ingestion pipeline
    """
    print("\n" + "="*60)
    print("UK BUS ANALYTICS - DYNAMIC DATA INGESTION")
    print("="*60)
    print("\nFully configurable, no hardcoding")
    print("Scalable to all UK regions\n")
    
    # Initialize pipeline
    pipeline = DynamicDataIngestionPipeline()
    
    # Run full ingestion
    results = pipeline.run_full_ingestion()
    
    # Print summary
    print("\n" + "="*60)
    print("INGESTION COMPLETE")
    print("="*60)
    
    transport = results['transport_results']
    demographics = results['demographic_results']
    
    print(f"\nTransport Data:")
    print(f"  Regions processed: {len(transport)}")
    print(f"  Total datasets: {sum(r.get('datasets_downloaded', 0) for r in transport.values())}")
    
    print(f"\nDemographic Data:")
    print(f"  Successful: {demographics['successful']}")
    print(f"  Failed: {demographics['failed']}")
    print(f"  Manual required: {demographics['manual_required']}")
    
    if results['report']['errors']:
        print(f"\n⚠️  Errors encountered: {len(results['report']['errors'])}")
        for error in results['report']['errors'][:5]:
            print(f"  - {error}")
    
    if results['success']:
        print("\n✅ Ingestion completed successfully")
    else:
        print("\n⚠️  Ingestion completed with errors")
    
    print(f"\nNext steps:")
    print("1. python data_pipeline/02_data_processing.py")
    print("2. python data_pipeline/03_data_validation.py")


if __name__ == "__main__":
    main()