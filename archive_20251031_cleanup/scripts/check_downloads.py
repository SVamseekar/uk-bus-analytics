#!/usr/bin/env python3
"""
Check Download Status
Quick script to see what's downloaded and what's missing
"""

from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent
REPORT_FILE = PROJECT_ROOT / 'data_pipeline' / 'raw' / 'ingestion_report.json'

print("="*60)
print("UK Bus Analytics - Download Status Report")
print("="*60)

if not REPORT_FILE.exists():
    print("❌ No ingestion report found")
    print("   Run: python3 data_pipeline/01_data_ingestion.py")
    exit(1)

with open(REPORT_FILE, 'r') as f:
    report = json.load(f)

# Transport Data
print("\n📦 TRANSPORT DATA")
print("-"*60)

total_discovered = 0
total_downloaded = 0
total_failed = 0

for region, data in report['regional_breakdown'].items():
    discovered = data['datasets_discovered']
    downloaded = data['datasets_downloaded']
    failed = data['datasets_failed']

    total_discovered += discovered
    total_downloaded += downloaded
    total_failed += failed

    status = "✅" if failed == 0 else "⚠️"
    print(f"{status} {data['region_name']:25s} {downloaded}/{discovered} files")

print("-"*60)
print(f"{'TOTAL':25s} {total_downloaded}/{total_discovered} files")

if total_failed > 0:
    print(f"\n❌ {total_failed} files failed to download")
else:
    print("\n✅ All transport files downloaded successfully!")

# Demographic Data
print("\n📊 DEMOGRAPHIC DATA")
print("-"*60)

demo_dir = PROJECT_ROOT / 'data_pipeline' / 'raw' / 'demographic'
expected_datasets = {
    'age_structure.csv': 'Age Structure by LSOA',
    'population_2021.csv': 'Population 2021 Census',
    'imd_2019.csv': 'Index of Multiple Deprivation 2019',
    'unemployment_2024.csv': 'Unemployment Rate 2024',
    'schools_2024.csv': 'UK Schools Database (OPTIONAL)'
}

for filename, description in expected_datasets.items():
    file_path = demo_dir / filename
    if file_path.exists():
        size = file_path.stat().st_size
        size_mb = size / (1024 * 1024)
        if size_mb < 1:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size_mb:.1f} MB"
        print(f"✅ {description:40s} ({size_str})")
    else:
        optional = " (OPTIONAL)" if 'schools' in filename else ""
        status = "⚠️" if not optional else "ℹ️"
        print(f"{status} {description:40s} MISSING{optional}")

# Warnings & Errors
print("\n📋 ISSUES")
print("-"*60)

warnings = report.get('warnings', [])
errors = report.get('errors', [])

if not warnings and not errors:
    print("✅ No issues detected!")
else:
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  ❌ {error}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

demo_count = sum(1 for f in expected_datasets.keys() if (demo_dir / f).exists())
demo_total = len(expected_datasets)

print(f"Transport Data: {total_downloaded}/{total_discovered} files ({total_downloaded/total_discovered*100:.1f}%)")
print(f"Demographic Data: {demo_count}/{demo_total} datasets ({demo_count/demo_total*100:.1f}%)")

if total_failed == 0 and demo_count >= 4:  # 4 required, 1 optional
    print("\n✅ STATUS: READY TO PROCEED")
    print("   All required data available!")
    print("\n   Next step: python3 data_pipeline/02_data_processing.py")
elif total_failed > 0:
    print("\n⚠️ STATUS: SOME DOWNLOADS FAILED")
    print(f"   {total_failed} transport files need re-downloading")
    print("\n   Action: Re-run ingestion or check network connection")
else:
    print("\n⚠️ STATUS: MISSING OPTIONAL DATA")
    print("   Core data available, optional data missing")
    print("\n   See: MANUAL_DOWNLOAD_GUIDE.md for details")

print("="*60)
