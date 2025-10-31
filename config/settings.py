"""
Enhanced configuration settings for UK Bus Analytics project
Dynamic, configurable, no hardcoding - loads from YAML when available
Maintains backwards compatibility with existing code
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_STAGING = PROJECT_ROOT / "data" / "staging"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure critical directories exist
for directory in [DATA_RAW, DATA_PROCESSED, DATA_STAGING, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load dynamic configuration from YAML if available
CONFIG_FILE = PROJECT_ROOT / 'config' / 'ingestion_config.yaml'

def load_yaml_config():
    """Load configuration from YAML file if it exists"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to load YAML config: {e}")
            return None
    return None

# Try to load YAML config
YAML_CONFIG = load_yaml_config()

# Database settings
DATABASE_CONFIG = {
    'local': {
        'engine': 'sqlite',
        'path': str(PROJECT_ROOT / 'data' / 'uk_transport.db'),
        'echo': False,
        'pool_pre_ping': True,
        'pool_recycle': 3600
    },
    'postgres': {
        'engine': 'postgresql',
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'uk_transport'),
        'username': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }
}

# API Configuration
API_ENDPOINTS = {
    'bods': {
        'base_url': 'https://data.bus-data.dft.gov.uk/api/v1',
        'api_key': os.getenv('BODS_API_KEY'),
        'timeout': 60,
        'retry_attempts': 3,
        'backoff_factor': 2,
        'rate_limit_per_hour': 1000,
        'max_concurrent_downloads': 3
    },
    'ons': {
        'base_url': 'https://api.beta.ons.gov.uk/v1',
        'timeout': 90,
        'retry_attempts': 5,
        'rate_limit_per_hour': 100
    },
    'nomis': {
        'base_url': 'https://www.nomisweb.co.uk/api/v01',
        'timeout': 120,
        'retry_attempts': 3,
        'rate_limit_per_hour': 50
    },
    'arcgis_hub': {
        'base_url': 'https://hub.arcgis.com/api',
        'timeout': 180,
        'retry_attempts': 3
    }
}

# UK Regions Configuration - dynamically loaded from YAML or use defaults
if YAML_CONFIG and 'regions' in YAML_CONFIG:
    UK_REGIONS = YAML_CONFIG['regions']
else:
    # Minimal default - will be auto-generated on first run
    UK_REGIONS = {}

# Demographic Sources Configuration - dynamically loaded from YAML
if YAML_CONFIG and 'demographic_sources' in YAML_CONFIG:
    DEMOGRAPHIC_SOURCES = YAML_CONFIG['demographic_sources']
else:
    DEMOGRAPHIC_SOURCES = {}

# Data quality thresholds
DATA_QUALITY_THRESHOLDS = {
    'gtfs': {
        'max_missing_coordinates': 0.05,
        'max_future_dates': 90,
        'min_stops_per_route': 2,
        'max_route_distance_km': 200,
        'min_stops_total': 100,
        'max_stops_total': 50000,
        'coordinate_bounds': {
            'min_lat': 49.9,
            'max_lat': 60.9,
            'min_lon': -8.2,
            'max_lon': 1.8
        }
    },
    'transxchange': {
        'max_missing_coordinates': 0.15,
        'min_stops_per_service': 2,
        'min_services_total': 5,
        'max_services_total': 1000,
        'required_elements': ['StopPoint', 'Service'],
        'coordinate_bounds': {
            'min_lat': 49.9,
            'max_lat': 60.9,
            'min_lon': -8.2,
            'max_lon': 1.8
        }
    },
    'demographics': {
        'max_missing_population': 0.02,
        'min_population_per_lsoa': 500,
        'max_population_per_lsoa': 20000,
        'min_imd_score': 0.0,
        'max_imd_score': 100.0,
        'expected_lsoa_count': 32844
    },
    'geographic': {
        'min_lsoa_records': 1000,
        'required_fields': ['LSOA11CD', 'LSOA11NM'],
        'valid_lsoa_pattern': r'^E0[12]\d{6}$',
        'coordinate_precision': 6
    }
}

# Processing configuration
PROCESSING_CONFIG = {
    'chunk_size': 50000,
    'parallel_workers': max(1, os.cpu_count() - 1),
    'memory_limit_gb': 16,
    'temp_file_cleanup': True,
    'cache_enabled': True,
    'cache_expiry_days': 7,
    'max_file_size_mb': 500,
    'max_xml_files_per_zip': 50
}

# UK coordinate reference systems
CRS_SYSTEMS = {
    'wgs84': 'EPSG:4326',
    'bng': 'EPSG:27700',
    'web_mercator': 'EPSG:3857',
    'osgb36': 'EPSG:4277'
}

# Validation patterns for UK-specific data
VALIDATION_PATTERNS = {
    'lsoa_code_2011': r'^E0[12]\d{6}$',
    'lsoa_code_2021': r'^E0[12]\d{6}$',
    'postcode': r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$',
    'atco_code': r'^\d{3}[A-Z]*\d{8}$',
    'noc_code': r'^[A-Z0-9]{2,8}$'
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}',
    'rotation': '100 MB',
    'retention': '30 days',
    'compression': 'gz',
    'backtrace': True,
    'diagnose': True
}

