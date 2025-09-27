"""
Simple GTFS parser for immediate use
"""
import zipfile
import pandas as pd
from pathlib import Path
from loguru import logger

class GTFSParser:
    """Simple GTFS parser that just validates basic structure"""
    
    def __init__(self, gtfs_path):
        self.gtfs_path = Path(gtfs_path)
        self.feed_data = {}
    
    def parse_feed(self):
        """Basic parse - just check if it's a valid GTFS zip"""
        try:
            if self.gtfs_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(self.gtfs_path, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    
                    # Check for required GTFS files
                    required_files = ['stops.txt', 'routes.txt', 'trips.txt']
                    found_files = [f for f in required_files if f in files]
                    
                    self.feed_data = {f: True for f in found_files}
                    
                    if len(found_files) >= 2:  # At least 2 core files
                        return self.feed_data
                    
            return None
        except Exception as e:
            logger.error(f"GTFS parsing failed: {e}")
            return None
    
    def validate_feed(self):
        """Basic validation"""
        issues = {'critical': [], 'warnings': [], 'info': []}
        
        if not self.feed_data:
            issues['critical'].append("No GTFS data loaded")
        else:
            issues['info'].append(f"Found {len(self.feed_data)} GTFS files")
            
        return issues
    
    def get_summary(self):
        """Get basic summary"""
        return {
            'parsing_method': 'simple_validation',
            'files_loaded': list(self.feed_data.keys()) if self.feed_data else [],
            'record_counts': {}
        }