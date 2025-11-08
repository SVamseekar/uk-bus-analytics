"""
Parse TransXChange XML files to extract route geometries, stop sequences, and trip schedules
Creates route_geometries.csv and route_metrics.csv for Category C analysis
"""
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from math import radians, cos, sin, asin, sqrt
from loguru import logger

# Setup logging
logger.add("logs/transxchange_parsing_{time}.log", rotation="100 MB")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c  # Radius of earth in kilometers

    return km


class TransXChangeParser:
    """Parse TransXChange XML files to extract route and trip data"""

    def __init__(self, stops_data_path: str = 'data/processed/outputs/all_stops_deduplicated.csv'):
        """Initialize parser with stops data for coordinate lookup"""
        logger.info("Loading stops data for coordinate lookup...")
        self.stops_df = pd.read_csv(stops_data_path,
                                      usecols=['stop_id', 'latitude', 'longitude', 'region_code', 'LA (code)', 'LA (name)'],
                                      low_memory=False)
        logger.info(f"Loaded {len(self.stops_df):,} stops")

        # Create stop lookup dictionary
        self.stop_coords = {}
        for _, row in self.stops_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                self.stop_coords[row['stop_id']] = {
                    'lat': row['latitude'],
                    'lon': row['longitude'],
                    'region': row['region_code'],
                    'la_code': row['LA (code)'],
                    'la_name': row['LA (name)']
                }

        logger.info(f"Created coordinate lookup for {len(self.stop_coords):,} stops")

    def parse_xml_file(self, xml_path: str) -> Dict:
        """
        Parse a single TransXChange XML file or ZIP containing XMLs

        Returns dict with:
        - routes: list of route info
        - journey_patterns: list of stop sequences
        - vehicle_journeys: list of trip schedules
        """
        import zipfile

        # Check if it's a real ZIP archive
        try:
            with zipfile.ZipFile(xml_path, 'r') as zip_ref:
                # It's a valid ZIP - extract and parse each XML inside
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]

                if not xml_files:
                    logger.warning(f"No XML files in ZIP: {xml_path}")
                    return None

                # Parse all XMLs in the ZIP and combine results
                combined_result = {
                    'source_file': Path(xml_path).name,
                    'routes': [],
                    'journey_patterns': [],
                    'vehicle_journeys': [],
                    'services': []
                }

                for xml_file in xml_files:
                    with zip_ref.open(xml_file) as xml_content:
                        try:
                            tree = ET.parse(xml_content)
                            root = tree.getroot()
                            result = self._extract_from_root(root, Path(xml_path).name)

                            # Merge results
                            combined_result['services'].extend(result['services'])
                            combined_result['journey_patterns'].extend(result['journey_patterns'])
                            combined_result['vehicle_journeys'].extend(result['vehicle_journeys'])

                        except Exception as e:
                            logger.debug(f"Error parsing {xml_file} in {xml_path}: {e}")
                            continue

                return combined_result if (combined_result['journey_patterns'] or combined_result['vehicle_journeys']) else None

        except zipfile.BadZipFile:
            # Not a ZIP - try as plain XML
            pass

        # Parse as plain XML file
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            return self._extract_from_root(root, Path(xml_path).name)
        except Exception as e:
            logger.error(f"Error parsing {xml_path}: {e}")
            return None

    def _extract_from_root(self, root, source_file: str) -> Dict:
        """
        Extract data from parsed XML root element
        """
        # Get namespace
        ns = {'txc': 'http://www.transxchange.org.uk/'}

        result = {
            'source_file': source_file,
            'routes': [],
            'journey_patterns': [],
            'vehicle_journeys': [],
            'services': []
        }

        # Extract Services (contains route metadata)
        services = root.findall('.//txc:Service', ns)
        for service in services:
            service_code_elem = service.find('.//txc:ServiceCode', ns)
            service_code = service_code_elem.text if service_code_elem is not None else 'unknown'

            line_elem = service.find('.//txc:LineName', ns)
            line_name = line_elem.text if line_elem is not None else ''

            desc_elem = service.find('.//txc:Description', ns)
            description = desc_elem.text if desc_elem is not None else ''

            result['services'].append({
                'service_code': service_code,
                'line_name': line_name,
                'description': description
            })

        # Extract Journey Patterns (stop sequences)
        journey_patterns = root.findall('.//txc:JourneyPattern', ns)
        for jp in journey_patterns:
            jp_id_elem = jp.get('id') or jp.find('.//txc:PrivateCode', ns)
            jp_id = jp_id_elem if isinstance(jp_id_elem, str) else (jp_id_elem.text if jp_id_elem is not None else 'unknown')

            # Get stop sequence from JourneyPatternSection
            sections = jp.findall('.//txc:JourneyPatternSection', ns)
            stop_sequence = []

            for section in sections:
                timing_links = section.findall('.//txc:JourneyPatternTimingLink', ns)

                for link in timing_links:
                    from_elem = link.find('.//txc:From/txc:StopPointRef', ns)
                    to_elem = link.find('.//txc:To/txc:StopPointRef', ns)
                    runtime_elem = link.find('.//txc:RunTime', ns)

                    if from_elem is not None:
                        stop_sequence.append({
                            'stop_id': from_elem.text,
                            'runtime_mins': self._parse_duration(runtime_elem.text) if runtime_elem is not None else None
                        })

                    # Add the 'to' stop at the end
                    if to_elem is not None and link == timing_links[-1]:
                        stop_sequence.append({
                            'stop_id': to_elem.text,
                            'runtime_mins': None
                        })

            if stop_sequence:
                result['journey_patterns'].append({
                    'pattern_id': jp_id,
                    'stops': stop_sequence,
                    'num_stops': len(stop_sequence)
                })

        # Extract Vehicle Journeys (trip schedules)
        vehicle_journeys = root.findall('.//txc:VehicleJourney', ns)
        for vj in vehicle_journeys:
            vj_code_elem = vj.find('.//txc:PrivateCode', ns) or vj.find('.//txc:VehicleJourneyCode', ns)
            vj_code = vj_code_elem.text if vj_code_elem is not None else 'unknown'

            departure_elem = vj.find('.//txc:DepartureTime', ns)
            departure_time = departure_elem.text if departure_elem is not None else None

            jp_ref_elem = vj.find('.//txc:JourneyPatternRef', ns)
            jp_ref = jp_ref_elem.text if jp_ref_elem is not None else None

            result['vehicle_journeys'].append({
                'journey_code': vj_code,
                'departure_time': departure_time,
                'pattern_ref': jp_ref
            })

        return result

    def _parse_duration(self, duration_str: str) -> float:
        """Parse PT duration string (e.g., 'PT5M', 'PT1H30M') to minutes"""
        if not duration_str or not duration_str.startswith('PT'):
            return None

        try:
            duration_str = duration_str[2:]  # Remove 'PT'
            hours = 0
            minutes = 0

            if 'H' in duration_str:
                parts = duration_str.split('H')
                hours = int(parts[0])
                duration_str = parts[1]

            if 'M' in duration_str:
                minutes = int(duration_str.replace('M', ''))

            return hours * 60 + minutes
        except:
            return None

    def calculate_route_metrics(self, parsed_data: Dict) -> List[Dict]:
        """
        Calculate route metrics from parsed data

        Returns list of route records with:
        - route_id, route_length_km, num_stops, trips_per_day, regions_served, las_served
        """
        routes = []

        for pattern in parsed_data['journey_patterns']:
            # Calculate route length from stop sequence
            stops = pattern['stops']
            route_length = 0
            regions = set()
            las = set()
            valid_stops = 0

            for i in range(len(stops) - 1):
                stop1_id = stops[i]['stop_id']
                stop2_id = stops[i + 1]['stop_id']

                if stop1_id in self.stop_coords and stop2_id in self.stop_coords:
                    coord1 = self.stop_coords[stop1_id]
                    coord2 = self.stop_coords[stop2_id]

                    # Calculate distance
                    distance = haversine_distance(
                        coord1['lat'], coord1['lon'],
                        coord2['lat'], coord2['lon']
                    )
                    route_length += distance

                    # Track regions and LAs
                    regions.add(coord1['region'])
                    regions.add(coord2['region'])
                    if pd.notna(coord1['la_code']):
                        las.add(coord1['la_code'])
                    if pd.notna(coord2['la_code']):
                        las.add(coord2['la_code'])

                    valid_stops += 1

            # Count trips (vehicle journeys) for this pattern
            trips = [vj for vj in parsed_data['vehicle_journeys']
                     if vj.get('pattern_ref') == pattern['pattern_id']]

            # Service metadata
            service_info = parsed_data['services'][0] if parsed_data['services'] else {}

            routes.append({
                'source_file': parsed_data['source_file'],
                'pattern_id': pattern['pattern_id'],
                'service_code': service_info.get('service_code', 'unknown'),
                'line_name': service_info.get('line_name', ''),
                'description': service_info.get('description', ''),
                'route_length_km': round(route_length, 2),
                'num_stops': len(stops),
                'valid_stops': valid_stops,
                'trips_per_day': len(trips),
                'num_regions': len(regions),
                'regions_served': ','.join(sorted(regions)),
                'num_las': len(las),
                'las_served': ','.join(str(int(la)) for la in sorted(las) if pd.notna(la))
            })

        return routes

    def parse_all_files(self, pattern: str = 'data/raw/regions/*/*.zip') -> pd.DataFrame:
        """
        Parse all TransXChange files and create combined route metrics dataset
        """
        xml_files = glob.glob(pattern)
        logger.info(f"Found {len(xml_files)} TransXChange files to parse")

        all_routes = []
        errors = 0

        for i, xml_path in enumerate(xml_files):
            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i+1}/{len(xml_files)} files parsed, {len(all_routes)} routes extracted")

            parsed_data = self.parse_xml_file(xml_path)

            if parsed_data:
                route_metrics = self.calculate_route_metrics(parsed_data)
                all_routes.extend(route_metrics)
            else:
                errors += 1

        logger.info(f"Parsing complete: {len(all_routes)} routes extracted from {len(xml_files)} files ({errors} errors)")

        # Create DataFrame
        if not all_routes:
            logger.error("No routes extracted from any files!")
            return pd.DataFrame()

        routes_df = pd.DataFrame(all_routes)

        # Add calculated metrics
        if len(routes_df) > 0:
            routes_df['mileage_per_day'] = routes_df['route_length_km'] * routes_df['trips_per_day']
            routes_df['avg_stop_spacing_km'] = routes_df.apply(
                lambda row: row['route_length_km'] / (row['num_stops'] - 1) if row['num_stops'] > 1 else 0,
                axis=1
            )

        return routes_df


