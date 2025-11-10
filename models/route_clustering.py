"""
Route Clustering using Sentence Transformers + HDBSCAN

Groups bus routes by semantic similarity:
- Urban frequent vs rural infrequent
- Long-distance vs short local
- Deprived area service vs affluent area service
- High-frequency trunk routes vs low-frequency feeders

Author: Week 4 ML Models
Date: November 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

try:
    from sentence_transformers import SentenceTransformer
    print("✓ sentence-transformers available")
except ImportError:
    print("⚠ sentence-transformers not installed. Install with: pip install sentence-transformers")
    SentenceTransformer = None

try:
    import hdbscan
    print("✓ hdbscan available")
except ImportError:
    print("⚠ hdbscan not installed. Install with: pip install hdbscan")
    hdbscan = None


class RouteClustering:
    """
    Cluster bus routes using semantic embeddings

    Process:
    1. Create textual descriptions of each route
    2. Generate semantic embeddings using Sentence Transformers
    3. Cluster using HDBSCAN (density-based clustering)
    4. Analyze and name clusters
    """

    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        """
        Initialize route clustering model

        Args:
            model_name: Hugging Face model for embeddings (FREE)
        """
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers required. Install: pip install sentence-transformers")
        if hdbscan is None:
            raise ImportError("hdbscan required. Install: pip install hdbscan")

        self.model = SentenceTransformer(model_name)
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=10,  # Minimum 10 routes per cluster
            min_samples=5,  # Conservative clustering
            metric='euclidean',
            cluster_selection_method='eom'
        )
        self.cluster_labels = None
        self.cluster_descriptions = {}

    def prepare_route_descriptions(self, routes_df):
        """
        Create textual descriptions of routes for embedding

        Args:
            routes_df: DataFrame with route features

        Returns:
            DataFrame with route_id and description columns
        """
        print("\n[1/4] Creating route descriptions...")

        descriptions = []

        for idx, route in routes_df.iterrows():
            # Create rich textual description
            desc = f"""
            Route {route['line_name']} operated by {route['operator']}.
            Length: {route['route_length_km']:.1f} km with {route['num_stops']} stops.
            Frequency: {route['trips_per_day']} trips per day ({route['frequency_per_hour']:.1f} buses per hour).
            Service area: {route['num_regions']} regions ({route['regions_served']}), {route['num_las']} local authorities.
            Route type: {route['length_category']}, {route['frequency_category']}.
            Daily mileage: {route['mileage_per_day']:.1f} km.
            """

            descriptions.append({
                'route_id': route['route_id'],
                'line_name': route['line_name'],
                'operator': route['operator'],
                'description': desc.strip()
            })

        desc_df = pd.DataFrame(descriptions)
        print(f"   Created {len(desc_df):,} route descriptions")

        return desc_df

    def train(self, routes_df, save_path=None):
        """
        Train clustering model on route data

        Args:
            routes_df: DataFrame with route features
            save_path: Path to save trained model (optional)

        Returns:
            routes_df with cluster labels added
        """
        print("\n" + "="*60)
        print("ROUTE CLUSTERING MODEL TRAINING")
        print("="*60)

        # Step 1: Prepare descriptions
        route_descriptions = self.prepare_route_descriptions(routes_df)

        # Step 2: Generate embeddings
        print("\n[2/4] Generating semantic embeddings...")
        print("   Using model: sentence-transformers/all-MiniLM-L6-v2")
        print(f"   Processing {len(route_descriptions):,} routes...")

        embeddings = self.model.encode(
            route_descriptions['description'].tolist(),
            show_progress_bar=True,
            batch_size=32
        )

        print(f"   Generated embeddings: {embeddings.shape}")

        # Step 3: Cluster routes
        print("\n[3/4] Clustering routes...")
        cluster_assignments = self.clusterer.fit_predict(embeddings)

        route_descriptions['cluster'] = cluster_assignments
        self.cluster_labels = cluster_assignments

        n_clusters = len(set(cluster_assignments)) - (1 if -1 in cluster_assignments else 0)
        n_noise = list(cluster_assignments).count(-1)

        print(f"   Found {n_clusters} clusters")
        print(f"   Noise points: {n_noise:,} ({n_noise/len(cluster_assignments)*100:.1f}%)")

        # Step 4: Analyze clusters
        print("\n[4/4] Analyzing clusters...")
        clustered_routes = route_descriptions.merge(
            routes_df,
            on=['route_id', 'line_name', 'operator'],
            how='left'
        )

        self._analyze_and_name_clusters(clustered_routes)

        # Save model if path provided
        if save_path:
            self._save_model(save_path, embeddings, route_descriptions)

        return clustered_routes

    def _analyze_and_name_clusters(self, clustered_routes):
        """
        Analyze cluster characteristics and assign names

        Args:
            clustered_routes: DataFrame with cluster assignments
        """
        print("\n" + "="*60)
        print("CLUSTER ANALYSIS")
        print("="*60)

        for cluster_id in sorted(clustered_routes['cluster'].unique()):
            if cluster_id == -1:
                continue  # Skip noise

            cluster_data = clustered_routes[clustered_routes['cluster'] == cluster_id]
            n_routes = len(cluster_data)

            # Compute statistics
            avg_length = cluster_data['route_length_km'].mean()
            avg_stops = cluster_data['num_stops'].mean()
            avg_frequency = cluster_data['frequency_per_hour'].mean()
            avg_trips = cluster_data['trips_per_day'].mean()
            n_operators = cluster_data['operator'].nunique()

            # Determine cluster name based on characteristics
            length_mode_val = cluster_data['length_category'].mode()
            freq_mode_val = cluster_data['frequency_category'].mode()

            cluster_name = self._name_cluster(
                avg_length, avg_frequency, avg_trips,
                length_mode_val[0] if not length_mode_val.empty else 'Unknown',
                freq_mode_val[0] if not freq_mode_val.empty else 'Unknown'
            )

            self.cluster_descriptions[cluster_id] = {
                'name': cluster_name,
                'n_routes': n_routes,
                'avg_length_km': avg_length,
                'avg_stops': avg_stops,
                'avg_frequency_per_hour': avg_frequency,
                'avg_trips_per_day': avg_trips,
                'n_operators': n_operators
            }

            print(f"\n━━━ CLUSTER {cluster_id}: {cluster_name} ━━━")
            print(f"  Routes: {n_routes:,} ({n_routes/len(clustered_routes)*100:.1f}%)")
            print(f"  Operators: {n_operators}")
            print(f"  Avg length: {avg_length:.1f} km")
            print(f"  Avg stops: {avg_stops:.0f}")
            print(f"  Avg frequency: {avg_frequency:.2f} buses/hour ({avg_trips:.0f} trips/day)")

            # Handle empty modes
            length_mode = cluster_data['length_category'].mode()
            freq_mode = cluster_data['frequency_category'].mode()

            if not length_mode.empty:
                print(f"  Most common length: {length_mode[0]}")
            if not freq_mode.empty:
                print(f"  Most common frequency: {freq_mode[0]}")

    def _name_cluster(self, avg_length, avg_frequency, avg_trips, length_mode, freq_mode):
        """
        Generate descriptive cluster name based on characteristics

        Args:
            avg_length: Average route length (km)
            avg_frequency: Average frequency (buses/hour)
            avg_trips: Average trips per day
            length_mode: Most common length category
            freq_mode: Most common frequency category

        Returns:
            Descriptive cluster name
        """
        # High frequency urban trunk routes
        if avg_frequency > 4 and avg_length < 15:
            return "High-Frequency Urban Core Routes"

        # Moderate frequency urban routes
        elif avg_frequency > 2 and avg_length < 20:
            return "Moderate-Frequency Urban Routes"

        # Long distance interurban
        elif avg_length > 30:
            return "Long-Distance Interurban Routes"

        # Rural medium distance
        elif avg_length > 15 and avg_frequency < 1:
            return "Rural Medium-Distance Routes"

        # Low frequency local
        elif avg_frequency < 1 and avg_length < 10:
            return "Low-Frequency Local Feeder Routes"

        # Medium routes
        elif 10 <= avg_length <= 20:
            if avg_frequency > 1:
                return "Suburban Connector Routes"
            else:
                return "Rural Connector Routes"

        # Short routes
        elif avg_length < 10:
            return "Short Local Circular Routes"

        # Default
        else:
            return f"Mixed Service Cluster"

    def _save_model(self, save_path, embeddings, route_descriptions):
        """
        Save trained model and artifacts

        Args:
            save_path: Directory to save model
            embeddings: Route embeddings array
            route_descriptions: DataFrame with route info
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save clusterer
        model_file = save_path / 'route_clusterer.pkl'
        joblib.dump(self.clusterer, model_file)
        print(f"\n✓ Saved clusterer to: {model_file}")

        # Save embeddings
        embeddings_file = save_path / 'route_embeddings.npy'
        np.save(embeddings_file, embeddings)
        print(f"✓ Saved embeddings to: {embeddings_file}")

        # Save cluster assignments
        clusters_file = save_path / 'route_clusters.csv'
        route_descriptions.to_csv(clusters_file, index=False)
        print(f"✓ Saved cluster assignments to: {clusters_file}")

        # Save cluster descriptions
        desc_df = pd.DataFrame.from_dict(self.cluster_descriptions, orient='index')
        desc_file = save_path / 'cluster_descriptions.csv'
        desc_df.to_csv(desc_file)
        print(f"✓ Saved cluster descriptions to: {desc_file}")


