"""
UK Transport Data Parser - handles both GTFS and TransXchange formats
Based on real UK operator data structures from BODS
"""
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from loguru import logger
import re

class UKTransportParser:
    """
    Parser for UK transport data - handles GTFS (.txt) and TransXchange (.xml)
    Designed for real BODS data structures
    """
    
    def __init__(self, data_path: Union[str, Path]):
        self.data_path = Path(data_path)
        self.format_type = None
        self.parsed_data = {}
        self.validation_issues = {'critical': [], 'warnings': [], 'info': []}
        
    def detect_format(self) -> str:
        """Detect if data is GTFS or TransXchange"""
        try:
            if not self.data_path.exists():
                return 'unknown'
                
            if self.data_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
                    files = zip_ref.namelist()
                    
                    txt_files = [f for f in files if f.endswith('.txt')]
                    xml_files = [f for f in files if f.endswith('.xml')]
                    
                    if txt_files and any(f in files for f in ['stops.txt', 'routes.txt', 'trips.txt']):
                        self.format_type = 'gtfs'
                        return 'gtfs'
                    elif xml_files:
                        self.format_type = 'transxchange'
                        return 'transxchange'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Format detection failed: {e}")
            return 'unknown'
    
    def parse_data(self) -> Dict:
        """Parse data based on detected format"""
        format_type = self.detect_format()
        
        if format_type == 'gtfs':
            return self._parse_gtfs()
        elif format_type == 'transxchange':
            return self._parse_transxchange()
        else:
            logger.error(f"Unknown or unsupported format: {format_type}")
            return {}
    
    def _parse_gtfs(self) -> Dict:
        """Parse GTFS format data"""
        logger.info("Parsing GTFS format data")
        
        try:
            with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
                gtfs_files = ['agency.txt', 'stops.txt', 'routes.txt', 'trips.txt', 
                             'stop_times.txt', 'calendar.txt', 'calendar_dates.txt']
                
                for gtfs_file in gtfs_files:
                    if gtfs_file in zip_ref.namelist():
                        try:
                            with zip_ref.open(gtfs_file) as f:
                                df = pd.read_csv(f, dtype=str)
                                self.parsed_data[gtfs_file.replace('.txt', '')] = df
                                logger.info(f"Loaded {gtfs_file}: {len(df)} records")
                        except Exception as e:
                            logger.warning(f"Failed to parse {gtfs_file}: {e}")
                            self.validation_issues['warnings'].append(f"Could not read {gtfs_file}: {e}")
                
                return self.parsed_data
                
        except Exception as e:
            logger.error(f"GTFS parsing failed: {e}")
            self.validation_issues['critical'].append(f"GTFS parsing failed: {e}")
            return {}
    
    def _parse_transxchange(self) -> Dict:
        """Parse TransXchange format data - the reality of UK bus data"""
        logger.info("Parsing TransXchange format data")
        
        stops_data = []
        routes_data = []
        services_data = []
        
        try:
            with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                
                logger.info(f"Processing {len(xml_files)} TransXchange files")
                
                for xml_file in xml_files[:10]:  # Limit to first 10 files to avoid memory issues
                    try:
                        xml_content = zip_ref.read(xml_file)
                        file_stops, file_routes, file_services = self._parse_transxchange_xml(xml_content, xml_file)
                        
                        stops_data.extend(file_stops)
                        routes_data.extend(file_routes)
                        services_data.extend(file_services)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse {xml_file}: {e}")
                        continue
                
                # Convert to DataFrames
                if stops_data:
                    self.parsed_data['stops'] = pd.DataFrame(stops_data)
                    logger.info(f"Extracted {len(stops_data)} stops")
                
                if routes_data:
                    self.parsed_data['routes'] = pd.DataFrame(routes_data)
                    logger.info(f"Extracted {len(routes_data)} routes")
                
                if services_data:
                    self.parsed_data['services'] = pd.DataFrame(services_data)
                    logger.info(f"Extracted {len(services_data)} services")
                
                return self.parsed_data
                
        except Exception as e:
            logger.error(f"TransXchange parsing failed: {e}")
            self.validation_issues['critical'].append(f"TransXchange parsing failed: {e}")
            return {}
    
    def _parse_transxchange_xml(self, xml_content: bytes, filename: str) -> Tuple[List, List, List]:
        """Parse individual TransXchange XML file"""
        stops = []
        routes = []
        services = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespaces - TransXchange uses various namespace patterns
            namespaces = {
                'txc': 'http://www.transxchange.org.uk/',
                'nptg': 'http://www.naptan.org.uk/'
            }
            
            # Try to find namespace in root
            if root.tag.startswith('{'):
                namespace_uri = root.tag.split('}')[0][1:]
                namespaces['txc'] = namespace_uri
            
            # Extract stops/stop points
            stop_selectors = [
                './/txc:StopPoint',
                './/txc:AnnotatedStopPointRef',
                './/StopPoint',  # No namespace fallback
                './/AnnotatedStopPointRef'
            ]
            
            for selector in stop_selectors:
                stop_points = root.findall(selector, namespaces)
                if stop_points:
                    for stop_point in stop_points:
                        stop_data = self._extract_stop_data(stop_point, namespaces, filename)
                        if stop_data:
                            stops.append(stop_data)
                    break  # Use first successful selector
            
            # Extract services
            service_selectors = [
                './/txc:Service',
                './/Service'
            ]
            
            for selector in service_selectors:
                services_found = root.findall(selector, namespaces)
                if services_found:
                    for service in services_found:
                        service_data = self._extract_service_data(service, namespaces, filename)
                        if service_data:
                            services.append(service_data)
                    break
            
            # Extract routes/lines
            route_selectors = [
                './/txc:Route',
                './/txc:Line',
                './/Route',
                './/Line'
            ]
            
            for selector in route_selectors:
                routes_found = root.findall(selector, namespaces)
                if routes_found:
                    for route in routes_found:
                        route_data = self._extract_route_data(route, namespaces, filename)
                        if route_data:
                            routes.append(route_data)
                    break
            
        except ET.ParseError as e:
            logger.debug(f"XML parse error in {filename}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error parsing {filename}: {e}")
        
        return stops, routes, services
    
    def _extract_stop_data(self, stop_element, namespaces: Dict, filename: str) -> Optional[Dict]:
        """Extract stop data from TransXchange XML element"""
        try:
            stop_data = {
                'source_file': filename,
                'stop_id': None,
                'stop_name': None,
                'latitude': None,
                'longitude': None,
                'locality': None
            }
            
            # Stop ID
            stop_data['stop_id'] = (
                stop_element.get('AtcoCode') or 
                stop_element.get('StopPointRef') or 
                stop_element.get('id')
            )
            
            # Stop name
            descriptor = stop_element.find('txc:Descriptor', namespaces)
            if descriptor is not None:
                common_name = descriptor.find('txc:CommonName', namespaces)
                if common_name is not None:
                    stop_data['stop_name'] = common_name.text
            
            # Location data
            place = stop_element.find('txc:Place', namespaces)
            if place is not None:
                location = place.find('txc:Location', namespaces)
                if location is not None:
                    lat_elem = location.find('txc:Latitude', namespaces)
                    lon_elem = location.find('txc:Longitude', namespaces)
                    
                    if lat_elem is not None and lon_elem is not None:
                        try:
                            stop_data['latitude'] = float(lat_elem.text)
                            stop_data['longitude'] = float(lon_elem.text)
                        except ValueError:
                            pass
                
                # Locality
                nptg_locality = place.find('txc:NptgLocalityRef', namespaces)
                if nptg_locality is not None:
                    stop_data['locality'] = nptg_locality.text
            
            return stop_data if stop_data['stop_id'] else None
            
        except Exception as e:
            logger.debug(f"Failed to extract stop data: {e}")
            return None
    
    def _extract_service_data(self, service_element, namespaces: Dict, filename: str) -> Optional[Dict]:
        """Extract service data from TransXchange XML element"""
        try:
            service_data = {
                'source_file': filename,
                'service_code': None,
                'service_description': None,
                'operator': None,
                'mode': None
            }
            
            # Service code
            service_data['service_code'] = service_element.get('ServiceCode')
            
            # Description
            description = service_element.find('txc:Description', namespaces)
            if description is not None:
                service_data['service_description'] = description.text
            
            # Mode (bus, coach, etc.)
            mode = service_element.find('txc:Mode', namespaces)
            if mode is not None:
                service_data['mode'] = mode.text
            
            return service_data if service_data['service_code'] else None
            
        except Exception as e:
            logger.debug(f"Failed to extract service data: {e}")
            return None
    
    def _extract_route_data(self, route_element, namespaces: Dict, filename: str) -> Optional[Dict]:
        """Extract route data from TransXchange XML element"""
        try:
            route_data = {
                'source_file': filename,
                'route_id': None,
                'route_description': None,
                'route_section_count': 0
            }
            
            # Route ID
            route_data['route_id'] = route_element.get('id')
            
            # Description
            description = route_element.find('txc:Description', namespaces)
            if description is not None:
                route_data['route_description'] = description.text
            
            # Count route sections
            sections = route_element.findall('txc:RouteSection', namespaces)
            route_data['route_section_count'] = len(sections)
            
            return route_data if route_data['route_id'] else None
            
        except Exception as e:
            logger.debug(f"Failed to extract route data: {e}")
            return None
    
    def validate_data(self) -> Dict:
        """Validate parsed transport data"""
        if not self.parsed_data:
            self.validation_issues['critical'].append("No data was parsed")
            return self.validation_issues
        
        # Validate based on format
        if self.format_type == 'gtfs':
            self._validate_gtfs()
        elif self.format_type == 'transxchange':
            self._validate_transxchange()
        
        return self.validation_issues
    
    def _validate_gtfs(self):
        """Validate GTFS data"""
        required_files = ['agency', 'stops', 'routes', 'trips']
        
        for req_file in required_files:
            if req_file not in self.parsed_data:
                self.validation_issues['warnings'].append(f"Missing recommended file: {req_file}")
        
        # Validate stops
        if 'stops' in self.parsed_data:
            stops_df = self.parsed_data['stops']
            
            # Check for required fields
            required_stop_fields = ['stop_id', 'stop_name']
            for field in required_stop_fields:
                if field not in stops_df.columns:
                    self.validation_issues['critical'].append(f"Missing required stop field: {field}")
            
            # Check coordinate validity
            if 'stop_lat' in stops_df.columns and 'stop_lon' in stops_df.columns:
                invalid_coords = stops_df[
                    (stops_df['stop_lat'].astype(str) == '') | 
                    (stops_df['stop_lon'].astype(str) == '') |
                    (pd.to_numeric(stops_df['stop_lat'], errors='coerce').isna()) |
                    (pd.to_numeric(stops_df['stop_lon'], errors='coerce').isna())
                ]
                
                if len(invalid_coords) > 0:
                    self.validation_issues['warnings'].append(f"{len(invalid_coords)} stops have invalid coordinates")
    
    def _validate_transxchange(self):
        """Validate TransXchange data"""
        # Check if we extracted any meaningful data
        data_types = ['stops', 'routes', 'services']
        extracted_types = [dt for dt in data_types if dt in self.parsed_data and len(self.parsed_data[dt]) > 0]
        
        if not extracted_types:
            self.validation_issues['critical'].append("No TransXchange data could be extracted")
            return
        
        self.validation_issues['info'].append(f"Successfully extracted: {', '.join(extracted_types)}")
        
        # Validate stops if present
        if 'stops' in self.parsed_data:
            stops_df = self.parsed_data['stops']
            
            # Check for stops with coordinates
            coord_stops = stops_df[
                (stops_df['latitude'].notna()) & 
                (stops_df['longitude'].notna())
            ]
            
            coord_percentage = len(coord_stops) / len(stops_df) * 100 if len(stops_df) > 0 else 0
            
            if coord_percentage < 50:
                self.validation_issues['warnings'].append(f"Only {coord_percentage:.1f}% of stops have coordinates")
            else:
                self.validation_issues['info'].append(f"{coord_percentage:.1f}% of stops have coordinates")
    
    def get_summary(self) -> Dict:
        """Get summary of parsed data"""
        summary = {
            'format': self.format_type,
            'file_path': str(self.data_path),
            'parsed_at': pd.Timestamp.now().isoformat(),
            'data_types': list(self.parsed_data.keys()),
            'record_counts': {}
        }
        
        for data_type, df in self.parsed_data.items():
            if isinstance(df, pd.DataFrame):
                summary['record_counts'][data_type] = len(df)
        
        summary['validation_issues'] = self.validation_issues
        
        return summary