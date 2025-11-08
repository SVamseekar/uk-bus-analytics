"""
FAST extraction for Category C - Only extracts what's needed
Target: < 5 minutes for 206 files

Extracts:
1. Stop sequences (for C19, C22 overlap)
2. First/last coords (for C20 circuity)
3. Departure times (for C23 temporal)
"""
import xml.etree.ElementTree as ET
import pandas as pd
import zipfile
import glob
from pathlib import Path
from math import radians, sin, cos, asin, sqrt
import sys

def haversine(lat1, lon1, lat2, lon2):
    """Fast haversine"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 12742 * asin(sqrt(a))  # 2*R*asin

# Quick stop coords lookup
print("Loading stop coordinates...", flush=True)
stops = pd.read_csv('data/processed/outputs/all_stops_deduplicated.csv',
                    usecols=['stop_id', 'latitude', 'longitude'],
                    low_memory=False)
stops = stops.dropna(subset=['latitude', 'longitude'])
COORDS = dict(zip(stops['stop_id'].astype(str), zip(stops['latitude'], stops['longitude'])))
print(f"Loaded {len(COORDS):,} stop coords", flush=True)

def quick_parse(file_path):
    """Fast parse - minimal data"""
    results = []

    try:
        with zipfile.ZipFile(file_path) as z:
            for xml_file in [f for f in z.namelist() if f.endswith('.xml')]:
                with z.open(xml_file) as xf:
                    try:
                        tree = ET.parse(xf)
                        root = tree.getroot()
                        ns = {'txc': 'http://www.transxchange.org.uk/'}

                        # Get sections
                        sections = {}
                        for sec in root.findall('.//txc:JourneyPatternSection', ns):
                            sid = sec.get('id')
                            stops = []
                            for link in sec.findall('.//txc:JourneyPatternTimingLink', ns):
                                from_stop = link.find('.//txc:From/txc:StopPointRef', ns)
                                to_stop = link.find('.//txc:To/txc:StopPointRef', ns)
                                if from_stop is not None:
                                    stops.append(from_stop.text)
                                if link == sec.findall('.//txc:JourneyPatternTimingLink', ns)[-1] and to_stop is not None:
                                    stops.append(to_stop.text)
                            sections[sid] = stops

                        # Get line name once
                        line_name = ''
                        service = root.find('.//txc:Service', ns)
                        if service is not None:
                            line_elem = service.find('.//txc:LineName', ns)
                            if line_elem is not None:
                                line_name = line_elem.text or ''

                        # Process patterns
                        for jp in root.findall('.//txc:JourneyPattern', ns):
                            jp_id = jp.get('id', 'unknown')

                            # Get all stops
                            all_stops = []
                            for ref_elem in jp.findall('.//txc:JourneyPatternSectionRefs', ns):
                                if ref_elem.text in sections:
                                    all_stops.extend(sections[ref_elem.text])

                            if len(all_stops) < 2:
                                continue

                            # Get valid stop coords
                            stop_ids = [str(s) for s in all_stops if str(s) in COORDS]

                            if len(stop_ids) < 2:
                                continue

                            # First/last coords for circuity
                            first_coord = COORDS[stop_ids[0]]
                            last_coord = COORDS[stop_ids[-1]]
                            straight_km = haversine(*first_coord, *last_coord)

                            # Get departure times (sample first 20)
                            dep_times = []
                            for vj in root.findall(f".//txc:VehicleJourney[txc:JourneyPatternRef='{jp_id}']", ns)[:20]:
                                dt = vj.find('.//txc:DepartureTime', ns)
                                if dt is not None and dt.text:
                                    dep_times.append(dt.text[:5])  # HH:MM only

                            results.append({
                                'source_file': Path(file_path).name,
                                'pattern_id': jp_id,
                                'line_name': line_name,
                                'num_stops': len(all_stops),
                                'stop_sequence': '|'.join(stop_ids),  # For overlap analysis
                                'first_lat': first_coord[0],
                                'first_lon': first_coord[1],
                                'last_lat': last_coord[0],
                                'last_lon': last_coord[1],
                                'straight_line_km': round(straight_km, 2),
                                'departure_times': ','.join(dep_times) if dep_times else ''
                            })
                    except:
                        continue
    except:
        pass

    return results

# Process all files
files = glob.glob('data/raw/regions/*/*.zip')
print(f"Processing {len(files)} files...", flush=True)

all_results = []
for i, f in enumerate(files):
    all_results.extend(quick_parse(f))
    if (i+1) % 20 == 0:
        print(f"  {i+1}/{len(files)} files, {len(all_results)} routes", flush=True)

print(f"\nExtracted {len(all_results):,} routes", flush=True)

# Save
df = pd.DataFrame(all_results)
output = 'data/processed/outputs/category_c_data.csv'
df.to_csv(output, index=False)
print(f"✅ Saved to {output}", flush=True)

# Quick stats
print(f"\nQuick Stats:")
print(f"  Routes with stop sequences: {df['stop_sequence'].notna().sum():,}")
print(f"  Routes with coords: {df['first_lat'].notna().sum():,}")
print(f"  Routes with departure times: {df['departure_times'].str.len().gt(0).sum():,}")
