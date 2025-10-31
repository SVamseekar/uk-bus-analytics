"""
ML Models Training - Phase 1
============================
Train 3 machine learning models for UK Bus Analytics Platform:
1. Route Clustering (Sentence Transformers + HDBSCAN)
2. Underserved Area Detection (Isolation Forest anomaly detection)
3. Coverage Prediction (Random Forest)

Author: UK Bus Analytics Platform
Date: 2025-10-29
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
import hdbscan
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)

ANALYTICS_DIR = BASE_DIR / 'analytics' / 'outputs' / 'spatial'

print("="*70)
print("ML MODELS TRAINING - PHASE 1")
print("="*70)


# =============================================================================
# MODEL 1: Route Clustering (Sentence Transformers + HDBSCAN)
# =============================================================================

print("\n🤖 MODEL 1: Route Clustering (Sentence Transformers + HDBSCAN)")
print("-" * 70)

# Load routes data from all regions
print("Loading routes data from all regions...")
regions = ['london', 'south_east', 'south_west', 'east_england',
           'west_midlands', 'east_midlands', 'yorkshire', 'north_west', 'north_east']

routes_list = []
for region in regions:
    routes_file = DATA_DIR / 'processed' / 'regions' / region / 'routes_processed.csv'
    if routes_file.exists():
        df = pd.read_csv(routes_file)
        df['region'] = region
        routes_list.append(df)

routes_df = pd.concat(routes_list, ignore_index=True)
print(f"  ✓ Loaded {len(routes_df):,} routes from {len(regions)} regions")

# Create route descriptions for embedding
print("Creating route descriptions...")
routes_df['description'] = routes_df.apply(
    lambda r: f"Route {r['route_id']} in {r['region']}. {r['route_description'][:200] if pd.notna(r['route_description']) else 'Bus route'}",
    axis=1
)

# Generate embeddings using Sentence Transformers
print("Generating route embeddings (this may take a few minutes)...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embeddings = model.encode(
    routes_df['description'].tolist(),
    show_progress_bar=True,
    batch_size=32,
    convert_to_numpy=True
)
print(f"  ✓ Generated embeddings: shape {embeddings.shape}")

# Cluster routes using HDBSCAN
print("Clustering routes with HDBSCAN...")
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=5,       # At least 5 routes per cluster
    min_samples=2,
    metric='euclidean',
    cluster_selection_epsilon=0.5
)

cluster_labels = clusterer.fit_predict(embeddings)
routes_df['cluster'] = cluster_labels

# Analyze clusters
n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
n_outliers = (cluster_labels == -1).sum()

print(f"  ✓ Clustering complete:")
print(f"     - Clusters found: {n_clusters}")
print(f"     - Routes in clusters: {(cluster_labels != -1).sum():,}")
print(f"     - Outliers: {n_outliers:,}")

# Cluster statistics
if n_clusters > 0:
    cluster_stats = routes_df[routes_df['cluster'] != -1].groupby('cluster').agg({
        'route_id': 'count',
        'region': lambda x: ', '.join(x.unique()[:3])
    }).rename(columns={'route_id': 'num_routes'})

    print(f"     - Average routes per cluster: {cluster_stats['num_routes'].mean():.1f}")

# Save model
model_artifacts = {
    'embeddings_model': model,
    'clusterer': clusterer,
    'embeddings': embeddings,
    'cluster_labels': cluster_labels,
    'routes_metadata': routes_df[['route_id', 'region', 'cluster']]
}

model_file = MODELS_DIR / 'route_clustering.pkl'
with open(model_file, 'wb') as f:
    pickle.dump(model_artifacts, f)

print(f"  ✅ Saved model: {model_file}")


# =============================================================================
# MODEL 2: Underserved Area Detection (Isolation Forest)
# =============================================================================

print("\n🤖 MODEL 2: Underserved Area Detection (Isolation Forest)")
print("-" * 70)

# Load LSOA metrics
print("Loading LSOA metrics...")
lsoa_file = ANALYTICS_DIR / 'lsoa_metrics.csv'
lsoa_df = pd.read_csv(lsoa_file)
print(f"  ✓ Loaded {len(lsoa_df):,} LSOAs")

# Select features for anomaly detection
features = [
    'stops_per_capita',
    'routes_per_capita',
    'imd_score',
    'unemployment_rate',
    'elderly_pct',
    'car_ownership_rate'
]

X = lsoa_df[features].fillna(0)

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Isolation Forest
print("Training Isolation Forest anomaly detector...")
iso_forest = IsolationForest(
    contamination=0.10,  # Expect 10% anomalies (underserved areas)
    random_state=42,
    n_estimators=100
)

anomaly_labels = iso_forest.fit_predict(X_scaled)
anomaly_scores = iso_forest.score_samples(X_scaled)

lsoa_df['anomaly_label'] = anomaly_labels  # -1 = anomaly, 1 = normal
lsoa_df['anomaly_score'] = anomaly_scores

n_anomalies = (anomaly_labels == -1).sum()

print(f"  ✓ Training complete:")
print(f"     - Anomalies detected: {n_anomalies:,} ({n_anomalies/len(lsoa_df)*100:.1f}%)")
print(f"     - Normal areas: {(anomaly_labels == 1).sum():,}")

# Analyze underserved characteristics
underserved = lsoa_df[lsoa_df['anomaly_label'] == -1]
print(f"  📊 Underserved area characteristics:")
print(f"     - Avg coverage score: {underserved['coverage_score'].mean():.2f} vs {lsoa_df['coverage_score'].mean():.2f} overall")
print(f"     - Avg IMD score: {underserved['imd_score'].mean():.2f} vs {lsoa_df['imd_score'].mean():.2f} overall")
print(f"     - Avg stops per capita: {underserved['stops_per_capita'].mean():.2f} vs {lsoa_df['stops_per_capita'].mean():.2f} overall")

# Save model
model_artifacts = {
    'model': iso_forest,
    'scaler': scaler,
    'features': features,
    'lsoa_results': lsoa_df[['lsoa_code', 'anomaly_label', 'anomaly_score']]
}

model_file = MODELS_DIR / 'anomaly_detector.pkl'
with open(model_file, 'wb') as f:
    pickle.dump(model_artifacts, f)

print(f"  ✅ Saved model: {model_file}")


# =============================================================================
# MODEL 3: Coverage Prediction (Random Forest)
# =============================================================================

print("\n🤖 MODEL 3: Coverage Score Predictor (Random Forest)")
print("-" * 70)

# Prepare data for supervised learning
print("Preparing training data...")

# Features (demographics + geography)
feature_cols = [
    'population',
    'imd_score',
    'imd_decile',
    'unemployment_rate',
    'elderly_pct',
    'youth_pct',
    'car_ownership_rate',
    'bus_stops_count'
]

# Target: coverage score
target = 'coverage_score'

X = lsoa_df[feature_cols].fillna(0)
y = lsoa_df[target]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"  ✓ Training set: {len(X_train):,} samples")
print(f"  ✓ Test set: {len(X_test):,} samples")

# Train Random Forest
print("Training Random Forest regressor...")
rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=10,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)

# Evaluate
train_score = rf_model.score(X_train, y_train)
test_score = rf_model.score(X_test, y_test)

print(f"  ✓ Training complete:")
print(f"     - Train R²: {train_score:.3f}")
print(f"     - Test R²: {test_score:.3f}")

# Feature importances
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"  📊 Top 3 important features:")
for idx, row in feature_importance.head(3).iterrows():
    print(f"     - {row['feature']}: {row['importance']:.3f}")

# Save model
model_artifacts = {
    'model': rf_model,
    'features': feature_cols,
    'feature_importance': feature_importance,
    'train_score': train_score,
    'test_score': test_score
}

model_file = MODELS_DIR / 'coverage_predictor.pkl'
with open(model_file, 'wb') as f:
    pickle.dump(model_artifacts, f)

print(f"  ✅ Saved model: {model_file}")


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("✅ ML MODELS TRAINING COMPLETE")
print("="*70)
print(f"\n📊 Models Summary:")
print(f"\n1. Route Clustering:")
print(f"   • Routes processed: {len(routes_df):,}")
print(f"   • Clusters identified: {n_clusters}")
print(f"   • Model file: route_clustering.pkl")
print(f"\n2. Anomaly Detection:")
print(f"   • LSOAs analyzed: {len(lsoa_df):,}")
print(f"   • Underserved areas detected: {n_anomalies:,}")
print(f"   • Model file: anomaly_detector.pkl")
print(f"\n3. Coverage Prediction:")
print(f"   • Training samples: {len(X_train):,}")
print(f"   • Test R²: {test_score:.3f}")
print(f"   • Model file: coverage_predictor.pkl")
print(f"\n📁 All models saved to: {MODELS_DIR}")
print("="*70)
