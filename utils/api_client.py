"""
Robust API client for UK transport data sources
Includes retry logic and error handling based on real-world experience
"""
import requests
import time
from typing import Dict, Optional, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
import json

class UKTransportAPIClient:
    """
    API client specifically designed for UK transport data peculiarities
    Based on 8+ years of dealing with DfT, BODS, and operator APIs
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 timeout: int = 30, retry_attempts: int = 3):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        
        # Set up session headers
        headers = {
            'User-Agent': 'UK-Transport-Analytics/1.0 (Research)',
            'Accept': 'application/json',
        }
        
        # Note: BODS uses query parameter authentication, not headers
        self.session.headers.update(headers)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, 
                                     requests.exceptions.Timeout))
    )
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET request with intelligent retry logic
        Handles common issues with UK transport APIs
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add API key to params for BODS (not headers)
        if params is None:
            params = {}
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            logger.info(f"Making API request to {url}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            # Handle specific UK transport API quirks
            if response.status_code == 429:
                # Rate limited - common with BODS
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException("Rate limited")
            
            if response.status_code == 503:
                # Service unavailable - BODS maintenance
                logger.warning("Service unavailable - likely maintenance")
                raise requests.exceptions.RequestException("Service unavailable")
            
            response.raise_for_status()
            
            # Handle different response types
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return response.json()
            elif 'text/csv' in content_type:
                return {'csv_content': response.text}
            else:
                return {'content': response.content, 'content_type': content_type}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response.text[:500]}")
            raise

class BODSClient(UKTransportAPIClient):
    """
    Specialized client for Bus Open Data Service
    Handles BODS-specific authentication and endpoints
    """
    
    def get_datasets(self, dataset_type: str = 'timetables', limit: int = 10) -> Dict[str, Any]:
        """
        Get datasets from BODS
        dataset_type can be 'timetables', 'fares', or 'avl'
        """
        return self.get('dataset/', params={'limit': limit})
    
    def get_timetables_datasets(self, limit: int = 10) -> Dict[str, Any]:
        """Get timetables datasets specifically"""
        return self.get('dataset/', params={'limit': limit})
    
    def get_dataset_by_id(self, dataset_id: str) -> Dict[str, Any]:
        """Get specific dataset by ID"""
        return self.get(f'dataset/{dataset_id}/')
    
    def download_dataset_file(self, dataset_url: str, output_path: str) -> bool:
        """
        Download dataset file from BODS URL
        Returns True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading dataset from {dataset_url}")
            
            # For BODS downloads, we need to add the API key to the URL
            if '?' in dataset_url:
                download_url = f"{dataset_url}&api_key={self.api_key}"
            else:
                download_url = f"{dataset_url}?api_key={self.api_key}"
            
            response = self.session.get(download_url, timeout=300, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.success(f"Dataset downloaded to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            return False

class NomisClient(UKTransportAPIClient):
    """
    Client for NOMIS API - UK's official labour market and census statistics
    """
    
    def __init__(self):
        super().__init__('https://www.nomisweb.co.uk/api/v01', timeout=45)
    
    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata for a NOMIS dataset"""
        return self.get(f'dataset/{dataset_id}.def.sdmx.json')
    
    def get_data(self, dataset_id: str, geography: str = None, 
                 measures: List[str] = None, time: str = 'latest') -> Dict[str, Any]:
        """
        Get data from NOMIS dataset
        geography: e.g., 'TYPE297' for LSOA 2011
        measures: list of measure codes
        time: 'latest' or specific time period
        """
        params = {
            'dataset': dataset_id,
            'format': 'json',
            'time': time
        }
        
        if geography:
            params['geography'] = geography
            
        if measures:
            params['measures'] = ','.join(measures)
        
        return self.get('dataset', params=params)
    
    def get_geographies(self, geography_type: str = 'TYPE297') -> Dict[str, Any]:
        """
        Get available geographies
        TYPE297 = LSOA 2011
        TYPE499 = Countries
        """
        return self.get('geography', params={
            'geography': geography_type,
            'format': 'json'
        })

class ONSClient(UKTransportAPIClient):
    """
    Client for ONS Beta API - Official statistics
    """
    
    def __init__(self):
        super().__init__('https://api.beta.ons.gov.uk/v1', timeout=60)
    
    def get_datasets(self) -> Dict[str, Any]:
        """Get list of available datasets"""
        return self.get('datasets')
    
    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get specific dataset metadata"""
        return self.get(f'datasets/{dataset_id}')
    
    def get_dataset_editions(self, dataset_id: str) -> Dict[str, Any]:
        """Get editions for a dataset"""
        return self.get(f'datasets/{dataset_id}/editions')
    
    def get_dataset_data(self, dataset_id: str, edition: str = 'time-series') -> Dict[str, Any]:
        """Get data from a dataset edition"""
        return self.get(f'datasets/{dataset_id}/editions/{edition}/versions/1')
    
    def download_csv(self, download_url: str, output_path: str) -> bool:
        """Download CSV data from ONS"""
        try:
            logger.info(f"Downloading CSV from ONS: {download_url}")
            response = self.session.get(download_url, timeout=300, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.success(f"CSV downloaded to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download CSV: {e}")
            return False