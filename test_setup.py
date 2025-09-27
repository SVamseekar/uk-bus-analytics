"""
Quick test script to verify everything is set up correctly
Run this before the full data ingestion
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

def test_environment():
    """Test that all dependencies are working"""
    print("🔧 Testing environment setup...")
    
    # Test imports
    try:
        import pandas as pd
        import geopandas as gpd
        import requests
        from loguru import logger
        from tenacity import retry
        print("✅ All required packages imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test .env file
    load_dotenv()
    api_key = os.getenv('BODS_API_KEY')
    if api_key and api_key != 'your_actual_bods_api_key_here':
        print("✅ BODS API key found")
    else:
        print("❌ BODS API key not set or still placeholder")
        print("   Edit your .env file with: BODS_API_KEY=your_actual_key")
        return False
    
    # Test directory structure
    expected_dirs = [
        'data_pipeline/raw/gtfs',
        'data_pipeline/raw/ons',
        'data_pipeline/raw/boundaries',
        'config',
        'utils',
        'logs'
    ]
    
    for dir_path in expected_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            return False
    
    return True

def test_api_connection():
    """Test BODS API connection"""
    print("\n🌐 Testing BODS API connection...")
    
    load_dotenv()
    api_key = os.getenv('BODS_API_KEY')
    
    try:
        headers = {
            'Accept': 'application/json'
        }
        
        # BODS uses query parameter authentication, not header authentication
        params = {
            'api_key': api_key,
            'limit': 1
        }
        
        # Test with the dataset endpoint
        response = requests.get(
            'https://data.bus-data.dft.gov.uk/api/v1/dataset/',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ BODS API connected successfully")
            print(f"   Found {data.get('count', 0)} datasets available")
            return True
        elif response.status_code == 401:
            print("❌ BODS API authentication failed - check your API key")
            return False
        else:
            print(f"❌ BODS API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ BODS API connection failed: {e}")
        return False

def test_ons_connection():
    """Test ONS API connection"""
    print("\n📊 Testing ONS connection...")
    
    try:
        # Test with ONS API
        response = requests.get(
            'https://api.beta.ons.gov.uk/v1/datasets',
            timeout=10,
            params={'limit': 1}
        )
        
        if response.status_code == 200:
            print("✅ ONS API connected successfully")
            return True
        else:
            print(f"⚠️ ONS API returned status code: {response.status_code}")
            print("   This is often OK - ONS API can be temperamental")
            return True  # Don't fail on this
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ ONS API connection issue: {e}")
        print("   This is often OK - we have direct download URLs as backup")
        return True  # Don't fail on this

if __name__ == "__main__":
    print("🚀 UK Bus Analytics - Environment Test")
    print("=" * 50)
    print("Script is running...")  # Add this to confirm execution
    
    env_ok = test_environment()
    api_ok = test_api_connection()
    ons_ok = test_ons_connection()
    
    print("\n" + "=" * 50)
    if env_ok and api_ok:
        print("🎉 All tests passed! Ready to run data ingestion")
        print("\nNext steps:")
        print("1. Run: python data_pipeline/01_data_ingestion.py")
        print("2. Check logs/ directory for detailed output")
        print("3. Verify data in data_pipeline/raw/ directories")
    else:
        print("❌ Some tests failed. Fix the issues above before proceeding.")
        sys.exit(1)