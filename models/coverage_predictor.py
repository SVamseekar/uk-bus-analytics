"""
Coverage Prediction using Random Forest

Predicts expected bus stop coverage given demographic and geographic factors.
Enables:
- Understanding what drives coverage allocation
- Identifying policy vs demographic determinants
- Simulating intervention impacts

Author: Week 4 ML Models
Date: November 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


class CoveragePredictor:
    """
    Predict bus coverage using demographic features

    Helps answer:
    - What coverage SHOULD an area have given its demographics?
    - Is current coverage above/below expectation?
    - What's the impact of adding X stops to area Y?
    """

    def __init__(self, n_estimators=100, max_depth=10, random_state=42):
        """
        Initialize coverage prediction model

        Args:
            n_estimators: Number of trees in forest
            max_depth: Maximum tree depth
            random_state: Random seed for reproducibility
        """
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1  # Use all CPU cores
        )
        self.feature_names = []
        self.train_stats = {}

    def prepare_features(self, lsoa_metrics):
        """
        Create feature matrix for coverage prediction

        Features (demographic/geographic - things we DON'T control):
        - total_population
        - imd_score, imd_decile (deprivation)
        - car_ownership_pct (transport dependency)
        - elderly_pct (mobility needs)
        - urban_rural_code (geography)
        - population_density_relative

        Target: stops_per_1000 (what we DO control via policy)

        Args:
            lsoa_metrics: DataFrame with LSOA-level metrics

        Returns:
            X (features), y (target)
        """
        print("\n[1/5] Preparing features for coverage prediction...")

        # Features (independent variables - demographics/geography)
        feature_columns = [
            'total_population',
            'imd_score',
            'imd_decile',
            'car_ownership_pct',
            'urban_rural_code',
            'population_density_relative'
        ]

        # Add elderly_pct if available
        if 'elderly_pct' in lsoa_metrics.columns:
            feature_columns.append('elderly_pct')

        # Filter to available
        available_features = [f for f in feature_columns if f in lsoa_metrics.columns]
        self.feature_names = available_features

        print(f"   Features: {len(available_features)}")
        for f in available_features:
            print(f"     - {f}")

        # Target (dependent variable - service provision)
        target = 'stops_per_1000'

        if target not in lsoa_metrics.columns:
            raise ValueError(f"Target column '{target}' not found")

        # Extract X, y
        X = lsoa_metrics[available_features].copy()
        y = lsoa_metrics[target].copy()

        # Handle urban_rural_code encoding
        if 'urban_rural_code' in X.columns and X['urban_rural_code'].dtype == 'object':
            urban_rural_map = {
                'C1': 1, 'C2': 1,  # Urban
                'UN1': 2,  # Urban/rural fringe
                'R1': 3, 'R2': 3,  # Rural
            }
            X['urban_rural_code'] = X['urban_rural_code'].map(urban_rural_map).fillna(2)

        # Handle missing values
        for col in X.columns:
            if X[col].dtype in ['float64', 'int64']:
                X[col] = X[col].fillna(X[col].median())
            else:
                X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

        # Remove rows with missing target
        valid_mask = y.notna() & (y > 0)
        X = X[valid_mask]
        y = y[valid_mask]

        print(f"\n   Training samples: {len(X):,}")
        print(f"   Target range: {y.min():.2f} - {y.max():.2f} stops/1000")
        print(f"   Target mean: {y.mean():.2f}, median: {y.median():.2f}")

        return X, y

    def train(self, lsoa_metrics, save_path=None):
        """
        Train coverage prediction model with validation

        Args:
            lsoa_metrics: DataFrame with LSOA-level metrics
            save_path: Path to save model (optional)

        Returns:
            Model performance metrics
        """
        print("\n" + "="*60)
        print("COVERAGE PREDICTION MODEL TRAINING")
        print("="*60)

        # Prepare features
        X, y = self.prepare_features(lsoa_metrics)

        # Train-test split
        print("\n[2/5] Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"   Train set: {len(X_train):,} LSOAs")
        print(f"   Test set: {len(X_test):,} LSOAs")

        # Train model
        print("\n[3/5] Training Random Forest...")
        self.model.fit(X_train, y_train)
        print("   ✓ Training complete")

        # Cross-validation
        print("\n[4/5] Cross-validation (5-fold)...")
        cv_scores = cross_val_score(
            self.model, X_train, y_train,
            cv=5, scoring='r2', n_jobs=-1
        )
        print(f"   CV R² scores: {cv_scores}")
        print(f"   Mean CV R²: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})")

        # Evaluate on test set
        print("\n[5/5] Evaluating on test set...")
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        # Metrics
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

        self.train_stats = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }

        # Report results
        self._report_performance()

        # Feature importance
        self._analyze_feature_importance(X)

        # Prediction examples
        self._show_prediction_examples(X_test, y_test, y_pred_test)

        # Save model
        if save_path:
            self._save_model(save_path, lsoa_metrics, y_pred_test, X_test, y_test)

        return self.train_stats

    def _report_performance(self):
        """Report model performance metrics"""
        print("\n" + "="*60)
        print("MODEL PERFORMANCE")
        print("="*60)

        print("\n━━━ R² Score (Variance Explained) ━━━")
        print(f"  Train R²: {self.train_stats['train_r2']:.3f}")
        print(f"  Test R²:  {self.train_stats['test_r2']:.3f}")
        print(f"  CV R²:    {self.train_stats['cv_mean']:.3f} (±{self.train_stats['cv_std']:.3f})")

        overfitting = self.train_stats['train_r2'] - self.train_stats['test_r2']
        if overfitting > 0.1:
            print(f"  ⚠ Overfitting detected: {overfitting:.3f} gap")
        else:
            print(f"  ✓ Good generalization: {overfitting:.3f} gap")

        print("\n━━━ Prediction Error ━━━")
        print(f"  Train MAE: {self.train_stats['train_mae']:.2f} stops/1000")
        print(f"  Test MAE:  {self.train_stats['test_mae']:.2f} stops/1000")
        print(f"  Train RMSE: {self.train_stats['train_rmse']:.2f} stops/1000")
        print(f"  Test RMSE:  {self.train_stats['test_rmse']:.2f} stops/1000")

        print("\n━━━ Interpretation ━━━")
        print(f"  Model explains {self.train_stats['test_r2']*100:.1f}% of coverage variation")
        print(f"  Typical prediction error: ±{self.train_stats['test_mae']:.2f} stops/1000")
        print(f"  Unexplained variation: {(1-self.train_stats['test_r2'])*100:.1f}% (policy/other factors)")

    def _analyze_feature_importance(self, X):
        """Analyze and report feature importance"""
        print("\n" + "="*60)
        print("FEATURE IMPORTANCE ANALYSIS")
        print("="*60)

        importances = self.model.feature_importances_
        feature_imp = pd.DataFrame({
            'feature': X.columns,
            'importance': importances
        }).sort_values('importance', ascending=False)

        print("\n━━━ What Drives Coverage? ━━━")
        for idx, row in feature_imp.iterrows():
            print(f"  {row['feature']:30s}: {row['importance']:.3f} ({row['importance']*100:.1f}%)")

        # Interpretation
        top_feature = feature_imp.iloc[0]
        print(f"\n━━━ Key Insight ━━━")
        print(f"  Top driver: {top_feature['feature']} ({top_feature['importance']*100:.1f}%)")

        if 'urban_rural_code' in feature_imp['feature'].values:
            urban_imp = feature_imp[feature_imp['feature'] == 'urban_rural_code']['importance'].iloc[0]
            print(f"  Urban/rural effect: {urban_imp*100:.1f}% of variation")

        if 'imd_score' in feature_imp['feature'].values or 'imd_decile' in feature_imp['feature'].values:
            imd_imp = feature_imp[feature_imp['feature'].str.contains('imd')]['importance'].sum()
            print(f"  Deprivation effect: {imd_imp*100:.1f}% of variation")

    def _show_prediction_examples(self, X_test, y_test, y_pred_test):
        """Show example predictions"""
        print("\n" + "="*60)
        print("PREDICTION EXAMPLES")
        print("="*60)

        # Best predictions (low error)
        errors = np.abs(y_test - y_pred_test)
        best_idx = errors.nsmallest(3).index
        worst_idx = errors.nlargest(3).index

        print("\n━━━ Best Predictions (Model Confident) ━━━")
        for idx in best_idx:
            actual = y_test.loc[idx]
            predicted = y_pred_test[X_test.index.get_loc(idx)]
            error = abs(actual - predicted)
            print(f"  Actual: {actual:.2f}, Predicted: {predicted:.2f}, Error: {error:.2f}")

        print("\n━━━ Worst Predictions (Anomalies/Policy Effects) ━━━")
        for idx in worst_idx:
            actual = y_test.loc[idx]
            predicted = y_pred_test[X_test.index.get_loc(idx)]
            error = abs(actual - predicted)
            over_under = "OVER-served" if actual > predicted else "UNDER-served"
            print(f"  Actual: {actual:.2f}, Predicted: {predicted:.2f}, Error: {error:.2f} ({over_under})")

    def predict_intervention_impact(self, lsoa_code, new_stops_to_add, lsoa_data):
        """
        Predict coverage improvement from adding stops

        Args:
            lsoa_code: LSOA code
            new_stops_to_add: Number of stops to add
            lsoa_data: DataFrame with current LSOA metrics

        Returns:
            Dict with current, predicted, and improvement values
        """
        if lsoa_code not in lsoa_data['lsoa_code'].values:
            return {'error': f'LSOA {lsoa_code} not found'}

        lsoa = lsoa_data[lsoa_data['lsoa_code'] == lsoa_code].iloc[0]

        current_coverage = lsoa['stops_per_1000']
        current_stops = lsoa['stops_count']
        population = lsoa['total_population']

        new_stops_count = current_stops + new_stops_to_add
        new_coverage = (new_stops_count / population) * 1000
        improvement = new_coverage - current_coverage

        return {
            'lsoa_code': lsoa_code,
            'population': population,
            'current_stops': current_stops,
            'current_coverage': current_coverage,
            'new_stops': new_stops_count,
            'predicted_coverage': new_coverage,
            'improvement': improvement,
            'improvement_pct': (improvement / current_coverage) * 100 if current_coverage > 0 else 0
        }

    def _save_model(self, save_path, lsoa_data, predictions, X_test, y_test):
        """Save trained model and results"""
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save model
        model_file = save_path / 'coverage_predictor.pkl'
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names,
            'train_stats': self.train_stats
        }, model_file)
        print(f"\n✓ Saved model to: {model_file}")

        # Save predictions
        results = X_test.copy()
        results['actual_coverage'] = y_test
        results['predicted_coverage'] = predictions
        results['prediction_error'] = np.abs(y_test - predictions)
        results['over_under'] = ['over' if a > p else 'under' for a, p in zip(y_test, predictions)]

        results_file = save_path / 'coverage_predictions.csv'
        results.to_csv(results_file)
        print(f"✓ Saved predictions to: {results_file}")

        # Save feature importance
        importances = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        imp_file = save_path / 'feature_importance.csv'
        importances.to_csv(imp_file, index=False)
        print(f"✓ Saved feature importance to: {imp_file}")


def main():
    """Run coverage prediction pipeline"""
    print("\n" + "="*70)
    print(" "*18 + "COVERAGE PREDICTION MODEL")
    print(" "*22 + "Week 4 - ML Model 3")
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

    # Train predictor
    predictor = CoveragePredictor(n_estimators=100, max_depth=10)
    performance = predictor.train(lsoa_data, save_path='models')

    print("\n" + "="*70)
    print("✅ COVERAGE PREDICTION MODEL COMPLETE")
    print("="*70)

    print(f"\nModel Performance:")
    print(f"  R² Score: {performance['test_r2']:.3f}")
    print(f"  MAE: {performance['test_mae']:.2f} stops/1000")
    print(f"  RMSE: {performance['test_rmse']:.2f} stops/1000")

    print(f"\nModel artifacts saved to: models/")
    print("  - coverage_predictor.pkl")
    print("  - coverage_predictions.csv")
    print("  - feature_importance.csv")
    print("="*70)


if __name__ == '__main__':
    main()
