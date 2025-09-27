"""
Configuration settings for UK Bus Analytics project
Based on lessons learned from multiple UK transport data projects
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

# Database settings
DATABASE_CONFIG = {
    'local': {
        'engine': 'sqlite',
        'path': str(PROJECT_ROOT / 'data' / 'uk_transport.db'),
        'echo': False  # Set to True for SQL debugging
    },
    'postgres': {
        'engine': 'postgresql',
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'uk_transport'),
        'username': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
    }
}

# API Configuration - these are the most reliable sources I've used
API_ENDPOINTS = {
    'bods': {
        'base_url': 'https://data.bus-data.dft.gov.uk/api/v1',
        'api_key': os.getenv('BODS_API_KEY'),  # Get this from DfT
        'timeout': 30,
        'retry_attempts': 3,
        'backoff_factor': 2
    },
    'ons': {
        'base_url': 'https://api.beta.ons.gov.uk/v1',
        'timeout': 45,  # ONS can be slow
        'retry_attempts': 5
    },
    'nomis': {
        'base_url': 'https://www.nomisweb.co.uk/api/v01',
        'timeout': 30
    }
}

# Data sources - from experience, these are the most reliable
RELIABLE_OPERATORS = {
    'first_group': {
        'name': 'First Group',
        'regions': ['south_west', 'scotland', 'north_east'],
        'gtfs_quality': 'high',  # Personal rating from experience
        'api_reliability': 'medium',
        'bods_operator_id': 'FIRST'
    },
    'stagecoach': {
        'name': 'Stagecoach',
        'regions': ['national'],
        'gtfs_quality': 'high',
        'api_reliability': 'high',
        'bods_operator_id': 'SCOX'
    },
    'arriva': {
        'name': 'Arriva',
        'regions': ['north', 'midlands'],
        'gtfs_quality': 'medium',  # Can have some data quality issues
        'api_reliability': 'medium',
        'bods_operator_id': 'ARRV'
    }
}

# ONS datasets - these are the core ones you'll need with proper API endpoints
ONS_DATASETS = {
    'imd2019': {
        'name': 'Indices of Multiple Deprivation 2019',
        'nomis_dataset': 'NM_2010_1',  # Use NOMIS API for IMD data
        'geography_level': 'lsoa2011',
        'key_fields': ['GEOGRAPHY_CODE', 'OBS_VALUE', 'MEASURES_NAME']
    },
    'population_2021': {
        'name': 'Census 2021 Population Data',
        'nomis_dataset': 'NM_2094_1',  # Census 2021 population
        'geography_level': 'lsoa2021',
        'key_fields': ['GEOGRAPHY_CODE', 'OBS_VALUE']
    },
    'boundaries_lsoa': {
        'name': 'LSOA Boundaries 2021',
        'ons_dataset': 'statistical-geographies',
        'api_endpoint': '/datasets/cpih01/geography',
        'key_fields': ['code', 'name']
    }
}

# Data quality thresholds - learned these the hard way
DATA_QUALITY_THRESHOLDS = {
    'gtfs': {
        'max_missing_coordinates': 0.05,  # 5% max missing stop coordinates
        'max_future_dates': 90,  # GTFS shouldn't go more than 3 months ahead
        'min_stops_per_route': 2,
        'max_route_distance_km': 200  # Catch obvious errors
    },
    'demographics': {
        'max_missing_population': 0.02,  # 2% max missing population data
        'min_population_per_lsoa': 500,  # Flag very small LSOAs
        'max_population_per_lsoa': 5000  # Flag potential errors
    }
}

# Processing settings
PROCESSING_CONFIG = {
    'chunk_size': 10000,  # For large dataset processing
    'parallel_workers': os.cpu_count() - 1,
    'memory_limit_gb': 8,  # Adjust based on your machine
    'temp_file_cleanup': True
}

# Coordinate systems - crucial for UK data
CRS_SYSTEMS = {
    'wgs84': 'EPSG:4326',  # GPS coordinates
    'bng': 'EPSG:27700',   # British National Grid - use this for distance calculations
    'web_mercator': 'EPSG:3857'  # For web mapping
}