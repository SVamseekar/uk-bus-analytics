"""
FIXED TransXChange Parser - handles actual BODS data structure
Key fix: JourneyPatternSections are defined separately, not nested in JourneyPatterns
OPTIMIZED: Vectorized distance calculations, reduced dictionary lookups
"""
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import zipfile
import glob
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from loguru import logger

logger.add("logs/txc_parsing_{time}.log", rotation="100 MB")


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km - scalar version"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def haversine_vectorized(lats1, lons1, lats2, lons2):
    """Vectorized haversine for arrays of coordinates"""
    lats1, lons1, lats2, lons2 = map(np.radians, [lats1, lons1, lats2, lons2])
    dlat = lats2 - lats1
    dlon = lons2 - lons1
    a = np.sin(dlat/2)**2 + np.cos(lats1) * np.cos(lats2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371 * c


class TransXChangeParserFixed:
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
        """Parse XML content and extract route metrics"""
        try:
            tree = ET.parse(xml_content)
            root = tree.getroot()
            ns = {'txc': 'http://www.transxchange.org.uk/'}

            # Step 1: Build lookup of JourneyPatternSections (they're defined separately!)
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

            # Step 2: Process JourneyPatterns (reference sections)
            journey_patterns = root.findall('.//txc:JourneyPattern', ns)

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

                # Fast path: filter valid stops and get coords
                stop_ids = [str(s) for s in all_stops]
                coords_list = []
                regions = set()
                las = set()

                for sid in stop_ids:
                    if sid in self.stop_coords:
                        c = self.stop_coords[sid]
                        coords_list.append((c['lat'], c['lon']))
                        regions.add(c['region'])
                        if pd.notna(c['la']):
                            las.add(int(c['la']))

                # Skip if not enough valid stops
                if len(coords_list) < 2:
                    continue

                # Vectorized distance calculation
                coords = np.array(coords_list)
                lats1 = coords[:-1, 0]
                lons1 = coords[:-1, 1]
                lats2 = coords[1:, 0]
                lons2 = coords[1:, 1]

                distances = haversine_vectorized(lats1, lons1, lats2, lons2)
                route_length = float(np.sum(distances))

                # Count trips for this pattern
                vehicle_journeys = root.findall(f".//txc:VehicleJourney[txc:JourneyPatternRef='{jp_id}']", ns)
                trips = len(vehicle_journeys)

                # Get service info
                service = root.find('.//txc:Service', ns)
                line_name = ''
                if service is not None:
                    line_elem = service.find('.//txc:LineName', ns)
                    if line_elem is not None:
                        line_name = line_elem.text

                results.append({
                    'source_file': source_file,
                    'pattern_id': jp_id,
                    'line_name': line_name,
                    'route_length_km': round(route_length, 2),
                    'num_stops': len(all_stops),
                    'trips_per_day': trips,
                    'num_regions': len(regions),
                    'regions_served': ','.join(sorted(regions)) if regions else '',
                    'num_las': len(las),
                    'las_served': ','.join(str(la) for la in sorted(las)) if las else ''
                })

            return results

        except Exception as e:
            logger.debug(f"Error parsing {source_file}: {e}")
            return []

    def parse_all(self, pattern='data/raw/regions/*/*.zip'):
        """Parse all files"""
        files = glob.glob(pattern)
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

        if len(df) > 0:
            df['mileage_per_day'] = df['route_length_km'] * df['trips_per_day']

        return df


def main():
    logger.info("="*80)
    logger.info("FIXED TRANSXCHANGE PARSER")
    logger.info("="*80)

    parser = TransXChangeParserFixed()
    routes_df = parser.parse_all()

    if len(routes_df) > 0:
        output_path = 'data/processed/outputs/route_metrics.csv'
        routes_df.to_csv(output_path, index=False)
        logger.success(f"✅ Saved {len(routes_df):,} routes to {output_path}")

        # Summary
        logger.info("\n" + "="*80)
        logger.info("SUMMARY STATISTICS")
        logger.info("="*80)
        logger.info(f"Total route patterns: {len(routes_df):,}")
        logger.info(f"Avg route length: {routes_df['route_length_km'].mean():.2f} km")
        logger.info(f"Avg stops per route: {routes_df['num_stops'].mean():.1f}")
        logger.info(f"Total daily trips: {routes_df['trips_per_day'].sum():,}")
        logger.info(f"Cross-region routes: {(routes_df['num_regions'] > 1).sum():,}")
        logger.info(f"Cross-LA routes: {(routes_df['num_las'] > 1).sum():,}")

        # Top 10 longest
        logger.info("\nTop 10 longest routes:")
        top = routes_df.nlargest(10, 'route_length_km')[['line_name', 'route_length_km', 'num_stops', 'trips_per_day']]
        for _, r in top.iterrows():
            logger.info(f"  {r['line_name']}: {r['route_length_km']:.1f} km, {r['num_stops']} stops, {r['trips_per_day']} trips/day")
    else:
        logger.error("❌ No routes extracted!")


if __name__ == '__main__':
    main()
