"""
Graph Construction for Bus Network GNN
Converts processed bus network data into PyTorch Geometric graphs
"""

import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import networkx as nx
from loguru import logger


class BusNetworkGraphBuilder:
    """
    Builds graph representations of bus networks for GNN analysis
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.stops_df = None
        self.routes_df = None
        self.demographics_df = None
        self.graph = None

    def load_processed_data(self):
        """Load processed stops, routes, and demographics"""
        logger.info("Loading processed data...")

        # Load stops
        stops_path = self.data_dir / 'processed' / 'outputs' / 'stops_processed.csv'
        self.stops_df = pd.read_csv(stops_path)
        logger.info(f"Loaded {len(self.stops_df)} stops")

        # Load routes
        routes_path = self.data_dir / 'processed' / 'outputs' / 'routes_processed.csv'
        self.routes_df = pd.read_csv(routes_path)
        logger.info(f"Loaded {len(self.routes_df)} routes")

        # Extract demographics from stops (already merged)
        demographic_cols = [col for col in self.stops_df.columns if 'Gender:' in col or 'population' in col.lower()]
        logger.info(f"Found {len(demographic_cols)} demographic features")

        return self

    def build_node_features(self) -> torch.Tensor:
        """
        Create node feature matrix
        Each node = one bus stop
        Features = demographics + stop characteristics
        """
        logger.info("Building node features...")

        features = []

        # Feature 1-3: Demographics (aggregated to LSOA)
        if 'Gender: Total; Age: All Ages; measures: Value' in self.stops_df.columns:
            features.append(self.stops_df['Gender: Total; Age: All Ages; measures: Value'].fillna(0).values)
        else:
            features.append(np.zeros(len(self.stops_df)))

        # Feature 4: IMD Score (deprivation)
        if 'imd_score' in self.stops_df.columns:
            features.append(self.stops_df['imd_score'].fillna(0).values)
        else:
            features.append(np.zeros(len(self.stops_df)))

        # Feature 5-6: Coordinates (spatial position)
        if 'latitude' in self.stops_df.columns and 'longitude' in self.stops_df.columns:
            features.append(self.stops_df['latitude'].fillna(0).values)
            features.append(self.stops_df['longitude'].fillna(0).values)
        else:
            features.append(np.zeros(len(self.stops_df)))
            features.append(np.zeros(len(self.stops_df)))

        # Feature 7: Stop accessibility (number of routes)
        # Count routes per stop
        if 'route_id' in self.routes_df.columns:
            stop_route_counts = {}
            for idx, row in self.routes_df.iterrows():
                # Assume stop_id is in stops_df
                if 'stop_id' in row:
                    stop_id = row['stop_id']
                    stop_route_counts[stop_id] = stop_route_counts.get(stop_id, 0) + 1

            route_counts = self.stops_df['stop_id'].map(stop_route_counts).fillna(0).values
            features.append(route_counts)
        else:
            features.append(np.ones(len(self.stops_df)))  # Default: 1 route per stop

        # Feature 8: Has coordinates indicator
        has_coords = (self.stops_df['has_coordinates'] if 'has_coordinates' in self.stops_df.columns
                      else np.ones(len(self.stops_df))).values
        features.append(has_coords)

        # Stack all features
        node_features = np.column_stack(features)

        # Normalize features
        node_features = (node_features - node_features.mean(axis=0)) / (node_features.std(axis=0) + 1e-8)

        logger.info(f"Created node feature matrix: {node_features.shape}")

        return torch.tensor(node_features, dtype=torch.float)

    def build_edges_from_routes(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Create edges connecting stops that are on the same route
        Edge features = route characteristics
        """
        logger.info("Building edges from routes...")

        edge_list = []
        edge_features = []

        # Create stop_id to index mapping
        stop_id_to_idx = {stop_id: idx for idx, stop_id in enumerate(self.stops_df['stop_id'])}

        # Build edges from routes
        for route_idx, route in self.routes_df.iterrows():
            # Get stops on this route
            # This is placeholder logic - adjust based on actual route structure
            route_stops = self._extract_route_stops(route)

            if len(route_stops) < 2:
                continue

            # Connect consecutive stops on route
            for i in range(len(route_stops) - 1):
                src_stop = route_stops[i]
                dst_stop = route_stops[i + 1]

                # Get indices
                if src_stop in stop_id_to_idx and dst_stop in stop_id_to_idx:
                    src_idx = stop_id_to_idx[src_stop]
                    dst_idx = stop_id_to_idx[dst_stop]

                    edge_list.append([src_idx, dst_idx])
                    edge_list.append([dst_idx, src_idx])  # Undirected graph

                    # Edge features: route frequency, distance, etc.
                    edge_feature = [
                        1.0,  # Placeholder: route frequency
                        1.0,  # Placeholder: journey time
                        route_idx / len(self.routes_df)  # Route ID (normalized)
                    ]

                    edge_features.append(edge_feature)
                    edge_features.append(edge_feature)  # Same for reverse edge

        # Convert to tensors
        if len(edge_list) == 0:
            logger.warning("No edges created! Using fully connected graph")
            return self._create_fallback_edges()

        edge_index = torch.tensor(edge_list, dtype=torch.long).T
        edge_attr = torch.tensor(edge_features, dtype=torch.float)

        logger.info(f"Created {edge_index.shape[1]} edges")

        return edge_index, edge_attr

    def build_spatial_edges(self, k_neighbors: int = 5) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Create edges based on spatial proximity (k-nearest neighbors)
        Captures geographic spillover effects
        """
        logger.info(f"Building spatial edges (k={k_neighbors})...")

        if 'latitude' not in self.stops_df.columns or 'longitude' not in self.stops_df.columns:
            logger.warning("No coordinate data, skipping spatial edges")
            return torch.empty((2, 0), dtype=torch.long), torch.empty((0, 3), dtype=torch.float)

        # Get coordinates
        coords = self.stops_df[['latitude', 'longitude']].fillna(0).values

        # Build KD-tree for efficient nearest neighbor search
        from scipy.spatial import cKDTree
        tree = cKDTree(coords)

        edge_list = []
        edge_features = []

        for idx, coord in enumerate(coords):
            # Find k nearest neighbors
            distances, neighbors = tree.query(coord, k=k_neighbors + 1)

            for dist, neighbor_idx in zip(distances[1:], neighbors[1:]):  # Skip self
                edge_list.append([idx, neighbor_idx])

                # Edge feature: inverse distance (closer = stronger connection)
                edge_feature = [
                    1.0 / (dist + 0.001),  # Inverse distance
                    dist,  # Raw distance
                    0.0  # Spatial edge indicator
                ]
                edge_features.append(edge_feature)

        edge_index = torch.tensor(edge_list, dtype=torch.long).T
        edge_attr = torch.tensor(edge_features, dtype=torch.float)

        logger.info(f"Created {edge_index.shape[1]} spatial edges")

        return edge_index, edge_attr

    def build_graph(self, include_spatial: bool = True, k_neighbors: int = 5) -> Data:
        """
        Build complete PyTorch Geometric graph
        """
        logger.info("Building complete bus network graph...")

        # Build components
        node_features = self.build_node_features()
        route_edge_index, route_edge_attr = self.build_edges_from_routes()

        if include_spatial:
            spatial_edge_index, spatial_edge_attr = self.build_spatial_edges(k_neighbors)

            # Combine route and spatial edges
            edge_index = torch.cat([route_edge_index, spatial_edge_index], dim=1)
            edge_attr = torch.cat([route_edge_attr, spatial_edge_attr], dim=0)
        else:
            edge_index = route_edge_index
            edge_attr = route_edge_attr

        # Create graph
        self.graph = Data(
            x=node_features,
            edge_index=edge_index,
            edge_attr=edge_attr,
            num_nodes=len(self.stops_df)
        )

        logger.success(f"Graph built: {self.graph.num_nodes} nodes, {self.graph.num_edges} edges")

        return self.graph

    def _extract_route_stops(self, route: pd.Series) -> List[str]:
        """
        Extract stop IDs from route record
        This is a placeholder - adjust based on actual data structure
        """
        # Check if route has stop sequence
        if 'stop_sequence' in route:
            return route['stop_sequence']

        # Fallback: return empty list
        return []

    def _create_fallback_edges(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Create simple fallback edges if route data is incomplete
        Connects each node to next node in sequence
        """
        logger.warning("Creating fallback edge structure")

        edge_list = []
        edge_features = []

        for i in range(len(self.stops_df) - 1):
            edge_list.append([i, i + 1])
            edge_list.append([i + 1, i])
            edge_features.append([1.0, 1.0, 0.0])
            edge_features.append([1.0, 1.0, 0.0])

        edge_index = torch.tensor(edge_list, dtype=torch.long).T
        edge_attr = torch.tensor(edge_features, dtype=torch.float)

        return edge_index, edge_attr

    def save_graph(self, output_path: Path):
        """Save graph to disk"""
        torch.save(self.graph, output_path)
        logger.success(f"Graph saved to {output_path}")

    def visualize_graph_stats(self):
        """Print graph statistics"""
        if self.graph is None:
            logger.error("No graph built yet")
            return

        print("\n" + "=" * 60)
        print("BUS NETWORK GRAPH STATISTICS")
        print("=" * 60)
        print(f"Nodes (bus stops): {self.graph.num_nodes:,}")
        print(f"Edges (connections): {self.graph.num_edges:,}")
        print(f"Node features: {self.graph.x.shape[1]}")
        print(f"Edge features: {self.graph.edge_attr.shape[1]}")
        print(f"Average degree: {self.graph.num_edges / self.graph.num_nodes:.2f}")
        print("=" * 60 + "\n")


def main():
    """Test graph builder"""
    import sys
    sys.path.append(str(Path(__file__).parent.parent))

    from config.settings import DATA_DIR

    # Build graph
    builder = BusNetworkGraphBuilder(DATA_DIR)
    builder.load_processed_data()
    graph = builder.build_graph(include_spatial=True, k_neighbors=5)
    builder.visualize_graph_stats()

    # Save
    output_path = Path(__file__).parent / 'bus_network_graph.pt'
    builder.save_graph(output_path)

    logger.success("Graph construction complete!")


if __name__ == "__main__":
    main()
