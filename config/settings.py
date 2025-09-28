"""
Enhanced configuration settings for UK Bus Analytics project
Updated based on real UK transport data requirements and project experience
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data_pipeline" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data_pipeline" / "processed"
DATA_STAGING = PROJECT_ROOT / "data_pipeline" / "staging"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure critical directories exist
for directory in [DATA_RAW, DATA_PROCESSED, DATA_STAGING, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database settings - enhanced with connection pooling options
DATABASE_CONFIG = {
    'local': {
        'engine': 'sqlite',
        'path': str(PROJECT_ROOT / 'data' / 'uk_transport.db'),
        'echo': False,  # Set to True for SQL debugging
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

# API Configuration - enhanced with realistic timeouts and limits
API_ENDPOINTS = {
    'bods': {
        'base_url': 'https://data.bus-data.dft.gov.uk/api/v1',
        'api_key': os.getenv('BODS_API_KEY'),
        'timeout': 60,  # Increased for large downloads
        'retry_attempts': 3,
        'backoff_factor': 2,
        'rate_limit_per_hour': 1000,  # BODS rate limits
        'max_concurrent_downloads': 3
    },
    'ons': {
        'base_url': 'https://api.beta.ons.gov.uk/v1',
        'timeout': 90,  # ONS can be very slow
        'retry_attempts': 5,
        'rate_limit_per_hour': 100
    },
    'nomis': {
        'base_url': 'https://www.nomisweb.co.uk/api/v01',
        'timeout': 120,  # NOMIS bulk downloads can be slow
        'retry_attempts': 3,
        'rate_limit_per_hour': 50
    },
    'arcgis_hub': {
        'base_url': 'https://hub.arcgis.com/api',
        'timeout': 180,  # Large geographic downloads
        'retry_attempts': 3
    }
}

# Enhanced operator configuration based on real BODS data
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
        'transxchange_quality': 'high',  # Arriva provides good TransXchange
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

# Updated ONS datasets based on working endpoints
ONS_DATASETS = {
    'imd2019': {
        'name': 'Indices of Multiple Deprivation 2019',
        'source': 'direct_download',
        'geography_level': 'lsoa2011',
        'key_fields': ['LSOA_CODE_2011', 'IMD_SCORE', 'IMD_RANK'],
        'expected_records': 32844,  # England LSOAs
        'update_frequency': 'irregular'
    },
    'population_2021': {
        'name': 'Census 2021 Population Data',
        'source': 'nomis_api',
        'nomis_dataset': 'NM_2094_1',
        'geography_level': 'lsoa2021',
        'key_fields': ['GEOGRAPHY_CODE', 'OBS_VALUE'],
        'expected_records': 35672,  # 2021 LSOAs
        'update_frequency': 'decennial'
    },
    'lsoa_boundaries': {
        'name': 'LSOA Boundaries and Names',
        'source': 'arcgis_rest',
        'geography_level': 'lsoa2011',
        'key_fields': ['LSOA11CD', 'LSOA11NM', 'LAD11CD', 'LAD11NM'],
        'expected_records': 32844,
        'update_frequency': 'irregular'
    }
}

# Enhanced data quality thresholds based on real UK data experience
DATA_QUALITY_THRESHOLDS = {
    'gtfs': {
        'max_missing_coordinates': 0.05,  # 5% max missing stop coordinates
        'max_future_dates': 90,  # GTFS shouldn't go more than 3 months ahead
        'min_stops_per_route': 2,
        'max_route_distance_km': 200,  # Catch obvious errors
        'min_stops_total': 100,  # Minimum stops for a meaningful dataset
        'max_stops_total': 50000,  # Sanity check for very large operators
        'coordinate_bounds': {  # UK bounding box
            'min_lat': 49.9,
            'max_lat': 60.9,
            'min_lon': -8.2,
            'max_lon': 1.8
        }
    },
    'transxchange': {
        'max_missing_coordinates': 0.15,  # TransXchange often has fewer coordinates
        'min_stops_per_service': 2,
        'min_services_total': 5,  # Minimum services for meaningful data
        'max_services_total': 1000,  # Sanity check
        'required_elements': ['StopPoint', 'Service'],  # Essential XML elements
        'coordinate_bounds': {  # Same UK bounds
            'min_lat': 49.9,
            'max_lat': 60.9,
            'min_lon': -8.2,
            'max_lon': 1.8
        }
    },
    'demographics': {
        'max_missing_population': 0.02,  # 2% max missing population data
        'min_population_per_lsoa': 500,  # Flag very small LSOAs
        'max_population_per_lsoa': 20000,  # Flag potential errors (increased from 5000)
        'min_imd_score': 0.0,
        'max_imd_score': 100.0,
        'expected_lsoa_count': 32844  # England 2011 LSOAs
    },
    'geographic': {
        'min_lsoa_records': 1000,  # Minimum for meaningful analysis
        'required_fields': ['LSOA11CD', 'LSOA11NM'],
        'valid_lsoa_pattern': r'^E0[12]\d{6}$',  # England LSOA code pattern
        'coordinate_precision': 6  # Decimal places for coordinates
    }
}

# Enhanced processing settings for real-world data volumes
PROCESSING_CONFIG = {
    'chunk_size': 50000,  # Increased for large NOMIS datasets
    'parallel_workers': max(1, os.cpu_count() - 1),
    'memory_limit_gb': 16,  # Increased for processing large geographic data
    'temp_file_cleanup': True,
    'cache_enabled': True,
    'cache_expiry_days': 7,
    'max_file_size_mb': 500,  # Maximum individual file size
    'max_xml_files_per_zip': 50  # Limit TransXchange processing to avoid memory issues
}

# UK coordinate reference systems - essential for accurate analysis
CRS_SYSTEMS = {
    'wgs84': 'EPSG:4326',      # GPS coordinates (lat/lon)
    'bng': 'EPSG:27700',       # British National Grid - use for distance calculations
    'web_mercator': 'EPSG:3857',  # Web mapping
    'osgb36': 'EPSG:4277'      # Ordnance Survey historical reference
}

# Data validation patterns for UK-specific data
VALIDATION_PATTERNS = {
    'lsoa_code_2011': r'^E0[12]\d{6}$',  # England LSOA 2011 codes
    'lsoa_code_2021': r'^E0[12]\d{6}$',  # England LSOA 2021 codes (similar pattern)
    'postcode': r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$',  # UK postcode
    'atco_code': r'^\d{3}[A-Z]*\d{8}$',  # ATCO bus stop codes
    'noc_code': r'^[A-Z0-9]{2,8}$'       # National Operator Codes
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

# Analysis configuration for transport-demographic correlation
ANALYSIS_CONFIG = {
    'spatial': {
        'buffer_distance_meters': 400,  # 400m walking distance to bus stops
        'min_stops_per_area': 1,        # Minimum stops to consider area "served"
        'accessibility_threshold': 0.8   # 80% population within buffer for "good access"
    },
    'demographic': {
        'deprivation_deciles': 10,      # IMD decile calculation
        'population_density_bins': 5,   # For population density analysis
        'key_metrics': [
            'total_population',
            'imd_score',
            'imd_rank',
            'bus_stop_count',
            'bus_route_count'
        ]
    },
    'temporal': {
        'peak_hours': [(7, 9), (17, 19)],  # Morning and evening peaks
        'off_peak_hours': [(9, 17)],       # Daytime off-peak
        'evening_hours': [(19, 23)],       # Evening services
        'weekend_pattern': 'reduced'        # Typical weekend service pattern
    }
}

# Export key configurations for easy access
__all__ = [
    'PROJECT_ROOT', 'DATA_RAW', 'DATA_PROCESSED', 'DATA_STAGING', 'LOGS_DIR',
    'DATABASE_CONFIG', 'API_ENDPOINTS', 'RELIABLE_OPERATORS', 'ONS_DATASETS',
    'DATA_QUALITY_THRESHOLDS', 'PROCESSING_CONFIG', 'CRS_SYSTEMS',
    'VALIDATION_PATTERNS', 'LOGGING_CONFIG', 'ANALYSIS_CONFIG'
]