def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("TRANSXCHANGE PARSING PIPELINE")
    logger.info("=" * 80)

    # Initialize parser
    parser = TransXChangeParser()

    # Parse all files
    routes_df = parser.parse_all_files()

    # Save results
    output_path = 'data/processed/outputs/route_metrics.csv'
    routes_df.to_csv(output_path, index=False)
    logger.success(f"Saved {len(routes_df)} route records to {output_path}")

    # Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Total routes: {len(routes_df):,}")
    logger.info(f"Avg route length: {routes_df['route_length_km'].mean():.2f} km")
    logger.info(f"Avg stops per route: {routes_df['num_stops'].mean():.1f}")
    logger.info(f"Avg trips per day: {routes_df['trips_per_day'].mean():.1f}")
    logger.info(f"Cross-region routes: {(routes_df['num_regions'] > 1).sum():,}")
    logger.info(f"Cross-LA routes: {(routes_df['num_las'] > 1).sum():,}")

    # Top 10 longest routes
    logger.info("\nTop 10 longest routes:")
    top_routes = routes_df.nlargest(10, 'route_length_km')[['line_name', 'route_length_km', 'num_stops', 'description']]
    for _, route in top_routes.iterrows():
        logger.info(f"  {route['line_name']}: {route['route_length_km']:.1f} km, {route['num_stops']} stops - {route['description'][:50]}")

    logger.success("\n✅ TransXChange parsing complete!")


if __name__ == '__main__':
    main()
