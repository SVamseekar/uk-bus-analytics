"""
TransXChange Schedule Extractor
Extracts trip schedules, frequencies, and route geometries from TransXChange XML files

Author: UK Bus Analytics Project
Date: 2025-11-02
"""

import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TransXChangeScheduleExtractor:
    """Extract trip schedules, frequencies, and route geometries from TransXChange XML"""

    def __init__(self, xml_path: str):
        """
        Initialize extractor with XML file path

        Args:
            xml_path: Path to TransXChange XML file
        """
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()

        # Handle namespace
        self.ns = {'txc': 'http://www.transxchange.org.uk/'}

        # Extract filename and region for reference
        path = Path(xml_path)
        self.filename = path.name
        self.region = path.parts[-3] if len(path.parts) >= 3 else 'unknown'
        self.operator = path.parts[-2] if len(path.parts) >= 2 else 'unknown'

    def extract_vehicle_journeys(self) -> pd.DataFrame:
        """
        Extract all trips with departure times

        Returns:
            DataFrame with journey details
        """
        trips = []

        for service in self.root.findall('.//txc:Service', self.ns):
            # Get service code
            service_code = service.find('.//txc:ServiceCode', self.ns)
            service_code_text = service_code.text if service_code is not None else 'UNKNOWN'

            # Get line name
            line_name = service.find('.//txc:LineName', self.ns)
            line_name_text = line_name.text if line_name is not None else 'UNKNOWN'

            # Find all vehicle journeys for this service
            for journey in service.findall('.//txc:VehicleJourney', self.ns):
                try:
                    # Journey code
                    journey_code = journey.find('.//txc:PrivateCode', self.ns)
                    journey_code_text = journey_code.text if journey_code is not None else journey.find('.//txc:VehicleJourneyCode', self.ns)
                    if journey_code_text is not None and hasattr(journey_code_text, 'text'):
                        journey_code_text = journey_code_text.text

                    # Departure time
                    departure_time = journey.find('.//txc:DepartureTime', self.ns)
                    departure_time_text = departure_time.text if departure_time is not None else None

                    # Journey pattern reference
                    pattern_ref = journey.find('.//txc:JourneyPatternRef', self.ns)
                    pattern_ref_text = pattern_ref.text if pattern_ref is not None else None

                    # Operating profile (days of operation)
                    operating_profile = self._extract_operating_profile(journey)

                    if departure_time_text:
                        trip = {
                            'region': self.region,
                            'operator': self.operator,
                            'file': self.filename,
                            'service_code': service_code_text,
                            'line_name': line_name_text,
                            'journey_code': journey_code_text,
                            'pattern_ref': pattern_ref_text,
                            'departure_time': departure_time_text,
                            'operating_days': operating_profile.get('days', 'All'),
                            'start_date': operating_profile.get('start_date', None),
                            'end_date': operating_profile.get('end_date', None)
                        }
                        trips.append(trip)

                except Exception as e:
                    logger.debug(f"Error extracting journey in {self.filename}: {e}")
                    continue

        return pd.DataFrame(trips)

    def extract_route_geometry(self) -> pd.DataFrame:
        """
        Extract stop sequences and link distances

        Returns:
            DataFrame with route geometry
        """
        routes = []

        for section in self.root.findall('.//txc:JourneyPatternSection', self.ns):
            section_id = section.get('id', 'UNKNOWN')

            for link in section.findall('.//txc:JourneyPatternTimingLink', self.ns):
                try:
                    # From stop
                    from_stop_elem = link.find('.//txc:From/txc:StopPointRef', self.ns)
                    from_stop = from_stop_elem.text if from_stop_elem is not None else None

                    # To stop
                    to_stop_elem = link.find('.//txc:To/txc:StopPointRef', self.ns)
                    to_stop = to_stop_elem.text if to_stop_elem is not None else None

                    # Distance
                    distance_elem = link.find('.//txc:Distance', self.ns)
                    distance_m = int(distance_elem.text) if distance_elem is not None else None

                    # Run time
                    run_time_elem = link.find('.//txc:RunTime', self.ns)
                    run_time_min = self._parse_duration(run_time_elem)

                    if from_stop and to_stop:
                        route_link = {
                            'region': self.region,
                            'operator': self.operator,
                            'file': self.filename,
                            'section_id': section_id,
                            'from_stop': from_stop,
                            'to_stop': to_stop,
                            'distance_m': distance_m,
                            'run_time_min': run_time_min
                        }
                        routes.append(route_link)

                except Exception as e:
                    logger.debug(f"Error extracting route link in {self.filename}: {e}")
                    continue

        return pd.DataFrame(routes)

    def calculate_frequencies(self, trips_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate service frequency by hour of day

        Args:
            trips_df: DataFrame with trip data

        Returns:
            DataFrame with frequency calculations
        """
        if trips_df.empty:
            return pd.DataFrame()

        # Parse departure times to extract hour
        trips_df = trips_df.copy()
        trips_df['hour'] = trips_df['departure_time'].apply(self._extract_hour)

        # Remove invalid hours
        trips_df = trips_df[trips_df['hour'].notna()]

        if trips_df.empty:
            return pd.DataFrame()

        # Count trips per hour by service and region
        freq = trips_df.groupby(['region', 'operator', 'service_code', 'line_name', 'hour']).size().reset_index(name='trips_per_hour')

        # Calculate headway (average minutes between buses)
        freq['headway_min'] = 60 / freq['trips_per_hour']

        return freq

    def _extract_operating_profile(self, journey_elem) -> Dict[str, str]:
        """
        Extract operating profile (days of operation, date ranges)

        Args:
            journey_elem: XML element for VehicleJourney

        Returns:
            Dictionary with operating profile details
        """
        profile = {}

        # Operating profile
        op_profile = journey_elem.find('.//txc:OperatingProfile', self.ns)
        if op_profile is not None:
            # Regular days of week
            reg_days = op_profile.find('.//txc:RegularDayType', self.ns)
            if reg_days is not None:
                days_of_week = reg_days.find('.//txc:DaysOfWeek', self.ns)
                if days_of_week is not None:
                    # Extract all day elements
                    days = []
                    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                        if days_of_week.find(f'.//txc:{day}', self.ns) is not None:
                            days.append(day[:3])
                    profile['days'] = ','.join(days) if days else 'All'

            # Date range
            service_date_range = op_profile.find('.//txc:ServicedOrganisation', self.ns)
            if service_date_range is None:
                service_date_range = journey_elem.find('.//txc:OperatingPeriod', self.ns)

            if service_date_range is not None:
                start_date = service_date_range.find('.//txc:StartDate', self.ns)
                end_date = service_date_range.find('.//txc:EndDate', self.ns)

                if start_date is not None:
                    profile['start_date'] = start_date.text
                if end_date is not None:
                    profile['end_date'] = end_date.text

        return profile

    def _parse_duration(self, duration_elem) -> float:
        """
        Parse ISO 8601 duration (PT15M, PT1H30M) to minutes

        Args:
            duration_elem: XML element with duration text

        Returns:
            Duration in minutes
        """
        if duration_elem is None:
            return None

        duration_str = duration_elem.text
        if not duration_str or not duration_str.startswith('PT'):
            return None

        try:
            # Remove PT prefix
            duration_str = duration_str[2:]

            hours = 0
            minutes = 0

            # Extract hours if present
            if 'H' in duration_str:
                h_parts = duration_str.split('H')
                hours = int(h_parts[0])
                duration_str = h_parts[1] if len(h_parts) > 1 else ''

            # Extract minutes if present
            if 'M' in duration_str:
                minutes = int(duration_str.replace('M', ''))

            return hours * 60 + minutes

        except Exception as e:
            logger.debug(f"Error parsing duration '{duration_elem.text}': {e}")
            return None

    def _extract_hour(self, time_str: str) -> int:
        """
        Extract hour from time string (HH:MM:SS)

        Args:
            time_str: Time string

        Returns:
            Hour (0-23)
        """
        if not time_str:
            return None

        try:
            # Parse time string
            match = re.match(r'(\d{1,2}):(\d{2}):(\d{2})', time_str)
            if match:
                hour = int(match.group(1))
                return hour if 0 <= hour <= 23 else None
            return None
        except Exception:
            return None


def process_all_transxchange_files(input_dir: str = 'data/raw/transxchange_extracted',
                                    output_dir: str = 'data/processed/outputs') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main processing function - process all TransXChange XML files

    Args:
        input_dir: Directory containing extracted XML files
        output_dir: Directory for output CSV files

    Returns:
        Tuple of (trips_df, routes_df, frequencies_df)
    """
    logger.info("Starting TransXChange file processing...")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Find all XML files
    xml_files = list(Path(input_dir).rglob('*.xml'))
    logger.info(f"Found {len(xml_files)} TransXChange XML files")

    if not xml_files:
        logger.warning("No XML files found!")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    all_trips = []
    all_routes = []
    all_frequencies = []

    # Process each file
    processed = 0
    failed = 0

    for i, xml_file in enumerate(xml_files, 1):
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{len(xml_files)} files processed...")

        try:
            extractor = TransXChangeScheduleExtractor(str(xml_file))

            # Extract trips
            trips = extractor.extract_vehicle_journeys()
            if not trips.empty:
                all_trips.append(trips)

            # Extract route geometry
            routes = extractor.extract_route_geometry()
            if not routes.empty:
                all_routes.append(routes)

            # Calculate frequencies
            if not trips.empty:
                freq = extractor.calculate_frequencies(trips)
                if not freq.empty:
                    all_frequencies.append(freq)

            processed += 1

        except Exception as e:
            logger.error(f"Failed to process {xml_file.name}: {e}")
            failed += 1
            continue

    # Combine all data
    logger.info("\nCombining data from all files...")

    trips_combined = pd.concat(all_trips, ignore_index=True) if all_trips else pd.DataFrame()
    routes_combined = pd.concat(all_routes, ignore_index=True) if all_routes else pd.DataFrame()
    freq_combined = pd.concat(all_frequencies, ignore_index=True) if all_frequencies else pd.DataFrame()

    # Save outputs
    if not trips_combined.empty:
        output_path = Path(output_dir) / 'trips_schedule.csv'
        trips_combined.to_csv(output_path, index=False)
        logger.info(f"✓ Saved trips to {output_path}")

    if not routes_combined.empty:
        output_path = Path(output_dir) / 'route_geometries.csv'
        routes_combined.to_csv(output_path, index=False)
        logger.info(f"✓ Saved route geometries to {output_path}")

    if not freq_combined.empty:
        output_path = Path(output_dir) / 'service_frequencies.csv'
        freq_combined.to_csv(output_path, index=False)
        logger.info(f"✓ Saved frequencies to {output_path}")

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("EXTRACTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Files processed: {processed}")
    logger.info(f"Files failed: {failed}")
    logger.info(f"Total trips: {len(trips_combined):,}")
    logger.info(f"Total route links: {len(routes_combined):,}")
    logger.info(f"Total frequency records: {len(freq_combined):,}")

    if not trips_combined.empty:
        logger.info(f"\nTrips by region:")
        for region, count in trips_combined.groupby('region').size().sort_values(ascending=False).items():
            logger.info(f"  {region}: {count:,} trips")

    logger.info("=" * 80)

    return trips_combined, routes_combined, freq_combined


if __name__ == '__main__':
    # Run the extraction
    trips_df, routes_df, freq_df = process_all_transxchange_files()

    # Display sample data
    if not trips_df.empty:
        print("\n" + "=" * 80)
        print("SAMPLE TRIP DATA")
        print("=" * 80)
        print(trips_df.head(10))
        print(f"\nTotal trips: {len(trips_df):,}")

    if not routes_df.empty:
        print("\n" + "=" * 80)
        print("SAMPLE ROUTE GEOMETRY")
        print("=" * 80)
        print(routes_df.head(10))
        print(f"\nTotal route links: {len(routes_df):,}")

    if not freq_df.empty:
        print("\n" + "=" * 80)
        print("SAMPLE FREQUENCY DATA")
        print("=" * 80)
        print(freq_df.head(10))
        print(f"\nTotal frequency records: {len(freq_df):,}")
