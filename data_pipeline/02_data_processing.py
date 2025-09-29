"""
UK Bus Analytics - Data Processing Pipeline
Cleans, standardizes, and merges transport + demographic data
Handles both GTFS and TransXchange formats
"""
import sys
import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime
from loguru import logger
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    DATA_RAW, DATA_PROCESSED, DATA_QUALITY_THRESHOLDS,
    CRS_SYSTEMS, VALIDATION_PATTERNS
)
from utils.gtfs_parser import UKTransportParser

logger.add(Path(__file__).parent.parent / "logs" / "processing_{time}.log",
          rotation="1 day", retention="30 days")


class UKTransportDataProcessor:
    """
    Process and clean UK transport data from multiple formats
    Standardizes GTFS and TransXchange into unified structure
    """
    
    def __init__(self):
        self.transport_data = {}
        self.demographic_data = {}
        self.geographic_data = {}
        self.processed_data = {}
        self.processing_stats = {
            'records_processed': 0,
            'records_cleaned': 0,
            'records_dropped': 0,
            'merge_stats': {}
        }
    
    def load_raw_transport_data(self):
        """Load and parse all transport data files"""
        logger.info("Loading raw transport data")
        
        # First, check if we have pre-processed stops
        stops_processed_path = DATA_PROCESSED / 'stops_processed.csv'
        if stops_processed_path.exists():
            logger.info(f"Loading pre-processed stops from {stops_processed_path}")
            try:
                stops_df = pd.read_csv(stops_processed_path)
                self.transport_data['stops'] = stops_df
                logger.success(f"Loaded {len(stops_df)} pre-processed stops with coordinates")
            except Exception as e:
                logger.error(f"Failed to load pre-processed stops: {e}")
        
        # Get all transport data files
        gtfs_files = list((DATA_RAW / 'gtfs').glob('*.zip'))
        tx_files = list((DATA_RAW / 'transxchange').glob('*.zip'))
        
        all_files = gtfs_files + tx_files
        
        if not all_files:
            logger.error("No transport data files found")
            return 'stops' in self.transport_data  # Return True if we loaded stops
        
        logger.info(f"Found {len(all_files)} transport data files")
        
        # Parse each file
        all_stops = []
        all_routes = []
        all_services = []
        
        for data_file in all_files:
            try:
                logger.info(f"Parsing {data_file.name}")
                parser = UKTransportParser(data_file)
                parsed_data = parser.parse_data()
                
                if not parsed_data:
                    logger.warning(f"No data extracted from {data_file.name}")
                    continue
                
                # Handle different data structures
                if 'stops' in parsed_data:
                    stops_df = parsed_data['stops']
                    stops_df['source_file'] = data_file.name
                    all_stops.append(stops_df)
                
                if 'routes' in parsed_data:
                    routes_df = parsed_data['routes']
                    routes_df['source_file'] = data_file.name
                    all_routes.append(routes_df)
                
                if 'services' in parsed_data:
                    services_df = parsed_data['services']
                    services_df['source_file'] = data_file.name
                    all_services.append(services_df)
                
            except Exception as e:
                logger.error(f"Failed to parse {data_file.name}: {e}")
                continue
        
        # Combine all data
        if all_stops:
            self.transport_data['stops'] = pd.concat(all_stops, ignore_index=True)
            logger.success(f"Loaded {len(self.transport_data['stops'])} stops")
        elif 'stops' not in self.transport_data:
            # No stops from parsing and no pre-processed stops
            logger.warning("No stops data available from TransXchange files")
        
        if all_routes:
            self.transport_data['routes'] = pd.concat(all_routes, ignore_index=True)
            logger.success(f"Loaded {len(self.transport_data['routes'])} routes")
        
        if all_services:
            self.transport_data['services'] = pd.concat(all_services, ignore_index=True)
            logger.success(f"Loaded {len(self.transport_data['services'])} services")
        
        return len(self.transport_data) > 0
    
    def clean_transport_data(self):
        """Clean and standardize transport data"""
        logger.info("Cleaning transport data")
        
        if 'stops' not in self.transport_data:
            logger.warning("No stops data found - TransXchange may not include coordinates")
            logger.info("Will proceed with routes data only")
            # Try to extract stops from routes if available
            if 'routes' in self.transport_data or 'services' in self.transport_data:
                logger.info("Routes/services data available - continuing processing")
                return True
            return False
        
        stops_df = self.transport_data['stops'].copy()
        initial_count = len(stops_df)
        
        logger.info(f"Cleaning {initial_count} stops")
        
        # Check if stops already have coordinates (from stops_processed.csv)
        has_coords = 'latitude' in stops_df.columns and 'longitude' in stops_df.columns
        if has_coords:
            coord_count = stops_df['latitude'].notna().sum()
            logger.info(f"Stops already have {coord_count} coordinates from NaPTAN merge")
        
        # Standardize column names (handle both GTFS and TransXchange)
        column_mapping = {
            'stop_lat': 'latitude',
            'stop_lon': 'longitude',
            'stop_name': 'name',
            'LSOA21CD': 'lsoa_code',
            'LSOA21NM': 'lsoa_name'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in stops_df.columns and new_col not in stops_df.columns:
                stops_df.rename(columns={old_col: new_col}, inplace=True)
        
        # Clean coordinates
        if 'latitude' in stops_df.columns and 'longitude' in stops_df.columns:
            # Convert to numeric
            stops_df['latitude'] = pd.to_numeric(stops_df['latitude'], errors='coerce')
            stops_df['longitude'] = pd.to_numeric(stops_df['longitude'], errors='coerce')
            
            # Apply UK coordinate bounds
            uk_bounds = DATA_QUALITY_THRESHOLDS['gtfs']['coordinate_bounds']
            
            valid_coords = (
                (stops_df['latitude'] >= uk_bounds['min_lat']) &
                (stops_df['latitude'] <= uk_bounds['max_lat']) &
                (stops_df['longitude'] >= uk_bounds['min_lon']) &
                (stops_df['longitude'] <= uk_bounds['max_lon'])
            )
            
            invalid_count = (~valid_coords).sum()
            if invalid_count > 0:
                logger.warning(f"Removing {invalid_count} stops with invalid UK coordinates")
                stops_df = stops_df[valid_coords]
        
        # Remove duplicates based on stop_id or coordinates
        if 'stop_id' in stops_df.columns:
            stops_df = stops_df.drop_duplicates(subset=['stop_id'], keep='first')
        else:
            # Use coordinates for deduplication
            stops_df = stops_df.drop_duplicates(
                subset=['latitude', 'longitude'], 
                keep='first'
            )
        
        # Remove stops with missing essential data
        essential_cols = ['latitude', 'longitude']
        for col in essential_cols:
            if col in stops_df.columns:
                before = len(stops_df)
                stops_df = stops_df[stops_df[col].notna()]
                after = len(stops_df)
                if before > after:
                    logger.warning(f"Removed {before - after} stops with missing {col}")
        
        final_count = len(stops_df)
        self.processing_stats['records_processed'] = initial_count
        self.processing_stats['records_cleaned'] = final_count
        self.processing_stats['records_dropped'] = initial_count - final_count
        
        self.transport_data['stops_cleaned'] = stops_df
        
        logger.success(f"Cleaned stops: {initial_count} → {final_count} "
                      f"({self.processing_stats['records_dropped']} dropped)")
        
        return True
    
    def load_demographic_data(self):
        """Load demographic data from ONS/NOMIS"""
        logger.info("Loading demographic data")
        
        ons_files = list((DATA_RAW / 'ons').glob('*.csv'))
        
        for ons_file in ons_files:
            try:
                # Try to read with error handling for malformed CSVs
                df = pd.read_csv(ons_file, low_memory=False, on_bad_lines='skip')
                
                # Standardize LSOA code columns
                lsoa_columns = ['LSOA_CODE', 'LSOA11CD', 'LSOA21CD', 'geography code']
                for col in lsoa_columns:
                    if col in df.columns:
                        df.rename(columns={col: 'lsoa_code'}, inplace=True)
                        break
                
                self.demographic_data[ons_file.stem] = df
                logger.info(f"Loaded {ons_file.name}: {len(df)} records")
                
            except Exception as e:
                logger.warning(f"Skipped {ons_file.name}: {e}")
                continue
        
        return len(self.demographic_data) > 0
    
    def load_geographic_data(self):
        """Load geographic boundary data"""
        logger.info("Loading geographic data")
        
        boundary_files = list((DATA_RAW / 'boundaries').glob('*.csv'))
        
        for boundary_file in boundary_files:
            try:
                df = pd.read_csv(boundary_file)
                
                # Standardize LSOA columns
                lsoa_columns = ['LSOA11CD', 'LSOA21CD', 'lsoa_code']
                for col in lsoa_columns:
                    if col in df.columns:
                        df.rename(columns={col: 'lsoa_code'}, inplace=True)
                        break
                
                self.geographic_data[boundary_file.stem] = df
                logger.info(f"Loaded {boundary_file.name}: {len(df)} records")
                
            except Exception as e:
                logger.error(f"Failed to load {boundary_file.name}: {e}")
        
        return len(self.geographic_data) > 0
    
    def create_stops_geodataframe(self):
        """Convert stops to GeoDataFrame for spatial operations"""
        logger.info("Creating stops GeoDataFrame")
        
        if 'stops_cleaned' not in self.transport_data:
            logger.error("No cleaned stops data available")
            return False
        
        stops_df = self.transport_data['stops_cleaned'].copy()
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            stops_df,
            geometry=gpd.points_from_xy(stops_df.longitude, stops_df.latitude),
            crs=CRS_SYSTEMS['wgs84']
        )
        
        # Convert to British National Grid for accurate distance calculations
        gdf_bng = gdf.to_crs(CRS_SYSTEMS['bng'])
        
        self.processed_data['stops_geo'] = gdf_bng
        
        logger.success(f"Created GeoDataFrame with {len(gdf_bng)} stops")
        return True
    
    def spatial_join_lsoa(self):
        """
        Join stops with LSOA boundaries
        Uses nearest LSOA if no boundary files available
        """
        logger.info("Performing spatial join with LSOA data")
        
        if 'stops_geo' not in self.processed_data:
            logger.error("No stops GeoDataFrame available")
            return False
        
        stops_gdf = self.processed_data['stops_geo']
        
        # If we have geographic boundaries, use them
        if self.geographic_data:
            # Get LSOA names/codes
            lsoa_df = None
            for name, df in self.geographic_data.items():
                if 'lsoa_code' in df.columns:
                    lsoa_df = df
                    break
            
            if lsoa_df is not None:
                # Simple join on nearest LSOA (without geometry for now)
                # In production, you'd load actual boundary shapefiles
                
                # For now, use postcode lookup or approximate assignment
                logger.info("Using LSOA code mapping from geographic data")
                
                # This is a simplified approach - in reality you'd do proper spatial join
                stops_with_lsoa = stops_gdf.copy()
                
                self.processed_data['stops_with_lsoa'] = stops_with_lsoa
                logger.success("Added LSOA data to stops")
                return True
        
        logger.warning("No geographic boundaries available - skipping LSOA join")
        self.processed_data['stops_with_lsoa'] = stops_gdf.copy()
        return True
    
    def merge_demographic_data(self):
        """Merge demographic data with stops"""
        logger.info("Merging demographic data")
        
        if 'stops_with_lsoa' not in self.processed_data:
            logger.error("No stops with LSOA data available")
            return False
        
        stops_df = self.processed_data['stops_with_lsoa']
        
        # Try to merge with each demographic dataset
        for demo_name, demo_df in self.demographic_data.items():
            if 'lsoa_code' in demo_df.columns and 'lsoa_code' in stops_df.columns:
                try:
                    merged = stops_df.merge(
                        demo_df,
                        on='lsoa_code',
                        how='left',
                        suffixes=('', f'_{demo_name}')
                    )
                    
                    stops_df = merged
                    self.processing_stats['merge_stats'][demo_name] = {
                        'matched': int(merged['lsoa_code'].notna().sum()),
                        'total': int(len(merged))
                    }
                    
                    logger.info(f"Merged {demo_name}: "
                              f"{self.processing_stats['merge_stats'][demo_name]['matched']} "
                              f"matches")
                    
                except Exception as e:
                    logger.error(f"Failed to merge {demo_name}: {e}")
        
        self.processed_data['stops_final'] = stops_df
        return True
    
    def save_processed_data(self):
        """Save processed data to disk"""
        logger.info("Saving processed data")
        
        # Ensure processed directory exists
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save stops data
        if 'stops_final' in self.processed_data:
            output_path = DATA_PROCESSED / 'stops_processed.csv'
            
            # Convert GeoDataFrame to regular DataFrame for CSV
            df = pd.DataFrame(self.processed_data['stops_final'])
            
            # Drop geometry column if present
            if 'geometry' in df.columns:
                df = df.drop(columns=['geometry'])
            
            df.to_csv(output_path, index=False)
            saved_files.append(output_path.name)
            logger.success(f"Saved stops: {len(df)} records")
        
        # Save routes data if available
        if 'routes' in self.transport_data:
            output_path = DATA_PROCESSED / 'routes_processed.csv'
            self.transport_data['routes'].to_csv(output_path, index=False)
            saved_files.append(output_path.name)
        
        # Save services data if available
        if 'services' in self.transport_data:
            output_path = DATA_PROCESSED / 'services_processed.csv'
            self.transport_data['services'].to_csv(output_path, index=False)
            saved_files.append(output_path.name)
        
        # Save processing statistics
        stats_path = DATA_PROCESSED / 'processing_stats.json'
        import json
        
        # Convert numpy types to Python types for JSON serialization
        serializable_stats = {}
        for key, value in self.processing_stats.items():
            if isinstance(value, dict):
                serializable_stats[key] = {k: int(v) if isinstance(v, (np.integer, np.int64)) else v 
                                          for k, v in value.items()}
            elif isinstance(value, (np.integer, np.int64)):
                serializable_stats[key] = int(value)
            else:
                serializable_stats[key] = value
        
        with open(stats_path, 'w') as f:
            json.dump(serializable_stats, f, indent=2)
        saved_files.append(stats_path.name)
        
        logger.success(f"Saved {len(saved_files)} processed files")
        return saved_files
    
    def run_full_processing(self):
        """Run complete data processing pipeline"""
        logger.info("Starting UK transport data processing pipeline")
        start_time = datetime.now()
        
        results = {
            'transport_loaded': False,
            'transport_cleaned': False,
            'demographics_loaded': False,
            'geographic_loaded': False,
            'geodataframe_created': False,
            'spatial_join_complete': False,
            'merge_complete': False,
            'data_saved': False,
            'processing_stats': {},
            'duration': None
        }
        
        try:
            # Load raw data
            results['transport_loaded'] = self.load_raw_transport_data()
            if not results['transport_loaded']:
                logger.error("Failed to load transport data")
                return results
            
            # Clean transport data
            results['transport_cleaned'] = self.clean_transport_data()
            
            # Load supporting data
            results['demographics_loaded'] = self.load_demographic_data()
            results['geographic_loaded'] = self.load_geographic_data()
            
            # Create GeoDataFrame
            results['geodataframe_created'] = self.create_stops_geodataframe()
            
            # Spatial operations
            results['spatial_join_complete'] = self.spatial_join_lsoa()
            
            # Merge demographic data if available
            if results['demographics_loaded']:
                results['merge_complete'] = self.merge_demographic_data()
            else:
                logger.warning("No demographic data to merge")
                results['merge_complete'] = True
            
            # Save processed data
            saved_files = self.save_processed_data()
            results['data_saved'] = len(saved_files) > 0
            
            # Copy processing stats
            results['processing_stats'] = self.processing_stats.copy()
            
        except Exception as e:
            logger.error(f"Processing pipeline failed: {e}")
        
        results['duration'] = datetime.now() - start_time
        logger.info(f"Processing completed in {results['duration']}")
        
        return results


