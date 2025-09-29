"""
TransXchange Stop Extractor - Extract real stop data from your TransXchange files
Extracts stop IDs from routes and attempts to find coordinates in the XML
"""
import sys
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import DATA_RAW, DATA_PROCESSED


class TransXchangeStopExtractor:
    """Extract stops from TransXchange XML files"""
    
    def __init__(self):
        self.stops_data = []
        self.namespaces_tried = [
            {'txc': 'http://www.transxchange.org.uk/'},
            {}  # No namespace fallback
        ]
    
    def extract_from_zip(self, zip_path: Path) -> pd.DataFrame:
        """Extract all stops from a TransXchange ZIP file"""
        logger.info(f"Processing {zip_path.name}")
        
        stops_dict = {}  # stop_id -> stop_data
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                
                logger.info(f"Found {len(xml_files)} XML files")
                
                for xml_file in xml_files:
                    try:
                        xml_content = zip_ref.read(xml_file)
                        root = ET.fromstring(xml_content)
                        
                        # Try to extract stops with different strategies
                        file_stops = self._extract_stops_from_xml(root, xml_file)
                        
                        # Merge into main dictionary
                        for stop_id, stop_data in file_stops.items():
                            if stop_id not in stops_dict:
                                stops_dict[stop_id] = stop_data
                            else:
                                # Update if we have more information
                                if stop_data.get('latitude') and not stops_dict[stop_id].get('latitude'):
                                    stops_dict[stop_id].update(stop_data)
                        
                    except Exception as e:
                        logger.debug(f"Skipped {xml_file}: {e}")
                        continue
            
            if stops_dict:
                df = pd.DataFrame(list(stops_dict.values()))
                logger.success(f"Extracted {len(df)} stops from {zip_path.name}")
                
                # Add metadata
                df['source_file'] = zip_path.name
                
                return df
            else:
                logger.warning(f"No stops found in {zip_path.name}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to process {zip_path.name}: {e}")
            return pd.DataFrame()
    
    def _extract_stops_from_xml(self, root: ET.Element, filename: str) -> Dict:
        """Extract stops from a single XML file using multiple strategies"""
        stops = {}
        
        # Strategy 1: Look for explicit StopPoints section
        stops.update(self._extract_from_stoppoints(root))
        
        # Strategy 2: Extract from AnnotatedStopPointRef
        stops.update(self._extract_from_annotated_stops(root))
        
        # Strategy 3: Extract stop references from routes
        stops.update(self._extract_from_routes(root))
        
        return stops
    
    def _extract_from_stoppoints(self, root: ET.Element) -> Dict:
        """Extract from StopPoints section (most complete data)"""
        stops = {}
        
        # First try with namespace
        for ns in self.namespaces_tried:
            try:
                stop_points = root.findall('.//txc:StopPoints/txc:StopPoint', ns)
                if stop_points:
                    for sp in stop_points:
                        stop_data = self._parse_stoppoint(sp, ns)
                        if stop_data and stop_data['stop_id']:
                            stops[stop_data['stop_id']] = stop_data
                    if stops:
                        return stops
            except:
                pass
        
        # Try without namespace using iteration
        for elem in root.iter():
            if elem.tag.endswith('StopPoint') or elem.tag == 'StopPoint':
                stop_data = self._parse_stoppoint(elem, {})
                if stop_data and stop_data['stop_id']:
                    stops[stop_data['stop_id']] = stop_data
        
        return stops
    
    def _extract_from_annotated_stops(self, root: ET.Element) -> Dict:
        """Extract from AnnotatedStopPointRef sections"""
        stops = {}
        
        # Try with namespace
        for ns in self.namespaces_tried:
            try:
                annotated_stops = root.findall('.//txc:AnnotatedStopPointRef', ns)
                if annotated_stops:
                    for asp in annotated_stops:
                        stop_ref = asp.find('txc:StopPointRef', ns) or asp.find('StopPointRef')
                        common_name = asp.find('txc:CommonName', ns) or asp.find('CommonName')
                        
                        if stop_ref is not None and stop_ref.text:
                            stop_id = stop_ref.text.strip()
                            stop_name = common_name.text.strip() if common_name is not None else None
                            
                            stops[stop_id] = {
                                'stop_id': stop_id,
                                'stop_name': stop_name,
                                'latitude': None,
                                'longitude': None,
                                'has_coordinates': False
                            }
            except:
                pass
        
        # Try without namespace using iteration
        if not stops:
            for elem in root.iter():
                if elem.tag.endswith('AnnotatedStopPointRef') or elem.tag == 'AnnotatedStopPointRef':
                    # Find child elements
                    stop_ref = None
                    common_name = None
                    
                    for child in elem:
                        if child.tag.endswith('StopPointRef') or child.tag == 'StopPointRef':
                            stop_ref = child
                        elif child.tag.endswith('CommonName') or child.tag == 'CommonName':
                            common_name = child
                    
                    if stop_ref is not None and stop_ref.text:
                        stop_id = stop_ref.text.strip()
                        stop_name = common_name.text.strip() if common_name is not None else None
                        
                        stops[stop_id] = {
                            'stop_id': stop_id,
                            'stop_name': stop_name,
                            'latitude': None,
                            'longitude': None,
                            'has_coordinates': False
                        }
        
        return stops
    
    def _extract_from_routes(self, root: ET.Element) -> Dict:
        """Extract stop IDs referenced in routes"""
        stops = {}
        
        # Iterate through all elements to find RouteLink regardless of namespace
        for elem in root.iter():
            if elem.tag.endswith('RouteLink') or elem.tag == 'RouteLink':
                # Look for From and To elements
                for child in elem:
                    if child.tag.endswith('From') or child.tag == 'From':
                        # Find StopPointRef
                        for subchild in child:
                            if subchild.tag.endswith('StopPointRef') or subchild.tag == 'StopPointRef':
                                if subchild.text:
                                    stop_id = subchild.text.strip()
                                    if stop_id not in stops:
                                        stops[stop_id] = {
                                            'stop_id': stop_id,
                                            'stop_name': None,
                                            'latitude': None,
                                            'longitude': None,
                                            'has_coordinates': False
                                        }
                    
                    elif child.tag.endswith('To') or child.tag == 'To':
                        # Find StopPointRef
                        for subchild in child:
                            if subchild.tag.endswith('StopPointRef') or subchild.tag == 'StopPointRef':
                                if subchild.text:
                                    stop_id = subchild.text.strip()
                                    if stop_id not in stops:
                                        stops[stop_id] = {
                                            'stop_id': stop_id,
                                            'stop_name': None,
                                            'latitude': None,
                                            'longitude': None,
                                            'has_coordinates': False
                                        }
            
            # Also check JourneyPatternTimingLink
            elif elem.tag.endswith('JourneyPatternTimingLink') or elem.tag == 'JourneyPatternTimingLink':
                for child in elem:
                    if child.tag.endswith('From') or child.tag == 'From':
                        for subchild in child:
                            if subchild.tag.endswith('StopPointRef') or subchild.tag == 'StopPointRef':
                                if subchild.text:
                                    stop_id = subchild.text.strip()
                                    if stop_id not in stops:
                                        stops[stop_id] = {
                                            'stop_id': stop_id,
                                            'stop_name': None,
                                            'latitude': None,
                                            'longitude': None,
                                            'has_coordinates': False
                                        }
                    
                    elif child.tag.endswith('To') or child.tag == 'To':
                        for subchild in child:
                            if subchild.tag.endswith('StopPointRef') or subchild.tag == 'StopPointRef':
                                if subchild.text:
                                    stop_id = subchild.text.strip()
                                    if stop_id not in stops:
                                        stops[stop_id] = {
                                            'stop_id': stop_id,
                                            'stop_name': None,
                                            'latitude': None,
                                            'longitude': None,
                                            'has_coordinates': False
                                        }
        
        return stops
    
    def _parse_stoppoint(self, stop_element: ET.Element, ns: Dict) -> Dict:
        """Parse a StopPoint element to extract all data"""
        try:
            stop_data = {
                'stop_id': None,
                'stop_name': None,
                'latitude': None,
                'longitude': None,
                'has_coordinates': False
            }
            
            # Stop ID (AtcoCode attribute)
            stop_data['stop_id'] = stop_element.get('AtcoCode')
            
            # Iterate through children for namespace-agnostic parsing
            for child in stop_element:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag == 'Descriptor':
                    for desc_child in child:
                        desc_tag = desc_child.tag.split('}')[-1] if '}' in desc_child.tag else desc_child.tag
                        if desc_tag == 'CommonName' and desc_child.text:
                            stop_data['stop_name'] = desc_child.text
                
                elif tag == 'Place':
                    for place_child in child:
                        place_tag = place_child.tag.split('}')[-1] if '}' in place_child.tag else place_child.tag
                        if place_tag == 'Location':
                            lat_val = None
                            lon_val = None
                            for loc_child in place_child:
                                loc_tag = loc_child.tag.split('}')[-1] if '}' in loc_child.tag else loc_child.tag
                                if loc_tag == 'Latitude' and loc_child.text:
                                    lat_val = loc_child.text
                                elif loc_tag == 'Longitude' and loc_child.text:
                                    lon_val = loc_child.text
                            
                            if lat_val and lon_val:
                                try:
                                    stop_data['latitude'] = float(lat_val)
                                    stop_data['longitude'] = float(lon_val)
                                    stop_data['has_coordinates'] = True
                                except (ValueError, TypeError):
                                    pass
            
            return stop_data
            
        except Exception as e:
            logger.debug(f"Failed to parse stop element: {e}")
            return None


