"""
UK Bus Analytics - Geospatial Visualization Module
Creates interactive maps with multiple layers for bus stops, routes, and demographics
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import folium
from folium import plugins
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import DATA_PROCESSED, LOGS_DIR

logger.add(LOGS_DIR / "visualization_{time}.log", rotation="1 day", retention="30 days")


class GeoVisualizer:
    """
    Interactive geospatial visualization for UK bus networks
    Multi-layer maps with toggleable overlays
    """

    def __init__(self):
        """Initialize visualizer"""
        self.processed_dir = DATA_PROCESSED / 'regions'
        self.output_dir = Path('visualizations/maps')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # UK center coordinates
        self.uk_center = [54.5, -3.0]
        self.default_zoom = 6

    def load_region_data(self, region_code: str) -> Dict[str, pd.DataFrame]:
        """
        Load stops and routes data for a region
        """
        logger.info(f"Loading data for {region_code}...")

        region_dir = self.processed_dir / region_code
        data = {}

        stops_file = region_dir / 'stops_processed.csv'
        routes_file = region_dir / 'routes_processed.csv'

        if stops_file.exists():
            data['stops'] = pd.read_csv(stops_file)
            logger.info(f"  Loaded {len(data['stops'])} stops")

        if routes_file.exists():
            data['routes'] = pd.read_csv(routes_file)
            logger.info(f"  Loaded {len(data['routes'])} routes")

        return data

    def create_base_map(self, center: List[float] = None, zoom: int = None) -> folium.Map:
        """
        Create base map with multiple tile layers
        """
        center = center or self.uk_center
        zoom = zoom or self.default_zoom

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )

        # Add additional tile layers
        folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
        folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)

        return m

    def add_stops_layer(self, m: folium.Map, stops_df: pd.DataFrame, layer_name: str = 'Bus Stops'):
        """
        Add bus stops as markers to the map
        """
        logger.info(f"Adding {len(stops_df)} stops to map...")

        # Filter stops with valid coordinates
        valid_stops = stops_df[
            (stops_df['latitude'].notna()) &
            (stops_df['longitude'].notna())
        ].copy()

        if valid_stops.empty:
            logger.warning("No valid coordinates found for stops")
            return

        logger.info(f"  Valid stops with coordinates: {len(valid_stops)}")

        # Create feature group for stops
        stops_layer = folium.FeatureGroup(name=layer_name)

        # Add marker cluster for performance
        marker_cluster = plugins.MarkerCluster().add_to(stops_layer)

        # Add markers
        for idx, row in valid_stops.iterrows():
            popup_text = f"""
            <b>Stop: {row.get('stop_name', 'Unknown')}</b><br>
            Stop ID: {row.get('stop_id', 'N/A')}<br>
            Location: {row['latitude']:.4f}, {row['longitude']:.4f}
            """

            if 'OBS_VALUE_population_2021' in row and pd.notna(row['OBS_VALUE_population_2021']):
                popup_text += f"<br>Population: {row['OBS_VALUE_population_2021']:.0f}"

            if 'OBS_VALUE_unemployment_2024' in row and pd.notna(row['OBS_VALUE_unemployment_2024']):
                popup_text += f"<br>Unemployment: {row['OBS_VALUE_unemployment_2024']:.1f}%"

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                popup=folium.Popup(popup_text, max_width=250),
                color='blue',
                fill=True,
                fillColor='blue',
                fillOpacity=0.6
            ).add_to(marker_cluster)

        stops_layer.add_to(m)
        logger.success(f"Added {len(valid_stops)} stops to map")

    def add_heatmap_layer(self, m: folium.Map, stops_df: pd.DataFrame, layer_name: str = 'Stop Density'):
        """
        Add heatmap layer showing bus stop density
        """
        logger.info("Adding heatmap layer...")

        # Filter stops with valid coordinates
        valid_stops = stops_df[
            (stops_df['latitude'].notna()) &
            (stops_df['longitude'].notna())
        ].copy()

        if valid_stops.empty:
            logger.warning("No valid coordinates for heatmap")
            return

        # Prepare heat data
        heat_data = [[row['latitude'], row['longitude']] for idx, row in valid_stops.iterrows()]

        # Create heatmap
        heatmap = plugins.HeatMap(
            heat_data,
            name=layer_name,
            min_opacity=0.3,
            max_zoom=13,
            radius=15,
            blur=20,
            gradient={
                0.0: 'blue',
                0.5: 'yellow',
                1.0: 'red'
            }
        )

        heatmap.add_to(m)
        logger.success("Heatmap layer added")

    def create_regional_map(self, region_code: str) -> str:
        """
        Create comprehensive map for a specific region
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Creating map for: {region_code.upper().replace('_', ' ')}")
        logger.info(f"{'='*60}")

        # Load data
        data = self.load_region_data(region_code)

        if 'stops' not in data or data['stops'].empty:
            logger.error(f"No stops data available for {region_code}")
            return None

        stops_df = data['stops']

        # Determine map center from data
        valid_coords = stops_df[
            (stops_df['latitude'].notna()) &
            (stops_df['longitude'].notna())
        ]

        if valid_coords.empty:
            logger.warning(f"No valid coordinates for {region_code}, using UK center")
            center = self.uk_center
            zoom = 6
        else:
            center = [
                valid_coords['latitude'].mean(),
                valid_coords['longitude'].mean()
            ]
            zoom = 10

        # Create base map
        m = self.create_base_map(center=center, zoom=zoom)

        # Add layers
        self.add_stops_layer(m, stops_df, layer_name='Bus Stops')
        self.add_heatmap_layer(m, stops_df, layer_name='Stop Density')

        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)

        # Add title
        title_html = f'''
        <div style="position: fixed;
                    top: 10px; left: 50px; width: 400px; height: 60px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    padding: 10px; font-family: Arial; border-radius: 5px;">
        <h4 style="margin: 0">{region_code.upper().replace('_', ' ')} - Bus Network</h4>
        <p style="margin: 5px 0; font-size: 12px">
        Stops: {len(stops_df):,} |
        With Coordinates: {len(valid_coords):,}
        </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Save map
        output_file = self.output_dir / f'{region_code}_bus_map.html'
        m.save(str(output_file))

        logger.success(f"Map saved: {output_file}")
        return str(output_file)

    def create_national_overview_map(self) -> str:
        """
        Create national overview map with all regions
        """
        logger.info("\n" + "="*60)
        logger.info("Creating National Overview Map")
        logger.info("="*60)

        # Create base map
        m = self.create_base_map()

        all_stops = []
        total_stops = 0

        # Load and add all regions
        for region_dir in self.processed_dir.iterdir():
            if region_dir.is_dir():
                region_code = region_dir.name
                stops_file = region_dir / 'stops_processed.csv'

                if stops_file.exists():
                    try:
                        stops_df = pd.read_csv(stops_file)
                        all_stops.append(stops_df)
                        total_stops += len(stops_df)

                        logger.info(f"  Added {region_code}: {len(stops_df)} stops")
                    except Exception as e:
                        logger.error(f"  Error loading {region_code}: {e}")

        if not all_stops:
            logger.error("No regional data found for national map")
            return None

        # Combine all stops
        combined_stops = pd.concat(all_stops, ignore_index=True)

        logger.info(f"\nTotal stops across all regions: {total_stops:,}")

        # Add layers
        self.add_stops_layer(m, combined_stops, layer_name='All Bus Stops')
        self.add_heatmap_layer(m, combined_stops, layer_name='National Stop Density')

        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)

        # Add title
        valid_coords = combined_stops[
            (combined_stops['latitude'].notna()) &
            (combined_stops['longitude'].notna())
        ]

        title_html = f'''
        <div style="position: fixed;
                    top: 10px; left: 50px; width: 450px; height: 80px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    padding: 10px; font-family: Arial; border-radius: 5px;">
        <h4 style="margin: 0">UK Bus Network - National Overview</h4>
        <p style="margin: 5px 0; font-size: 12px">
        Total Stops: {total_stops:,} |
        Regions: {len(all_stops)} |
        With Coordinates: {len(valid_coords):,}
        </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Save map
        output_file = self.output_dir / 'uk_national_bus_map.html'
        m.save(str(output_file))

        logger.success(f"National map saved: {output_file}")
        return str(output_file)

    def generate_all_maps(self):
        """
        Generate maps for all regions plus national overview
        """
        logger.info("\n" + "="*60)
        logger.info("UK BUS ANALYTICS - GEOSPATIAL VISUALIZATION")
        logger.info("="*60)

        # Generate national overview
        self.create_national_overview_map()

        # Generate regional maps
        for region_dir in self.processed_dir.iterdir():
            if region_dir.is_dir():
                region_code = region_dir.name
                try:
                    self.create_regional_map(region_code)
                except Exception as e:
                    logger.error(f"Error creating map for {region_code}: {e}")
                    import traceback
                    traceback.print_exc()

        logger.success("\n" + "="*60)
        logger.success("MAP GENERATION COMPLETE")
        logger.success(f"Maps saved to: {self.output_dir}")
        logger.success("="*60)


def main():
    """Main execution function"""
    visualizer = GeoVisualizer()
    visualizer.generate_all_maps()


if __name__ == "__main__":
    main()
