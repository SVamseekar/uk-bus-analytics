"""
Enhanced TransXChange Parser for Category C Analytics
Extracts:
- Stop sequences (for overlap analysis)
- First/last stop coordinates (for circuity index)
- Departure times (for temporal patterns)
"""
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import zipfile
import glob
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from loguru import logger
from datetime import datetime

logger.add("logs/enhanced_txc_parsing_{time}.log", rotation="100 MB")


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


class EnhancedRouteDataExtractor:
    def __init__(self, stops_file='data/processed/outputs/all_stops_deduplicated.csv'):
        logger.info("Loading stops for coordinate lookup...")
        stops_df = pd.read_csv(stops_file,
                                usecols=['stop_id', 'latitude', 'longitude', 'region_code', 'LA (code)'],
                                low_memory=False)

        self.stop_coords = {}
        for _, row in stops_df[stops_df['latitude'].notna()].iterrows():
            self.stop_coords[str(row['stop_id'])] = {
                'lat': row['latitude'],
                'lon': row['longitude'],
                'region': row['region_code'],
                'la': row['LA (code)']
            }

        logger.info(f"Loaded {len(self.stop_coords):,} stop coordinates")

    def parse_file(self, file_path):
        """Parse single ZIP or XML file"""
        results = []

        try:
            # Try as ZIP first
            with zipfile.ZipFile(file_path, 'r') as z:
                xml_files = [f for f in z.namelist() if f.endswith('.xml')]

                for xml_file in xml_files:
                    with z.open(xml_file) as xf:
                        file_results = self._parse_xml_content(xf, Path(file_path).name)
                        results.extend(file_results)

                return results

        except zipfile.BadZipFile:
            # Try as plain XML
            with open(file_path, 'r', encoding='utf-8') as f:
                return self._parse_xml_content(f, Path(file_path).name)

    def _parse_xml_content(self, xml_content, source_file):
        """Parse XML content and extract enhanced route data"""
        try:
            tree = ET.parse(xml_content)
            root = tree.getroot()
            ns = {'txc': 'http://www.transxchange.org.uk/'}

            # Build lookup of JourneyPatternSections
            section_lookup = {}
            sections = root.findall('.//txc:JourneyPatternSection', ns)

            for section in sections:
                section_id = section.get('id')
                links = section.findall('.//txc:JourneyPatternTimingLink', ns)

                stop_sequence = []
                for link in links:
                    from_stop = link.find('.//txc:From/txc:StopPointRef', ns)
                    to_stop = link.find('.//txc:To/txc:StopPointRef', ns)

                    if from_stop is not None:
                        stop_sequence.append(from_stop.text)
                    # Add last stop
                    if link == links[-1] and to_stop is not None:
                        stop_sequence.append(to_stop.text)

                if stop_sequence:
                    section_lookup[section_id] = stop_sequence

            # Process JourneyPatterns
            journey_patterns = root.findall('.//txc:JourneyPattern', ns)

            # Get service info
            service = root.find('.//txc:Service', ns)
            line_name = ''
            if service is not None:
                line_elem = service.find('.//txc:LineName', ns)
                if line_elem is not None:
                    line_name = line_elem.text

            results = []
            for jp in journey_patterns:
                jp_id = jp.get('id', 'unknown')

                # Get referenced section(s)
                section_refs = jp.findall('.//txc:JourneyPatternSectionRefs', ns)

                all_stops = []
                for ref_elem in section_refs:
                    ref_id = ref_elem.text
                    if ref_id in section_lookup:
                        all_stops.extend(section_lookup[ref_id])

                if not all_stops:
                    continue

                # Get stop sequences with coordinates
                stop_ids = [str(s) for s in all_stops]
                coords_list = []
                regions = set()
                las = set()
                valid_stop_sequence = []

                for sid in stop_ids:
                    if sid in self.stop_coords:
                        c = self.stop_coords[sid]
                        coords_list.append((c['lat'], c['lon']))
                        valid_stop_sequence.append(sid)
                        regions.add(c['region'])
                        if pd.notna(c['la']):
                            las.add(int(c['la']))

                # Skip if not enough valid stops
                if len(coords_list) < 2:
                    continue

                # Calculate route length
                coords = np.array(coords_list)
                total_distance = 0
                for i in range(len(coords) - 1):
                    total_distance += haversine_distance(
                        coords[i][0], coords[i][1],
                        coords[i+1][0], coords[i+1][1]
                    )

                # First and last stop coordinates for circuity
                first_stop_lat = coords[0][0]
                first_stop_lon = coords[0][1]
                last_stop_lat = coords[-1][0]
                last_stop_lon = coords[-1][1]

                # Great circle distance (straight line)
                straight_line_distance = haversine_distance(
                    first_stop_lat, first_stop_lon,
                    last_stop_lat, last_stop_lon
                )

                # Circuity index
                circuity_index = total_distance / straight_line_distance if straight_line_distance > 0.1 else 1.0

                # Count trips and extract departure times
                vehicle_journeys = root.findall(f".//txc:VehicleJourney[txc:JourneyPatternRef='{jp_id}']", ns)
                trips = len(vehicle_journeys)

                # Extract departure times for temporal analysis
                departure_times = []
                for vj in vehicle_journeys:
                    departure_time_elem = vj.find('.//txc:DepartureTime', ns)
                    if departure_time_elem is not None and departure_time_elem.text:
                        departure_times.append(departure_time_elem.text)

                # Classify time periods
                time_periods = self._classify_time_periods(departure_times)

                results.append({
                    'source_file': source_file,
                    'pattern_id': jp_id,
                    'line_name': line_name,
                    'route_length_km': round(total_distance, 2),
                    'num_stops': len(all_stops),
                    'trips_per_day': trips,
                    'num_regions': len(regions),
                    'regions_served': ','.join(sorted(regions)) if regions else '',
                    'num_las': len(las),
                    'las_served': ','.join(str(la) for la in sorted(las)) if las else '',
                    'mileage_per_day': round(total_distance * trips, 2),
                    # Enhanced data
                    'stop_sequence': '|'.join(valid_stop_sequence),  # Pipe-separated for easy parsing
                    'first_stop_lat': first_stop_lat,
                    'first_stop_lon': first_stop_lon,
                    'last_stop_lat': last_stop_lat,
                    'last_stop_lon': last_stop_lon,
                    'straight_line_km': round(straight_line_distance, 2),
                    'circuity_index': round(circuity_index, 2),
                    'departure_times': ','.join(departure_times[:10]),  # First 10 departures
                    'morning_school_trips': time_periods.get('morning_school', 0),
                    'morning_commute_trips': time_periods.get('morning_commute', 0),
                    'midday_trips': time_periods.get('midday', 0),
                    'afternoon_school_trips': time_periods.get('afternoon_school', 0),
                    'evening_commute_trips': time_periods.get('evening_commute', 0),
                    'evening_trips': time_periods.get('evening', 0),
                    'night_trips': time_periods.get('night', 0)
                })

            return results

        except Exception as e:
            logger.debug(f"Error parsing {source_file}: {e}")
            return []

    def _classify_time_periods(self, departure_times):
        """Classify departure times into TAG 2024 time periods"""
        periods = {
            'morning_school': 0,    # 07:00-09:00
            'morning_commute': 0,   # 06:30-09:30
            'midday': 0,            # 09:30-15:00
            'afternoon_school': 0,  # 15:00-17:00
            'evening_commute': 0,   # 16:30-19:00
            'evening': 0,           # 19:00-23:00
            'night': 0              # 23:00-06:30
        }

        for time_str in departure_times:
            try:
                # Parse time (format: HH:MM:SS or HH:MM)
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0

                total_minutes = hour * 60 + minute

                # Classify
                if 7*60 <= total_minutes < 9*60:
                    periods['morning_school'] += 1
                if 6*60 + 30 <= total_minutes < 9*60 + 30:
                    periods['morning_commute'] += 1
                if 9*60 + 30 <= total_minutes < 15*60:
                    periods['midday'] += 1
                if 15*60 <= total_minutes < 17*60:
                    periods['afternoon_school'] += 1
                if 16*60 + 30 <= total_minutes < 19*60:
                    periods['evening_commute'] += 1
                if 19*60 <= total_minutes < 23*60:
                    periods['evening'] += 1
                if total_minutes >= 23*60 or total_minutes < 6*60 + 30:
                    periods['night'] += 1

            except (ValueError, IndexError):
                continue

        return periods

    def parse_all(self, pattern='data/raw/regions/*/*.zip', limit=None):
        """Parse all files"""
        files = glob.glob(pattern)
        if limit:
            files = files[:limit]

        logger.info(f"Found {len(files)} files to parse")

        all_results = []
        successful = 0

        for i, file_path in enumerate(files):
            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i+1}/{len(files)} files, {len(all_results)} routes extracted")

            results = self.parse_file(file_path)
            if results:
                all_results.extend(results)
                successful += 1

        logger.success(f"Parsing complete: {len(all_results)} routes from {successful}/{len(files)} files")

        df = pd.DataFrame(all_results)
        return df


def main():
    logger.info("="*80)
    logger.info("ENHANCED ROUTE DATA EXTRACTION - FULL DATASET")
    logger.info("="*80)

    parser = EnhancedRouteDataExtractor()
    routes_df = parser.parse_all(limit=None)  # Process ALL files

    if len(routes_df) > 0:
        output_path = 'data/processed/outputs/route_metrics_enhanced.csv'
        routes_df.to_csv(output_path, index=False)
        logger.success(f"✅ Saved {len(routes_df):,} routes to {output_path}")

        # Summary
        logger.info("\n" + "="*80)
        logger.info("ENHANCED METRICS SUMMARY")
        logger.info("="*80)
        logger.info(f"Total route patterns: {len(routes_df):,}")
        logger.info(f"Avg circuity index: {routes_df['circuity_index'].mean():.2f}")
        logger.info(f"Highly circuitous (>2.0): {(routes_df['circuity_index'] > 2.0).sum():,}")
        logger.info(f"Routes with time data: {routes_df['morning_commute_trips'].gt(0).sum():,}")

    else:
        logger.error("❌ No routes extracted!")


if __name__ == '__main__':
    main()
