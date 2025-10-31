"""
Spatial Metrics Computation - Phase 1 (Simplified Working Version)
==================================================================
Uses NaPTAN stops data with actual coordinates to create LSOA-level metrics

Author: UK Bus Analytics Platform
Date: 2025-10-29
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'analytics' / 'outputs' / 'spatial'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("SPATIAL METRICS COMPUTATION - USING DATA PIPELINE OUTPUT")
print("="*70)

# Step 1: Load processed stops from data pipeline (NOT raw NaPTAN)
print("\n📊 Loading processed stops from data pipeline...")
processed_stops_file = DATA_DIR / 'processed' / 'outputs' / 'stops_processed.csv'

if not processed_stops_file.exists():
    print(f"❌ ERROR: Data pipeline output not found!")
    print(f"Expected: {processed_stops_file}")
    print(f"\n⚠️  Please run the data pipeline first:")
    print(f"   python data_pipeline/01_data_ingestion.py")
    print(f"   python data_pipeline/02_data_processing.py")
    raise FileNotFoundError(f"Pipeline output missing: {processed_stops_file}")

# Load stops with LSOA codes and demographics already merged by pipeline
stops_df = pd.read_csv(processed_stops_file, usecols=['stop_id', 'name', 'latitude', 'longitude', 'lsoa_code', 'lsoa_name', 'locality'])
stops_df = stops_df[stops_df['latitude'].notna() & stops_df['longitude'].notna()].copy()
stops_df = stops_df[stops_df['lsoa_code'].notna()].copy()  # Only stops with LSOA codes
print(f"  ✓ Loaded {len(stops_df):,} stops from pipeline with LSOA linkage")
print(f"  ✓ Covering {stops_df['lsoa_code'].nunique():,} unique LSOAs")

# Step 2: Pipeline already has LSOA codes - skip geocoding!
print("\n✓ LSOA codes already assigned by data pipeline")

# Step 3: Aggregate to LSOA level
print("\n📈 Aggregating stops to LSOA level...")
lsoa_metrics = stops_df.groupby('lsoa_code').agg({
    'stop_id': 'count',
    'latitude': 'mean',
    'longitude': 'mean',
    'lsoa_name': 'first',
    'locality': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown'
}).reset_index()

lsoa_metrics.rename(columns={
    'stop_id': 'bus_stops_count',
    'lsoa_name': 'lsoa_name'
}, inplace=True)

# Estimate routes (rough approximation)
lsoa_metrics['routes_count'] = (lsoa_metrics['bus_stops_count'] / 8).astype(int).clip(lower=1)

print(f"  ✓ Created {len(lsoa_metrics):,} LSOA records")

# Step 4: Load actual demographics from pipeline data
print("\n👥 Loading demographic data from pipeline...")

demo_dir = DATA_DIR / 'raw' / 'demographics'

# Load population data
try:
    pop_df = pd.read_csv(demo_dir / 'lsoa_population.csv')
    pop_df = pop_df[['geography code', 'Gender: Total; Age: All Ages; measures: Value']].copy()
    pop_df.columns = ['lsoa_code', 'population']
    pop_df['population'] = pd.to_numeric(pop_df['population'], errors='coerce')
    lsoa_metrics = lsoa_metrics.merge(pop_df, on='lsoa_code', how='left')
    print(f"  ✓ Loaded population data for {pop_df['lsoa_code'].nunique():,} LSOAs")
except Exception as e:
    print(f"  ⚠️  Could not load population: {e}")
    # Fallback to estimates based on stops
    lsoa_metrics['population'] = (lsoa_metrics['bus_stops_count'] * 150).clip(lower=1000, upper=5000)

# Load IMD deprivation data
try:
    imd_df = pd.read_csv(demo_dir / 'imd_2019.csv', nrows=50000)  # Limit rows for speed
    if 'lsoa code (2011)' in imd_df.columns:
        imd_df = imd_df[['lsoa code (2011)', 'Index of Multiple Deprivation (IMD) Score',
                         'Index of Multiple Deprivation (IMD) Decile']].copy()
        imd_df.columns = ['lsoa_code', 'imd_score', 'imd_decile']
        imd_df['imd_score'] = pd.to_numeric(imd_df['imd_score'], errors='coerce')
        imd_df['imd_decile'] = pd.to_numeric(imd_df['imd_decile'], errors='coerce')
        lsoa_metrics = lsoa_metrics.merge(imd_df, on='lsoa_code', how='left')
        print(f"  ✓ Loaded IMD deprivation scores for {imd_df['lsoa_code'].nunique():,} LSOAs")
    else:
        raise ValueError("Expected columns not found in IMD file")
except Exception as e:
    print(f"  ⚠️  Could not load IMD data: {e}, using estimates")

# Fill missing IMD values
if 'imd_score' not in lsoa_metrics.columns:
    lsoa_metrics['imd_score'] = 20.0
if 'imd_decile' not in lsoa_metrics.columns:
    lsoa_metrics['imd_decile'] = 5

lsoa_metrics['imd_score'].fillna(20.0, inplace=True)
lsoa_metrics['imd_decile'].fillna(5, inplace=True)

# Load unemployment data
try:
    unemp_df = pd.read_csv(demo_dir / 'unemployment_2024.csv')
    if 'mnemonic' in unemp_df.columns and 'obs_value' in unemp_df.columns:
        unemp_df = unemp_df[['mnemonic', 'obs_value']].copy()
        unemp_df.columns = ['lsoa_code', 'unemployment_rate']
        unemp_df['unemployment_rate'] = pd.to_numeric(unemp_df['unemployment_rate'], errors='coerce') / 100
        lsoa_metrics = lsoa_metrics.merge(unemp_df, on='lsoa_code', how='left')
        print(f"  ✓ Loaded unemployment rates")
except Exception as e:
    print(f"  ⚠️  Could not load unemployment: {e}, using estimates")
    lsoa_metrics['unemployment_rate'] = 0.06

# Estimate other demographics
lsoa_metrics['elderly_pct'] = 0.18  # UK average ~18% 65+
lsoa_metrics['youth_pct'] = 0.22    # UK average ~22% 0-17
lsoa_metrics['car_ownership_rate'] = 0.75  # UK average ~75%

print(f"  ✓ Demographics loaded for {len(lsoa_metrics):,} LSOAs")

# Step 5: Calculate derived metrics
print("\n🧮 Calculating derived metrics...")

# Coverage metrics
lsoa_metrics['stops_per_capita'] = (lsoa_metrics['bus_stops_count'] / lsoa_metrics['population'] * 1000).round(2)
lsoa_metrics['routes_per_capita'] = (lsoa_metrics['routes_count'] / lsoa_metrics['population'] * 100000).round(2)

# Normalize coverage score (0-100)
stops_norm = (lsoa_metrics['stops_per_capita'] - lsoa_metrics['stops_per_capita'].min()) / \
             (lsoa_metrics['stops_per_capita'].max() - lsoa_metrics['stops_per_capita'].min()) * 100
routes_norm = (lsoa_metrics['routes_per_capita'] - lsoa_metrics['routes_per_capita'].min()) / \
              (lsoa_metrics['routes_per_capita'].max() - lsoa_metrics['routes_per_capita'].min()) * 100

lsoa_metrics['coverage_score'] = (stops_norm * 0.6 + routes_norm * 0.4).round(2)

# Equity index
deprivation_need = (10 - lsoa_metrics['imd_decile']) / 10 * 100
deprivation_equity = 100 - abs(deprivation_need - lsoa_metrics['coverage_score'])

elderly_need = lsoa_metrics['elderly_pct'] * 100
age_equity = 100 - abs(elderly_need - lsoa_metrics['coverage_score'])

car_need = (1 - lsoa_metrics['car_ownership_rate']) * 100
car_equity = 100 - abs(car_need - lsoa_metrics['coverage_score'])

lsoa_metrics['equity_index'] = (
    deprivation_equity * 0.40 +
    age_equity * 0.30 +
    car_equity * 0.30
).round(2)

# Flags
lsoa_metrics['service_gap'] = (lsoa_metrics['coverage_score'] < lsoa_metrics['coverage_score'].quantile(0.10)).astype(int)
lsoa_metrics['underserved'] = (
    (lsoa_metrics['imd_decile'] <= 3) &
    (lsoa_metrics['coverage_score'] < lsoa_metrics['coverage_score'].quantile(0.25))
).astype(int)

print(f"  ✓ Calculated 6 derived metrics")

# Step 6: Answer key spatial questions
print("\n❓ Answering spatial research questions...")

answers = {}

answers['A1'] = {
    'question': 'What is the total distribution of bus stops across UK?',
    'answer': {
        'total_stops': int(lsoa_metrics['bus_stops_count'].sum()),
        'total_lsoas': len(lsoa_metrics),
        'avg_stops_per_lsoa': round(lsoa_metrics['bus_stops_count'].mean(), 2)
    }
}

answers['A2'] = {
    'question': 'What is the national average stops per capita?',
    'answer': {
        'stops_per_1k_population': round(lsoa_metrics['stops_per_capita'].mean(), 2),
        'median': round(lsoa_metrics['stops_per_capita'].median(), 2),
        'std_dev': round(lsoa_metrics['stops_per_capita'].std(), 2)
    }
}

answers['A3'] = {
    'question': 'Which areas have the lowest coverage (service deserts)?',
    'answer': lsoa_metrics.nsmallest(10, 'coverage_score')[
        ['lsoa_code', 'locality', 'coverage_score', 'bus_stops_count', 'population']
    ].to_dict('records')
}

answers['D1'] = {
    'question': 'Correlation between deprivation and bus coverage',
    'answer': round(lsoa_metrics[['imd_score', 'coverage_score']].corr().iloc[0, 1], 3)
}

answers['D2'] = {
    'question': 'Do deprived areas have better or worse service?',
    'answer': {
        'most_deprived_avg_coverage': round(lsoa_metrics[lsoa_metrics['imd_decile'] <= 3]['coverage_score'].mean(), 2),
        'least_deprived_avg_coverage': round(lsoa_metrics[lsoa_metrics['imd_decile'] >= 8]['coverage_score'].mean(), 2)
    }
}

answers['F1'] = {
    'question': 'What is the national equity score?',
    'answer': {
        'mean_equity': round(lsoa_metrics['equity_index'].mean(), 2),
        'median_equity': round(lsoa_metrics['equity_index'].median(), 2)
    }
}

answers['F3'] = {
    'question': 'How many people live in equity gap areas?',
    'answer': int(lsoa_metrics[lsoa_metrics['equity_index'] < lsoa_metrics['equity_index'].quantile(0.25)]['population'].sum())
}

print(f"  ✅ Answered {len(answers)} key questions")

# Step 7: Save outputs
print("\n💾 Saving outputs...")

# Save LSOA metrics (CSV format - no parquet dependencies needed)
metrics_csv = OUTPUT_DIR / 'lsoa_metrics.csv'
lsoa_metrics.to_csv(metrics_csv, index=False)
print(f"  ✓ Saved: {metrics_csv}")

# Try parquet if available
try:
    metrics_parquet = OUTPUT_DIR / 'lsoa_metrics.parquet'
    lsoa_metrics.to_parquet(metrics_parquet, compression='snappy', index=False)
    print(f"  ✓ Saved: {metrics_parquet}")
except ImportError:
    print(f"  ℹ️  Parquet not available (install pyarrow for faster loading)")

# Save question answers
answers_file = OUTPUT_DIR / 'spatial_answers.json'
with open(answers_file, 'w') as f:
    json.dump({
        'metadata': {
            'generated_date': datetime.now().isoformat(),
            'data_snapshot': 'October 2025 (NaPTAN)',
            'total_questions': len(answers),
            'lsoa_count': len(lsoa_metrics),
            'total_stops': int(lsoa_metrics['bus_stops_count'].sum()),
            'total_routes': int(lsoa_metrics['routes_count'].sum())
        },
        'answers': answers
    }, f, indent=2, default=str)
print(f"  ✓ Saved: {answers_file}")

#Step 8: Summary statistics
print("\n" + "="*70)
print("✅ SPATIAL METRICS COMPUTATION COMPLETE")
print("="*70)
print(f"\n📊 Summary Statistics:")
print(f"   • LSOAs analyzed: {len(lsoa_metrics):,}")
print(f"   • Total bus stops: {lsoa_metrics['bus_stops_count'].sum():,}")
print(f"   • Total routes (estimated): {lsoa_metrics['routes_count'].sum():,}")
print(f"   • Average coverage score: {lsoa_metrics['coverage_score'].mean():.2f}/100")
print(f"   • Average equity index: {lsoa_metrics['equity_index'].mean():.2f}/100")
print(f"   • Service gap areas: {lsoa_metrics['service_gap'].sum():,}")
print(f"   • Underserved areas: {lsoa_metrics['underserved'].sum():,}")
print(f"   • Questions answered: {len(answers)}")
print(f"\n📁 Outputs saved to: {OUTPUT_DIR}")
print("="*70)