def process_all_transxchange_files():
    """Process all TransXchange files and combine results"""
    logger.info("Processing all TransXchange files to extract stops")
    
    tx_dir = DATA_RAW / 'transxchange'
    if not tx_dir.exists():
        logger.error(f"TransXchange directory not found: {tx_dir}")
        return None
    
    zip_files = list(tx_dir.glob('*.zip'))
    
    if not zip_files:
        logger.error("No TransXchange ZIP files found")
        return None
    
    logger.info(f"Found {len(zip_files)} TransXchange files")
    
    extractor = TransXchangeStopExtractor()
    all_stops = []
    
    for zip_file in zip_files:
        stops_df = extractor.extract_from_zip(zip_file)
        if len(stops_df) > 0:
            all_stops.append(stops_df)
    
    if not all_stops:
        logger.error("No stops extracted from any TransXchange file")
        return None
    
    # Combine all stops
    combined = pd.concat(all_stops, ignore_index=True)
    
    # Remove duplicates, keeping entries with coordinates if available
    combined = combined.sort_values('has_coordinates', ascending=False)
    combined = combined.drop_duplicates(subset=['stop_id'], keep='first')
    
    logger.success(f"Total unique stops: {len(combined)}")
    
    with_coords = combined['has_coordinates'].sum()
    without_coords = len(combined) - with_coords
    
    logger.info(f"Stops with coordinates: {with_coords}")
    logger.info(f"Stops without coordinates: {without_coords}")
    
    # Save to processed directory
    output_path = DATA_PROCESSED / 'stops_extracted.csv'
    combined.to_csv(output_path, index=False)
    logger.success(f"Saved to: {output_path}")
    
    return combined