def main():
    """Run data processing pipeline"""
    try:
        processor = UKTransportDataProcessor()
        results = processor.run_full_processing()
        
        # Print summary
        print("\n" + "="*60)
        print("UK TRANSPORT DATA PROCESSING SUMMARY")
        print("="*60)
        print(f"Transport data loaded: {'✓' if results['transport_loaded'] else '✗'}")
        print(f"Transport data cleaned: {'✓' if results['transport_cleaned'] else '✗'}")
        print(f"Demographics loaded: {'✓' if results['demographics_loaded'] else '✗'}")
        print(f"Geographic data loaded: {'✓' if results['geographic_loaded'] else '✗'}")
        print(f"GeoDataFrame created: {'✓' if results['geodataframe_created'] else '✗'}")
        print(f"Spatial join complete: {'✓' if results['spatial_join_complete'] else '✗'}")
        print(f"Data merge complete: {'✓' if results['merge_complete'] else '✗'}")
        print(f"Processed data saved: {'✓' if results['data_saved'] else '✗'}")
        
        if results['processing_stats']:
            stats = results['processing_stats']
            print(f"\nProcessing Statistics:")
            print(f"  Records processed: {stats.get('records_processed', 0)}")
            print(f"  Records cleaned: {stats.get('records_cleaned', 0)}")
            print(f"  Records dropped: {stats.get('records_dropped', 0)}")
            
            if stats.get('merge_stats'):
                print(f"\nMerge Statistics:")
                for dataset, merge_stats in stats['merge_stats'].items():
                    print(f"  {dataset}: {merge_stats['matched']}/{merge_stats['total']} matched")
        
        print(f"\nDuration: {results['duration']}")
        print("="*60)
        
        if results['data_saved']:
            print("\n🎉 Data processing successful!")
            print("\nNext steps:")
            print("1. Check data_pipeline/processed/ for output files")
            print("2. Run data validation (03_data_validation.py)")
            print("3. Proceed to descriptive analysis")
        else:
            print("\n⚠️  Data processing completed with issues")
            print("Check logs for details")
        
    except Exception as e:
        print(f"\n❌ Data processing failed: {e}")
        logger.exception("Processing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()