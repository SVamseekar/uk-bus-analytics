"""
Service Gap Detection using Isolation Forest

Identifies LSOAs that are anomalously underserved given their:
- Population size
- Population density
- Deprivation levels (IMD)
- Elderly population
- Car ownership

Anomalies indicate service gaps where coverage doesn't match demographic need.

Author: Week 4 ML Models
Date: November 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ServiceGapDetector:
    """
    Detect underserved areas using anomaly detection

    Uses Isolation Forest to identify LSOAs where service coverage
    is unusually low given demographic characteristics.
    """

    def __init__(self, contamination=0.15):
        """
        Initialize anomaly detector

        Args:
            contamination: Expected proportion of anomalies (default 15%)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )
        self.scaler = StandardScaler()
        self.feature_names = []

    def prepare_features(self, lsoa_metrics):
        """
        Create feature matrix for anomaly detection

        Features:
        - population, elderly_pct, car_ownership_pct (demographic need)
        - imd_score, imd_decile (deprivation - higher need if deprived)
        - stops_count, stops_per_1000 (actual service provision)
        - urban_rural_code (urban vs rural)

        Args:
            lsoa_metrics: DataFrame with LSOA-level metrics

        Returns:
            Scaled feature matrix
        """
        print("\n[1/4] Preparing features for anomaly detection...")

        # Select features
        feature_columns = [
            'total_population',
            'imd_score',
            'imd_decile',
            'car_ownership_pct',
            'stops_count',
            'stops_per_1000',
            'urban_rural_code'
        ]

        # Add elderly_pct if available
        if 'elderly_pct' in lsoa_metrics.columns:
            feature_columns.append('elderly_pct')

        # Filter to available columns
        available_features = [f for f in feature_columns if f in lsoa_metrics.columns]
        self.feature_names = available_features

        print(f"   Using {len(available_features)} features:")
        for f in available_features:
            print(f"     - {f}")

        # Extract features
        X = lsoa_metrics[available_features].copy()

        # Encode urban_rural_code if it's categorical
        if 'urban_rural_code' in X.columns:
            if X['urban_rural_code'].dtype == 'object':
                # Map common urban/rural codes to numeric
                urban_rural_map = {
                    'C1': 1,  # Urban city
                    'C2': 1,  # Urban town
                    'UN1': 2,  # Rural town/fringe
                    'R1': 3,  # Rural village
                    'R2': 3,  # Rural hamlet
                }
                X['urban_rural_code'] = X['urban_rural_code'].map(urban_rural_map)
                # Fill unmapped values with median
                X['urban_rural_code'] = X['urban_rural_code'].fillna(2)

        # Handle missing values (fill with median for numeric columns)
        for col in X.columns:
            if X[col].dtype in ['float64', 'int64']:
                X[col] = X[col].fillna(X[col].median())
            else:
                # Convert any remaining non-numeric to numeric
                X[col] = pd.to_numeric(X[col], errors='coerce').fillna(X[col].median() if X[col].notna().any() else 0)

        print(f"\n   Feature matrix: {X.shape}")
        print(f"   Missing values: {X.isnull().sum().sum()}")

        return X

    def train(self, lsoa_metrics, save_path=None):
        """
        Train anomaly detection model

        Args:
            lsoa_metrics: DataFrame with LSOA-level metrics
            save_path: Path to save model (optional)

        Returns:
            lsoa_metrics with anomaly flags added
        """
        print("\n" + "="*60)
        print("SERVICE GAP DETECTION MODEL TRAINING")
        print("="*60)

        # Prepare features
        X = self.prepare_features(lsoa_metrics)

        # Scale features (important for Isolation Forest)
        print("\n[2/4] Scaling features...")
        X_scaled = self.scaler.fit_transform(X)

        # Fit anomaly detector
        print("\n[3/4] Training Isolation Forest...")
        anomaly_labels = self.model.fit_predict(X_scaled)
        anomaly_scores = self.model.score_samples(X_scaled)

        # Add to dataframe
        lsoa_metrics = lsoa_metrics.copy()
        lsoa_metrics['is_anomaly'] = (anomaly_labels == -1)
        lsoa_metrics['anomaly_score'] = anomaly_scores

        # Classify anomaly types
        print("\n[4/4] Classifying anomaly types...")
        lsoa_metrics['anomaly_type'] = lsoa_metrics.apply(
            self._classify_anomaly, axis=1
        )

        # Summary statistics
        n_anomalies = lsoa_metrics['is_anomaly'].sum()
        n_total = len(lsoa_metrics)

        print(f"\n✓ Detected {n_anomalies:,} underserved LSOAs ({n_anomalies/n_total*100:.1f}%)")

        # Analyze anomaly types
        self._analyze_anomalies(lsoa_metrics)

        # Save model if path provided
        if save_path:
            self._save_model(save_path, lsoa_metrics)

        return lsoa_metrics

    def _classify_anomaly(self, row):
        """
        Classify type of service gap

        Args:
            row: DataFrame row

        Returns:
            Anomaly type string
        """
        if not row['is_anomaly']:
            return 'Normal Service'

        # High population + low coverage
        if row['total_population'] > 2000 and row['stops_per_1000'] < 3:
            return 'High-Population Gap'

        # High deprivation + low coverage (most critical)
        if row['imd_decile'] <= 3 and row['stops_per_1000'] < 4:
            return 'Deprived Area Gap'

        # Urban with low coverage (unexpected)
        if row['urban_rural_code'] == 1 and row['stops_per_1000'] < 3:
            return 'Urban Coverage Gap'

        # Low car ownership + low coverage (high dependency)
        if row['car_ownership_pct'] < 20 and row['stops_per_1000'] < 4:
            return 'High-Dependency Gap'

        # Elderly population + low coverage
        if 'elderly_pct' in row.index and row['elderly_pct'] > 20 and row['stops_per_1000'] < 3:
            return 'Elderly Access Gap'

        # General service gap
        return 'Other Service Gap'

    def _analyze_anomalies(self, lsoa_metrics):
        """
        Analyze and report anomaly characteristics

        Args:
            lsoa_metrics: DataFrame with anomaly classifications
        """
        print("\n" + "="*60)
        print("ANOMALY ANALYSIS")
        print("="*60)

        # Anomaly type distribution
        print("\n━━━ ANOMALY TYPES ━━━")
        anomaly_counts = lsoa_metrics[lsoa_metrics['is_anomaly']]['anomaly_type'].value_counts()
        for anomaly_type, count in anomaly_counts.items():
            pct = (count / anomaly_counts.sum()) * 100
            print(f"  {anomaly_type}: {count:,} ({pct:.1f}%)")

        # Top 10 most underserved
        print("\n━━━ TOP 10 MOST UNDERSERVED LSOAs ━━━")
        worst = lsoa_metrics[lsoa_metrics['is_anomaly']].nsmallest(10, 'anomaly_score')

        for idx, row in worst.iterrows():
            print(f"\n  {row['lsoa_code']}")
            print(f"    Anomaly type: {row['anomaly_type']}")
            print(f"    Population: {row['total_population']:,.0f}")
            print(f"    IMD Decile: {row['imd_decile']:.0f} (1=most deprived)")
            print(f"    Stops: {row['stops_count']:.0f}")
            print(f"    Coverage: {row['stops_per_1000']:.2f} stops/1000")
            print(f"    Anomaly score: {row['anomaly_score']:.3f}")

        # Statistics by anomaly type
        print("\n━━━ ANOMALY TYPE STATISTICS ━━━")
        for anomaly_type in anomaly_counts.index[:5]:  # Top 5 types
            subset = lsoa_metrics[lsoa_metrics['anomaly_type'] == anomaly_type]
            print(f"\n  {anomaly_type} ({len(subset):,} LSOAs):")
            print(f"    Avg population: {subset['total_population'].mean():,.0f}")
            print(f"    Avg IMD decile: {subset['imd_decile'].mean():.1f}")
            print(f"    Avg coverage: {subset['stops_per_1000'].mean():.2f} stops/1000")
            print(f"    Total affected population: {subset['total_population'].sum():,.0f}")

    def _save_model(self, save_path, lsoa_results):
        """
        Save trained model and results

        Args:
            save_path: Directory to save model
            lsoa_results: DataFrame with anomaly results
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model
        model_file = save_path / 'anomaly_detector.pkl'
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, model_file)
        print(f"\n✓ Saved model to: {model_file}")

        # Save anomaly results
        results_file = save_path / 'lsoa_anomalies.csv'
        lsoa_results.to_csv(results_file, index=False)
        print(f"✓ Saved anomaly results to: {results_file}")

        # Save summary statistics
        anomaly_summary = lsoa_results[lsoa_results['is_anomaly']]['anomaly_type'].value_counts()
        summary_file = save_path / 'anomaly_summary.csv'
        anomaly_summary.to_csv(summary_file, header=['count'])
        print(f"✓ Saved anomaly summary to: {summary_file}")


def main():
    """Run anomaly detection pipeline"""
    print("\n" + "="*70)
    print(" "*17 + "SERVICE GAP DETECTION MODEL")
    print(" "*22 + "Week 4 - ML Model 2")
    print("="*70)

    # Load LSOA metrics
    print("\nLoading LSOA metrics...")
    lsoa_file = Path('data/ml_ready/lsoa_metrics_for_ml.csv')

    if not lsoa_file.exists():
        print(f"❌ Error: LSOA data not found at {lsoa_file}")
        print("   Run data_pipeline/05_prepare_ml_datasets.py first")
        return

    lsoa_data = pd.read_csv(lsoa_file)
    print(f"✓ Loaded {len(lsoa_data):,} LSOAs")

    # Train anomaly detector
    detector = ServiceGapDetector(contamination=0.15)
    results = detector.train(lsoa_data, save_path='models')

    print("\n" + "="*70)
    print("✅ SERVICE GAP DETECTION COMPLETE")
    print("="*70)

    # Final summary
    n_anomalies = results['is_anomaly'].sum()
    affected_pop = results[results['is_anomaly']]['total_population'].sum()

    print(f"\nIdentified {n_anomalies:,} underserved LSOAs")
    print(f"Affected population: {affected_pop:,.0f}")
    print(f"Percentage of total: {n_anomalies/len(results)*100:.1f}%")
    print(f"\nModel artifacts saved to: models/")
    print("  - anomaly_detector.pkl")
    print("  - lsoa_anomalies.csv")
    print("  - anomaly_summary.csv")
    print("="*70)


if __name__ == '__main__':
    main()