def main():
    """Run route clustering pipeline"""
    print("\n" + "="*70)
    print(" "*20 + "ROUTE CLUSTERING MODEL")
    print(" "*22 + "Week 4 - ML Model 1")
    print("="*70)

    # Load route data
    print("\nLoading route data...")
    routes_file = Path('data/ml_ready/routes_for_ml.csv')

    if not routes_file.exists():
        print(f"❌ Error: Route data not found at {routes_file}")
        print("   Run data_pipeline/05_prepare_ml_datasets.py first")
        return

    routes = pd.read_csv(routes_file)
    print(f"✓ Loaded {len(routes):,} routes")

    # Sample for faster testing (remove for full training)
    # For development: use sample
    # For production: use full dataset
    SAMPLE_SIZE = 5000  # Adjust as needed
    if len(routes) > SAMPLE_SIZE:
        print(f"\n⚠ Using sample of {SAMPLE_SIZE:,} routes for faster training")
        print(f"  (Remove sampling in main() for full dataset)")
        routes = routes.sample(n=SAMPLE_SIZE, random_state=42)

    # Train clustering model
    clusterer = RouteClustering()
    clustered_routes = clusterer.train(routes, save_path='models')

    print("\n" + "="*70)
    print("✅ ROUTE CLUSTERING COMPLETE")
    print("="*70)
    print(f"\nClustered {len(clustered_routes):,} routes into {len(clusterer.cluster_descriptions)} clusters")
    print(f"\nModel artifacts saved to: models/")
    print("  - route_clusterer.pkl")
    print("  - route_embeddings.npy")
    print("  - route_clusters.csv")
    print("  - cluster_descriptions.csv")
    print("="*70)


if __name__ == '__main__':
    main()