# Analysis configuration for answering the 57 questions
ANALYSIS_CONFIG = {
    'spatial': {
        'buffer_distance_meters': 400,
        'min_stops_per_area': 1,
        'accessibility_threshold': 0.8
    },
    'demographic': {
        'deprivation_deciles': 10,
        'population_density_bins': 5,
        'key_metrics': [
            'total_population',
            'imd_score',
            'imd_rank',
            'bus_stop_count',
            'bus_route_count',
            'median_income',
            'unemployment_rate',
            'car_ownership',
            'age_structure'
        ]
    },
    'temporal': {
        'peak_hours': [(7, 9), (17, 19)],
        'off_peak_hours': [(9, 17)],
        'evening_hours': [(19, 23)],
        'weekend_pattern': 'reduced'
    },
    'questions': {
        # Mapping of question categories to required data
        'coverage_accessibility': {
            'questions': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8'],
            'required_data': ['stops', 'routes', 'population', 'lsoa_boundaries']
        },
        'service_frequency': {
            'questions': ['B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16'],
            'required_data': ['trips', 'stop_times', 'calendar', 'routes']
        },
        'route_characteristics': {
            'questions': ['C17', 'C18', 'C19', 'C20', 'C21', 'C22', 'C23'],
            'required_data': ['routes', 'shapes', 'schools', 'stops']
        },
        'socioeconomic': {
            'questions': ['D24', 'D25', 'D26', 'D27', 'D28', 'D29', 'D30', 'D31'],
            'required_data': ['stops', 'routes', 'income', 'unemployment', 'imd', 'schools', 'car_ownership', 'age_structure']
        },
        'temporal_trends': {
            'questions': ['E32', 'E33', 'E34', 'E35', 'E36'],
            'required_data': ['historical_data', 'population_trends', 'service_changes']
        },
        'equity_policy': {
            'questions': ['F37', 'F38', 'F39', 'F40', 'F41', 'F42', 'F43'],
            'required_data': ['stops', 'routes', 'population', 'imd', 'schools', 'employment_centers']
        },
        'analytical_insights': {
            'questions': ['G44', 'G45', 'G46', 'G47', 'G48', 'G49', 'G50'],
            'required_data': ['all_transport_data', 'all_demographic_data', 'ml_clustering']
        },
        'accessibility_equity': {
            'questions': ['H51', 'H52', 'H53'],
            'required_data': ['stops', 'services', 'income', 'employment', 'shift_patterns']
        },
        'economic_impact': {
            'questions': ['I54', 'I55', 'I56'],
            'required_data': ['stops', 'business_counts', 'property_prices', 'income']
        }
    }
}

# ONS Datasets - kept for backwards compatibility but can be overridden by YAML
ONS_DATASETS = DEMOGRAPHIC_SOURCES if DEMOGRAPHIC_SOURCES else {
    'imd2019': {
        'name': 'Indices of Multiple Deprivation 2019',
        'source': 'direct_download',
        'geography_level': 'lsoa2011',
        'key_fields': ['LSOA_CODE_2011', 'IMD_SCORE', 'IMD_RANK'],
        'expected_records': 32844,
        'update_frequency': 'irregular'
    }
}

# Reliable operators - kept for backwards compatibility
RELIABLE_OPERATORS = {
    'first_group': {
        'name': 'First Group',
        'regions': ['south_west', 'scotland', 'north_east'],
        'gtfs_quality': 'high',
        'transxchange_quality': 'high',
        'api_reliability': 'medium',
        'bods_operator_id': 'FIRST',
        'expected_stops': 5000,
        'expected_routes': 200
    },
    'stagecoach': {
        'name': 'Stagecoach',
        'regions': ['national'],
        'gtfs_quality': 'high',
        'transxchange_quality': 'high',
        'api_reliability': 'high',
        'bods_operator_id': 'SCOX',
        'expected_stops': 8000,
        'expected_routes': 400
    },
    'arriva': {
        'name': 'Arriva',
        'regions': ['north', 'midlands'],
        'gtfs_quality': 'medium',
        'transxchange_quality': 'high',
        'api_reliability': 'medium',
        'bods_operator_id': 'ARRV',
        'expected_stops': 6000,
        'expected_routes': 300
    },
    'go_ahead': {
        'name': 'Go-Ahead Group',
        'regions': ['london', 'south_east'],
        'gtfs_quality': 'medium',
        'transxchange_quality': 'high',
        'api_reliability': 'high',
        'bods_operator_id': 'GOEA',
        'expected_stops': 4000,
        'expected_routes': 250
    }
}

# Export key configurations
__all__ = [
    'PROJECT_ROOT', 'DATA_RAW', 'DATA_PROCESSED', 'DATA_STAGING', 'LOGS_DIR',
    'DATABASE_CONFIG', 'API_ENDPOINTS', 'UK_REGIONS', 'DEMOGRAPHIC_SOURCES',
    'RELIABLE_OPERATORS', 'ONS_DATASETS', 'DATA_QUALITY_THRESHOLDS',
    'PROCESSING_CONFIG', 'CRS_SYSTEMS', 'VALIDATION_PATTERNS',
    'LOGGING_CONFIG', 'ANALYSIS_CONFIG', 'YAML_CONFIG'
]