def main():
    """Run stop extraction"""
    print("="*60)
    print("TRANSXCHANGE STOP EXTRACTION TOOL")
    print("="*60)
    print("\nExtracting stops from your real TransXchange data...")
    print()
    
    stops_df = process_all_transxchange_files()
    
    if stops_df is not None:
        print("\n" + "="*60)
        print("EXTRACTION RESULTS")
        print("="*60)
        print(f"\nTotal unique stops extracted: {len(stops_df)}")
        print(f"Stops with coordinates: {stops_df['has_coordinates'].sum()}")
        print(f"Stops without coordinates: {(~stops_df['has_coordinates']).sum()}")
        
        if stops_df['has_coordinates'].sum() > 0:
            print("\n✅ SUCCESS! Found stops with coordinates")
            print("\nSample stops with coordinates:")
            with_coords = stops_df[stops_df['has_coordinates']].head(10)
            print(with_coords[['stop_id', 'stop_name', 'latitude', 'longitude']])
        else:
            print("\n⚠️  WARNING: No coordinate data in TransXchange files")
            print("\nThis is common with UK TransXchange data.")
            print("\nSOLUTION: Download NaPTAN database for coordinates")
            print("1. Visit: https://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx")
            print("2. Request 'Stops' CSV export (free)")
            print("3. Save as: data_pipeline/raw/naptan/Stops.csv")
            print("4. Run: python utils/merge_naptan_coordinates.py")
        
        print("\n" + "="*60)
        print(f"\nOutput saved to: data_pipeline/processed/stops_extracted.csv")
        print("="*60)
    else:
        print("\n❌ Failed to extract stops")
        print("Check logs for details")


if __name__ == "__main__":
    main()