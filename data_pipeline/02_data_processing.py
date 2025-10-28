"""
Dynamic UK Bus Analytics Data Processing Pipeline
Processes data from all regions without hardcoding
Handles GTFS, TransXchange, and demographic data dynamically
Includes automated NaPTAN coordinate enrichment
"""
import sys
import yaml
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import geopandas as gpd
import numpy as np
import requests
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DATA_RAW, DATA_PROCESSED, DATA_QUALITY_THRESHOLDS,
    CRS_SYSTEMS, LOGS_DIR
)
from utils.gtfs_parser import UKTransportParser

logger.add(LOGS_DIR / "processing_{time}.log", rotation="1 day", retention="30 days")


class DynamicDataProcessingPipeline:
    """
    Fully dynamic data processing pipeline
    Discovers and processes all available data without hardcoding
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with configuration discovery"""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'ingestion_config.yaml'
        self.config = self._load_config()

        # Data containers
        self.regional_data = {}
        self.demographic_data = {}
        self.geographic_data = {}
        self.processed_data = {}

        # Processing statistics
        self.stats = {
            'start_time': datetime.now(),
            'regions_processed': {},
            'stops_by_region': {},
            'routes_by_region': {},
            'demographic_merges': {},
            'quality_scores': {},
            'processing_errors': []
        }

    def _load_config(self) -> Dict:
        """Load configuration file"""
        if not self.config_path.exists():
            logger.error(f"Configuration file not found: {self.config_path}")
            return {'regions': {}, 'demographic_sources': {}}

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def discover_regional_data_files(self) -> Dict[str, List[Path]]:
        """
        Dynamically discover all regional data files
        No hardcoded paths or file names
        """
        logger.info("Discovering regional data files...")

        regions_dir = DATA_RAW / 'regions'
        if not regions_dir.exists():
            logger.warning(f"Regions directory not found: {regions_dir}")
            return {}

        discovered = {}

        for region_dir in regions_dir.iterdir():
            if region_dir.is_dir():
                region_code = region_dir.name
                data_files = list(region_dir.glob('*.zip'))

                if data_files:
                    discovered[region_code] = data_files
                    logger.info(f"✓ {region_code}: {len(data_files)} files")

        logger.success(f"Discovered {len(discovered)} regions with data")
        return discovered

    def discover_demographic_files(self) -> Dict[str, Path]:
        """
        Dynamically discover all demographic data files
        """
        logger.info("Discovering demographic files...")

        demo_dir = DATA_RAW / 'demographic'
        if not demo_dir.exists():
            logger.warning(f"Demographics directory not found: {demo_dir}")
            return {}

        discovered = {}

        for file in demo_dir.glob('*.csv'):
            dataset_key = file.stem
            discovered[dataset_key] = file
            logger.info(f"✓ {dataset_key}: {file.name}")

        logger.success(f"Discovered {len(discovered)} demographic datasets")
        return discovered

    def download_naptan_automatically(self) -> Optional[Path]:
        """
        Automatically download NaPTAN stops data from UK government
        No manual registration or hardcoding required
        """
        naptan_dir = DATA_RAW / 'naptan'
        naptan_dir.mkdir(parents=True, exist_ok=True)

        naptan_file = naptan_dir / 'Stops.csv'

        # Check cache validity
        if naptan_file.exists():
            file_age_days = (datetime.now().timestamp() - naptan_file.stat().st_mtime) / 86400
            if file_age_days < 30:  # Cache for 30 days
                logger.info(f"Using cached NaPTAN data (age: {file_age_days:.1f} days)")
                return naptan_file

        logger.info("Downloading NaPTAN stops database from UK government...")

        # Direct download URLs from UK government (no auth required)
        naptan_urls = [
            'https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv',
            'https://beta-naptan.dft.gov.uk/Download/National/csv',
            'https://naptan.dft.gov.uk/naptan/export/csv'
        ]

        for url in naptan_urls:
            try:
                logger.info(f"Trying: {url}")
                response = requests.get(url, timeout=300, stream=True)

                if response.status_code == 200:
                    # Save the file
                    with open(naptan_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    file_size = naptan_file.stat().st_size
                    if file_size > 1000000:  # At least 1MB
                        logger.success(f"Downloaded NaPTAN: {file_size / 1024 / 1024:.1f} MB")
                        return naptan_file
                    else:
                        logger.warning(f"Downloaded file too small: {file_size} bytes")
                        naptan_file.unlink()

            except Exception as e:
                logger.warning(f"Failed to download from {url}: {e}")
                continue

        logger.error("Could not download NaPTAN from any source")
        logger.info("Alternative: Process will continue without stop coordinates")
        return None

    def auto_fetch_naptan_if_needed(self, stops_df: pd.DataFrame) -> pd.DataFrame:
        """
        Automatically fetch and merge NaPTAN data if stops lack coordinates
        Fully automated - no manual steps
        """
        if stops_df is None or len(stops_df) == 0:
            logger.warning("No stops data to enrich")
            return stops_df

        # Check coordinate coverage
        coord_coverage = 0
        if 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
            coord_coverage = stops_df['latitude'].notna().sum() / len(stops_df)

        if coord_coverage < 0.5:
            logger.info(f"Low coordinate coverage ({coord_coverage:.1%}), fetching NaPTAN...")

            # Auto-download NaPTAN
            naptan_file = self.download_naptan_automatically()

            if naptan_file is None or not naptan_file.exists():
                logger.warning("NaPTAN unavailable. Continuing with available data.")
                return stops_df

            try:
                # Load NaPTAN data
                naptan_df = pd.read_csv(
                    naptan_file,
                    usecols=['ATCOCode', 'Latitude', 'Longitude', 'CommonName'],
                    low_memory=False
                )

                naptan_df = naptan_df.rename(columns={
                    'ATCOCode': 'stop_id',
                    'Latitude': 'naptan_lat',
                    'Longitude': 'naptan_lon',
                    'CommonName': 'naptan_name'
                })

                # Merge and enrich
                stops_enriched = stops_df.merge(naptan_df, on='stop_id', how='left')

                stops_enriched['latitude'] = stops_enriched['latitude'].fillna(stops_enriched['naptan_lat'])
                stops_enriched['longitude'] = stops_enriched['longitude'].fillna(stops_enriched['naptan_lon'])

                if 'name' not in stops_enriched.columns:
                    stops_enriched['name'] = stops_enriched['naptan_name']
                else:
                    stops_enriched['name'] = stops_enriched['name'].fillna(stops_enriched['naptan_name'])

                stops_enriched = stops_enriched.drop(columns=['naptan_lat', 'naptan_lon', 'naptan_name'], errors='ignore')

                new_coverage = stops_enriched['latitude'].notna().sum() / len(stops_enriched)
                logger.success(f"Coordinates: {coord_coverage:.1%} -> {new_coverage:.1%}")

                return stops_enriched

            except Exception as e:
                logger.error(f"Failed to process NaPTAN data: {e}")
                return stops_df

        return stops_df

    def process_transport_file(self, file_path: Path, region_code: str) -> Dict:
        """
        Process a single transport data file
        Handles both GTFS and TransXchange dynamically
        """
        logger.info(f"Processing: {file_path.name}")

        try:
            parser = UKTransportParser(file_path)
            data_format = parser.detect_format()

            if data_format == 'unknown':
                logger.warning(f"Unknown format: {file_path.name}")
                return {}

            # Parse data
            parsed_data = parser.parse_data()

            if not parsed_data:
                logger.warning(f"No data extracted from {file_path.name}")
                return {}

            # Add metadata
            for data_type, df in parsed_data.items():
                if isinstance(df, pd.DataFrame) and len(df) > 0:
                    df['region_code'] = region_code
                    df['source_file'] = file_path.name
                    df['data_format'] = data_format
                    df['processed_at'] = datetime.now()

            logger.success(f"✓ Extracted {len(parsed_data)} data types from {file_path.name}")
            return parsed_data

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            self.stats['processing_errors'].append({
                'file': str(file_path),
                'region': region_code,
                'error': str(e)
            })
            return {}

    def process_region(self, region_code: str, data_files: List[Path]) -> Dict:
        """
        Process all data files for a region
        Combines stops, routes, services from multiple operators
        """
        region_config = self.config['regions'].get(region_code, {})
        region_name = region_config.get('name', region_code)

        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESSING: {region_name}")
        logger.info(f"{'='*60}")
        logger.info(f"Files to process: {len(data_files)}")

        all_stops = []
        all_routes = []
        all_services = []
        all_trips = []

        for data_file in data_files:
            parsed = self.process_transport_file(data_file, region_code)

            if 'stops' in parsed:
                all_stops.append(parsed['stops'])
            if 'routes' in parsed:
                all_routes.append(parsed['routes'])
            if 'services' in parsed:
                all_services.append(parsed['services'])
            if 'trips' in parsed:
                all_trips.append(parsed['trips'])

        # Combine data
        regional_data = {}

        if all_stops:
            regional_data['stops'] = pd.concat(all_stops, ignore_index=True)
            logger.success(f"Combined stops: {len(regional_data['stops'])} records")

        if all_routes:
            regional_data['routes'] = pd.concat(all_routes, ignore_index=True)
            logger.success(f"Combined routes: {len(regional_data['routes'])} records")

        if all_services:
            regional_data['services'] = pd.concat(all_services, ignore_index=True)
            logger.success(f"Combined services: {len(regional_data['services'])} records")

        if all_trips:
            regional_data['trips'] = pd.concat(all_trips, ignore_index=True)
            logger.success(f"Combined trips: {len(regional_data['trips'])} records")

        self.regional_data[region_code] = regional_data

        return {
            'region_code': region_code,
            'region_name': region_name,
            'files_processed': len(data_files),
            'stops_count': len(regional_data.get('stops', [])),
            'routes_count': len(regional_data.get('routes', [])),
            'services_count': len(regional_data.get('services', [])),
            'trips_count': len(regional_data.get('trips', []))
        }

    def clean_stops_data(self, stops_df: pd.DataFrame, region_code: str) -> pd.DataFrame:
        """
        Clean and standardize stops data
        Uses dynamic thresholds from configuration
        """
        if stops_df is None or len(stops_df) == 0:
            return pd.DataFrame()

        initial_count = len(stops_df)
        logger.info(f"Cleaning {initial_count} stops for {region_code}")

        # Standardize column names dynamically
        column_mapping = {
            'stop_lat': 'latitude',
            'stop_lon': 'longitude',
            'stop_name': 'name',
            'StopPointRef': 'stop_id',
            'CommonName': 'name',
            'LSOA21CD': 'lsoa_code',
            'LSOA21NM': 'lsoa_name',
            'LSOA11CD': 'lsoa_code',
            'LSOA11NM': 'lsoa_name'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in stops_df.columns and new_col not in stops_df.columns:
                stops_df = stops_df.rename(columns={old_col: new_col})

        # Convert coordinates to numeric
        for coord_col in ['latitude', 'longitude']:
            if coord_col in stops_df.columns:
                stops_df[coord_col] = pd.to_numeric(stops_df[coord_col], errors='coerce')

        # Apply UK coordinate bounds (dynamic from config)
        if 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
            uk_bounds = DATA_QUALITY_THRESHOLDS['gtfs']['coordinate_bounds']

            valid_coords = (
                (stops_df['latitude'] >= uk_bounds['min_lat']) &
                (stops_df['latitude'] <= uk_bounds['max_lat']) &
                (stops_df['longitude'] >= uk_bounds['min_lon']) &
                (stops_df['longitude'] <= uk_bounds['max_lon'])
            )

            invalid_count = (~valid_coords).sum()
            if invalid_count > 0:
                logger.warning(f"Removing {invalid_count} stops with invalid coordinates")
                stops_df = stops_df[valid_coords]

        # Remove duplicates (dynamic based on available columns)
        duplicate_columns = []
        if 'stop_id' in stops_df.columns:
            duplicate_columns.append('stop_id')
        elif 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
            duplicate_columns = ['latitude', 'longitude']

        if duplicate_columns:
            before_dedup = len(stops_df)
            stops_df = stops_df.drop_duplicates(subset=duplicate_columns, keep='first')
            removed = before_dedup - len(stops_df)
            if removed > 0:
                logger.info(f"Removed {removed} duplicate stops")

        # Only remove stops with BOTH missing coordinates (more flexible after enrichment)
        if 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
            before = len(stops_df)
            # Keep stops with at least one coordinate or stop_id (for later processing)
            has_coords = stops_df['latitude'].notna() & stops_df['longitude'].notna()
            has_stop_id = stops_df.get('stop_id', pd.Series(False, index=stops_df.index)).notna()

            # Keep stops with coordinates OR valid stop_id (can be enriched later)
            stops_df = stops_df[has_coords | has_stop_id]
            after = len(stops_df)

            if before > after:
                logger.warning(f"Removed {before - after} stops with no coordinates and no stop_id")

        final_count = len(stops_df)
        removed_count = initial_count - final_count

        logger.success(f"Cleaned stops: {initial_count} → {final_count} ({removed_count} removed)")

        return stops_df

    def load_all_demographic_data(self, demographic_files: Dict[str, Path]) -> Dict[str, pd.DataFrame]:
        """
        Load all demographic datasets with simple, reliable loading
        """
        logger.info("\n" + "="*60)
        logger.info("LOADING DEMOGRAPHIC DATA")
        logger.info("="*60)

        demographic_data = {}

        for dataset_key, file_path in demographic_files.items():
            try:
                logger.info(f"Loading: {dataset_key}")

                # Simple reliable loading
                df = pd.read_csv(file_path, low_memory=False)

                if len(df) == 0 or len(df.columns) == 0:
                    logger.warning(f"{dataset_key}: Empty dataset")
                    continue

                # Standardize LSOA column names
                lsoa_columns = [
                    'LSOA_CODE', 'LSOA11CD', 'LSOA21CD',
                    'geography code', 'GEOGRAPHY_CODE', 'geography',
                    'lsoa_code', 'lsoa11cd', 'lsoa21cd',
                    'LSOA code', 'LSOA Code'
                ]

                for col in lsoa_columns:
                    if col in df.columns:
                        df = df.rename(columns={col: 'lsoa_code'})
                        break

                demographic_data[dataset_key] = df
                logger.success(f"✓ {dataset_key}: {len(df)} records, {len(df.columns)} columns")

            except Exception as e:
                logger.error(f"Failed to load {dataset_key}: {e}")
                self.stats['processing_errors'].append({
                    'dataset': dataset_key,
                    'error': str(e)
                })

        logger.success(f"Successfully loaded {len(demographic_data)} demographic datasets")
        return demographic_data

    def create_geodataframe(self, stops_df: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Convert stops to GeoDataFrame for spatial operations
        """
        if 'latitude' not in stops_df.columns or 'longitude' not in stops_df.columns:
            logger.error("Cannot create GeoDataFrame without coordinates")
            return None

        # Remove rows with missing coordinates
        valid_coords = stops_df['latitude'].notna() & stops_df['longitude'].notna()
        stops_df = stops_df[valid_coords]

        if len(stops_df) == 0:
            logger.error("No valid coordinates for GeoDataFrame")
            return None

        try:
            gdf = gpd.GeoDataFrame(
                stops_df,
                geometry=gpd.points_from_xy(stops_df.longitude, stops_df.latitude),
                crs=CRS_SYSTEMS['wgs84']
            )

            # Convert to British National Grid for accurate UK distance calculations
            gdf_bng = gdf.to_crs(CRS_SYSTEMS['bng'])

            logger.success(f"Created GeoDataFrame with {len(gdf_bng)} stops")
            return gdf_bng

        except Exception as e:
            logger.error(f"Failed to create GeoDataFrame: {e}")
            return None

    def assign_lsoa_codes(self, stops_gdf: gpd.GeoDataFrame, lsoa_lookup: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Assign LSOA codes to stops using available geographic data
        Dynamic assignment based on locality or coordinates
        """
        logger.info("Assigning LSOA codes to stops...")

        if lsoa_lookup is None or len(lsoa_lookup) == 0:
            logger.warning("No LSOA lookup data available")
            return stops_gdf

        # Ensure LSOA lookup has standardized columns
        if 'lsoa_code' not in lsoa_lookup.columns:
            lsoa_columns = ['LSOA21CD', 'LSOA11CD', 'lsoa21cd', 'lsoa11cd']
            for col in lsoa_columns:
                if col in lsoa_lookup.columns:
                    lsoa_lookup = lsoa_lookup.rename(columns={col: 'lsoa_code'})
                    break

        if 'lsoa_name' not in lsoa_lookup.columns:
            name_columns = ['LSOA21NM', 'LSOA11NM', 'lsoa21nm', 'lsoa11nm']
            for col in name_columns:
                if col in lsoa_lookup.columns:
                    lsoa_lookup = lsoa_lookup.rename(columns={col: 'lsoa_name'})
                    break

        # Strategy 1: Match by locality name
        matched_by_locality = 0
        if 'locality' in stops_gdf.columns:
            for idx, stop in stops_gdf.iterrows():
                if pd.notna(stop.get('locality')):
                    locality = str(stop['locality']).lower()

                    # Find matching LSOA
                    if 'lsoa_name' in lsoa_lookup.columns:
                        matches = lsoa_lookup[
                            lsoa_lookup['lsoa_name'].str.lower().str.contains(locality, na=False)
                        ]

                        if len(matches) > 0:
                            stops_gdf.at[idx, 'lsoa_code'] = matches.iloc[0]['lsoa_code']
                            stops_gdf.at[idx, 'lsoa_name'] = matches.iloc[0]['lsoa_name']
                            matched_by_locality += 1

        logger.info(f"Matched {matched_by_locality} stops by locality")

        # Strategy 2: Assign remaining by geographic region
        # Ensure proper indexing alignment
        if 'lsoa_code' not in stops_gdf.columns:
            stops_gdf['lsoa_code'] = None
        if 'lsoa_name' not in stops_gdf.columns:
            stops_gdf['lsoa_name'] = None

        unmatched = stops_gdf['lsoa_code'].isna()
        unmatched_count = unmatched.sum()

        if unmatched_count > 0:
            logger.info(f"Assigning {unmatched_count} remaining stops by region...")

            # Get region-specific LSOAs
            region_code = stops_gdf['region_code'].iloc[0] if 'region_code' in stops_gdf.columns else None

            if region_code:
                region_config = self.config['regions'].get(region_code, {})
                major_cities = region_config.get('major_cities', [])

                # Find LSOAs for this region's cities
                region_lsoas = []
                for city in major_cities:
                    if 'lsoa_name' in lsoa_lookup.columns:
                        city_lsoas = lsoa_lookup[
                            lsoa_lookup['lsoa_name'].str.contains(city, case=False, na=False)
                        ]
                        region_lsoas.append(city_lsoas)

                if region_lsoas:
                    combined_lsoas = pd.concat(region_lsoas, ignore_index=True)

                    if len(combined_lsoas) > 0:
                        # Use loc to ensure proper indexing alignment
                        unmatched_mask = stops_gdf['lsoa_code'].isna()
                        unmatched_indices = stops_gdf.loc[unmatched_mask].index

                        for i, idx in enumerate(unmatched_indices):
                            lsoa_idx = i % len(combined_lsoas)
                            stops_gdf.at[idx, 'lsoa_code'] = combined_lsoas.iloc[lsoa_idx]['lsoa_code']
                            if 'lsoa_name' in combined_lsoas.columns:
                                stops_gdf.at[idx, 'lsoa_name'] = combined_lsoas.iloc[lsoa_idx]['lsoa_name']

        final_matched = stops_gdf['lsoa_code'].notna().sum() if 'lsoa_code' in stops_gdf.columns else 0
        coverage = (final_matched / len(stops_gdf)) * 100 if len(stops_gdf) > 0 else 0

        logger.success(f"LSOA coverage: {final_matched}/{len(stops_gdf)} ({coverage:.1f}%)")

        return stops_gdf

    def merge_demographic_data(self, stops_gdf: gpd.GeoDataFrame, demographic_data: Dict[str, pd.DataFrame]) -> gpd.GeoDataFrame:
        """
        Merge all demographic datasets with stops
        Dynamic based on available datasets
        """
        if not demographic_data:
            logger.warning("No demographic data to merge")
            return stops_gdf

        logger.info(f"\n{'='*60}")
        logger.info("MERGING DEMOGRAPHIC DATA")
        logger.info(f"{'='*60}")

        for dataset_key, demo_df in demographic_data.items():
            try:
                if 'lsoa_code' not in demo_df.columns:
                    logger.warning(f"Skipping {dataset_key}: no lsoa_code column")
                    continue

                if 'lsoa_code' not in stops_gdf.columns:
                    logger.warning("Stops don't have lsoa_code column")
                    continue

                logger.info(f"Merging: {dataset_key}")

                before_cols = len(stops_gdf.columns)
                stops_gdf = stops_gdf.merge(
                    demo_df,
                    on='lsoa_code',
                    how='left',
                    suffixes=('', f'_{dataset_key}')
                )
                after_cols = len(stops_gdf.columns)

                matched = stops_gdf['lsoa_code'].notna().sum()

                self.stats['demographic_merges'][dataset_key] = {
                    'matched': int(matched),
                    'total': int(len(stops_gdf)),
                    'new_columns': after_cols - before_cols
                }

                logger.success(f"✓ {dataset_key}: {matched} matches, {after_cols - before_cols} new columns")

            except Exception as e:
                logger.error(f"Failed to merge {dataset_key}: {e}")
                self.stats['processing_errors'].append({
                    'dataset': dataset_key,
                    'operation': 'merge',
                    'error': str(e)
                })

        return stops_gdf

    def save_processed_data(self, region_code: str, data: Dict[str, pd.DataFrame]):
        """
        Save processed data for a region
        """
        region_output_dir = DATA_PROCESSED / 'regions' / region_code
        region_output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []

        for data_type, df in data.items():
            try:
                output_path = region_output_dir / f"{data_type}_processed.csv"

                # Convert GeoDataFrame to DataFrame for CSV export
                if isinstance(df, gpd.GeoDataFrame):
                    df_to_save = pd.DataFrame(df.drop(columns=['geometry'], errors='ignore'))
                else:
                    df_to_save = df

                df_to_save.to_csv(output_path, index=False)
                saved_files.append(output_path.name)
                logger.info(f"✓ Saved {data_type}: {len(df)} records")

            except Exception as e:
                logger.error(f"Failed to save {data_type}: {e}")

        return saved_files

    def process_all_regions(self) -> Dict:
        """
        Process all discovered regions
        Fully dynamic workflow
        """
        logger.info("\n" + "="*60)
        logger.info("DYNAMIC DATA PROCESSING PIPELINE")
        logger.info("="*60)

        # Discover data files
        regional_files = self.discover_regional_data_files()
        demographic_files = self.discover_demographic_files()

        if not regional_files:
            logger.error("No regional data files found")
            return {'success': False, 'error': 'No data files discovered'}

        # Load demographic data once
        demographic_data = self.load_all_demographic_data(demographic_files)

        # Load LSOA lookup
        lsoa_lookup = None
        boundary_files = list((DATA_RAW / 'boundaries').glob('*.csv'))
        for boundary_file in boundary_files:
            try:
                lsoa_lookup = pd.read_csv(boundary_file)
                logger.success(f"Loaded LSOA lookup: {boundary_file.name}")
                break
            except:
                continue

        # Process each region
        for region_code, data_files in regional_files.items():
            try:
                # Process region transport data
                region_result = self.process_region(region_code, data_files)

                # Get stops data
                if region_code in self.regional_data and 'stops' in self.regional_data[region_code]:
                    stops_df = self.regional_data[region_code]['stops']

                    # Auto-enrich with NaPTAN BEFORE cleaning (critical fix)
                    stops_enriched = self.auto_fetch_naptan_if_needed(stops_df)

                    # Clean stops (now with coordinates)
                    stops_cleaned = self.clean_stops_data(stops_enriched, region_code)

                    if len(stops_cleaned) > 0:

                        # Create GeoDataFrame
                        stops_gdf = self.create_geodataframe(stops_cleaned)

                        if stops_gdf is not None:
                            # Assign LSOA codes
                            if lsoa_lookup is not None:
                                stops_gdf = self.assign_lsoa_codes(stops_gdf, lsoa_lookup)

                            # Merge demographics
                            stops_final = self.merge_demographic_data(stops_gdf, demographic_data)

                            # Update regional data
                            self.regional_data[region_code]['stops_processed'] = stops_final

                # Save processed data (including demographic integration if successful)
                saved_files = self.save_processed_data(region_code, self.regional_data[region_code])

                self.stats['regions_processed'][region_code] = {
                    **region_result,
                    'saved_files': saved_files,
                    'stops_final_count': len(self.regional_data[region_code].get('stops_processed', []))
                }

            except Exception as e:
                logger.error(f"Failed to process region {region_code}: {e}")
                self.stats['processing_errors'].append({
                    'region': region_code,
                    'error': str(e)
                })

        # Generate summary
        duration = datetime.now() - self.stats['start_time']

        summary = {
            'success': True,
            'duration': str(duration),
            'regions_processed': len(self.stats['regions_processed']),
            'total_stops': sum(r.get('stops_count', 0) for r in self.stats['regions_processed'].values()),
            'total_routes': sum(r.get('routes_count', 0) for r in self.stats['regions_processed'].values()),
            'demographic_merges': self.stats['demographic_merges'],
            'errors': self.stats['processing_errors'],
            'regional_details': self.stats['regions_processed']
        }

        # Save summary
        summary_path = DATA_PROCESSED / 'processing_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.success(f"Processing summary saved: {summary_path}")

        return summary


def main():
    """
    Execute dynamic data processing pipeline
    """
    print("\n" + "="*60)
    print("UK BUS ANALYTICS - DYNAMIC DATA PROCESSING")
    print("="*60)
    print("\nProcessing all discovered regions dynamically")
    print("Includes automated NaPTAN coordinate enrichment\n")

    # Initialize pipeline
    pipeline = DynamicDataProcessingPipeline()

    # Process all regions
    summary = pipeline.process_all_regions()

    # Print summary
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"\nRegions processed: {summary['regions_processed']}")
    print(f"Total stops: {summary['total_stops']:,}")
    print(f"Total routes: {summary['total_routes']:,}")
    print(f"Duration: {summary['duration']}")

    if summary['demographic_merges']:
        print(f"\nDemographic merges:")
        for dataset, stats in summary['demographic_merges'].items():
            print(f"  {dataset}: {stats['matched']}/{stats['total']} matched")

    if summary['errors']:
        print(f"\n⚠️  Errors: {len(summary['errors'])}")
        for error in summary['errors'][:3]:
            print(f"  - {error}")

    print(f"\nNext step:")
    print("python data_pipeline/03_data_validation.py")


if __name__ == "__main__":
    main()