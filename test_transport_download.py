#!/usr/bin/env python3
"""
Quick test of transport data downloading
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from data_pipeline.data_ingestion_01 import DynamicDataIngestionPipeline

def test_transport_download():
    print("Testing transport data download...")

    pipeline = DynamicDataIngestionPipeline()

    # Test London (limit to 2 datasets for quick test)
    print("\nTesting London region (limited to 2 datasets)...")

    # Temporarily modify config for testing
    pipeline.config['regions']['london']['max_datasets'] = 2

    result = pipeline.ingest_transport_data_for_region('london')

    print(f"\nResult: {result}")

    if result.get('success'):
        print("✅ Transport download working!")
    else:
        print("❌ Transport download failed")

    return result

if __name__ == "__main__":
    test_transport_download()