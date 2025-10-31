"""
Smart Pipeline Update Strategy
==============================
Only re-runs pipeline components when data actually changes

Author: UK Bus Analytics
Date: 2025-10-31
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Track last update times
STATUS_FILE = BASE_DIR / 'data' / 'pipeline_status.json'


def load_status():
    """Load pipeline status"""
    if STATUS_FILE.exists():
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_status(status):
    """Save pipeline status"""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def days_since_update(component):
    """Check days since component last ran"""
    status = load_status()
    if component not in status:
        return 999  # Never run

    last_run = datetime.fromisoformat(status[component])
    days = (datetime.now() - last_run).days
    return days


def needs_update(component, frequency_days):
    """Check if component needs updating"""
    return days_since_update(component) >= frequency_days


def run_ingestion(force=False):
    """Run data ingestion if needed"""
    component = 'data_ingestion'

    # BODS timetable data typically updates weekly
    if force or needs_update(component, frequency_days=7):
        print(f"\n{'='*70}")
        print(f"🔄 Running Data Ingestion (last run: {days_since_update(component)} days ago)")
        print(f"{'='*70}\n")

        import subprocess
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'data_pipeline' / '01_data_ingestion.py')],
            capture_output=False
        )

        if result.returncode == 0:
            status = load_status()
            status[component] = datetime.now().isoformat()
            save_status(status)
            return True
        else:
            print(f"❌ Data ingestion failed")
            return False
    else:
        print(f"✓ Data ingestion up-to-date (last run: {days_since_update(component)} days ago)")
        return False  # No update needed


def run_processing(force=False):
    """Run data processing if ingestion changed or forced"""
    component = 'data_processing'

    if force or days_since_update('data_ingestion') < days_since_update(component):
        print(f"\n{'='*70}")
        print(f"🔄 Running Data Processing")
        print(f"{'='*70}\n")

        import subprocess
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'data_pipeline' / '02_data_processing.py')],
            capture_output=False
        )

        if result.returncode == 0:
            status = load_status()
            status[component] = datetime.now().isoformat()
            save_status(status)
            return True
        else:
            print(f"❌ Data processing failed")
            return False
    else:
        print(f"✓ Data processing up-to-date")
        return False


def run_spatial_metrics(force=False):
    """Run spatial metrics if processing changed or forced"""
    component = 'spatial_metrics'

    if force or days_since_update('data_processing') < days_since_update(component):
        print(f"\n{'='*70}")
        print(f"🔄 Running Spatial Metrics Computation")
        print(f"{'='*70}\n")

        import subprocess
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'analysis' / 'spatial' / '01_compute_spatial_metrics_v2.py')],
            capture_output=False
        )

        if result.returncode == 0:
            status = load_status()
            status[component] = datetime.now().isoformat()
            save_status(status)
            return True
        else:
            print(f"❌ Spatial metrics computation failed")
            return False
    else:
        print(f"✓ Spatial metrics up-to-date")
        return False


def run_ml_training(force=False):
    """Run ML model training if spatial metrics changed or forced"""
    component = 'ml_training'

    # ML models only need retraining monthly or when data significantly changes
    if force or needs_update(component, frequency_days=30):
        print(f"\n{'='*70}")
        print(f"🔄 Training ML Models (last training: {days_since_update(component)} days ago)")
        print(f"{'='*70}\n")

        import subprocess
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'analysis' / 'spatial' / '02_train_ml_models.py')],
            capture_output=False
        )

        if result.returncode == 0:
            status = load_status()
            status[component] = datetime.now().isoformat()
            save_status(status)
            return True
        else:
            print(f"❌ ML training failed")
            return False
    else:
        print(f"✓ ML models up-to-date (last training: {days_since_update(component)} days ago)")
        return False


def smart_update(force_all=False):
    """
    Smart pipeline update - only runs what's needed

    Args:
        force_all: Force all components to run regardless of last update
    """
    print("="*70)
    print("SMART PIPELINE UPDATE")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Show current status
    print("Current Status:")
    components = ['data_ingestion', 'data_processing', 'spatial_metrics', 'ml_training']
    for comp in components:
        days = days_since_update(comp)
        status_emoji = "✅" if days < 7 else "⚠️" if days < 30 else "❌"
        print(f"  {status_emoji} {comp}: {days} days since last run")
    print()

    # Run pipeline components intelligently
    ingestion_updated = run_ingestion(force=force_all)
    processing_updated = run_processing(force=force_all or ingestion_updated)
    metrics_updated = run_spatial_metrics(force=force_all or processing_updated)
    ml_updated = run_ml_training(force=force_all or metrics_updated)

    # Summary
    print()
    print("="*70)
    print("UPDATE SUMMARY")
    print("="*70)

    updates = []
    if ingestion_updated:
        updates.append("✅ Data Ingestion")
    if processing_updated:
        updates.append("✅ Data Processing")
    if metrics_updated:
        updates.append("✅ Spatial Metrics")
    if ml_updated:
        updates.append("✅ ML Training")

    if updates:
        print("\nComponents Updated:")
        for update in updates:
            print(f"  {update}")
    else:
        print("\n✓ No updates needed - all components up-to-date!")

    print()
    print("🎯 Dashboard ready to use with latest data")
    print("="*70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Smart pipeline update')
    parser.add_argument('--force', action='store_true', help='Force all components to run')
    parser.add_argument('--component', choices=['ingestion', 'processing', 'metrics', 'ml'],
                       help='Force specific component to run')

    args = parser.parse_args()

    if args.component:
        # Force specific component
        if args.component == 'ingestion':
            run_ingestion(force=True)
        elif args.component == 'processing':
            run_processing(force=True)
        elif args.component == 'metrics':
            run_spatial_metrics(force=True)
        elif args.component == 'ml':
            run_ml_training(force=True)
    else:
        # Smart update
        smart_update(force_all=args.force)
