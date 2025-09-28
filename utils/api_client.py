"""
Robust API client for UK transport data sources
Enhanced version with better error handling and response validation
"""
import requests
import time
from typing import Dict, Optional, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
import json
from pathlib import Path

class UKTransportAPIClient:
    """
    Enhanced API client for UK transport data with improved reliability
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 timeout: int = 30, retry_attempts: int = 3):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        
        # Enhanced session headers
        headers = {
            'User-Agent': 'UK-Transport-Analytics/1.0 (Research; Python)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        self.session.headers.update(headers)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((requests.exceptions.RequestException, 
                                     requests.exceptions.Timeout))
    )
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced GET request with better error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if params is None:
            params = {}
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            logger.debug(f"Making API request to {url} with params: {list(params.keys())}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            # Enhanced error handling
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException("Rate limited")
            
            if response.status_code == 503:
                logger.warning("Service unavailable - likely maintenance")
                raise requests.exceptions.RequestException("Service unavailable")
            
            if response.status_code == 401:
                logger.error("Authentication failed - check API key")
                raise requests.exceptions.RequestException("Authentication failed")
            
            response.raise_for_status()
            
            # Enhanced response handling
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {e}")
                    logger.error(f"Response content preview: {response.text[:200]}")
                    raise
            elif 'text/csv' in content_type:
                return {'csv_content': response.text, 'content_type': content_type}
            elif 'text/plain' in content_type:
                return {'text_content': response.text, 'content_type': content_type}
            else:
                return {
                    'content': response.content, 
                    'content_type': content_type,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during API request: {e}")
            raise

class BODSClient(UKTransportAPIClient):
    """Enhanced BODS client with better dataset handling"""
    
    def get_datasets(self, dataset_type: str = 'timetables', limit: int = 10) -> Dict[str, Any]:
        """Get datasets with enhanced filtering"""
        params = {'limit': limit}
        
        # Add dataset type filtering if supported
        if dataset_type and dataset_type != 'timetables':
            params['dataFormat'] = dataset_type
            
        return self.get('dataset/', params=params)
    
    def get_dataset_by_id(self, dataset_id: str) -> Dict[str, Any]:
        """Get specific dataset with validation"""
        if not dataset_id:
            raise ValueError("Dataset ID cannot be empty")
            
        return self.get(f'dataset/{dataset_id}/')
    
    def download_dataset_file(self, dataset_url: str, output_path: str) -> bool:
        """Enhanced dataset download with validation"""
        try:
            if not dataset_url:
                logger.error("No dataset URL provided")
                return False
                
            logger.info(f"Downloading dataset from {dataset_url}")
            
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Add API key to URL
            if '?' in dataset_url:
                download_url = f"{dataset_url}&api_key={self.api_key}"
            else:
                download_url = f"{dataset_url}?api_key={self.api_key}"
            
            # Download with progress indication for large files
            response = self.session.get(download_url, timeout=300, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                logger.error("Received HTML response - likely an error page")
                return False
            
            # Get expected file size
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            # Validate download
            actual_size = Path(output_path).stat().st_size
            
            if total_size > 0 and abs(actual_size - total_size) > 1024:  # Allow 1KB difference
                logger.warning(f"Download size mismatch: expected {total_size}, got {actual_size}")
            
            if actual_size < 1000:  # Very small files are likely errors
                logger.error(f"Downloaded file too small: {actual_size} bytes")
                Path(output_path).unlink(missing_ok=True)
                return False
            
            logger.success(f"Dataset downloaded successfully: {actual_size} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            if Path(output_path).exists():
                Path(output_path).unlink(missing_ok=True)
            return False

class NomisClient(UKTransportAPIClient):
    """Enhanced NOMIS client with better parameter handling"""
    
    def __init__(self):
        super().__init__('https://www.nomisweb.co.uk/api/v01', timeout=45)
    
    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata with validation"""
        if not dataset_id:
            raise ValueError("Dataset ID cannot be empty")
            
        return self.get(f'dataset/{dataset_id}.def.sdmx.json')
    
    def get_data(self, dataset_id: str, geography: str = None, 
                 measures: List[str] = None, time: str = 'latest') -> Dict[str, Any]:
        """Enhanced data retrieval with parameter validation"""
        if not dataset_id:
            raise ValueError("Dataset ID cannot be empty")
            
        params = {
            'dataset': dataset_id,
            'format': 'json',
            'time': time
        }
        
        if geography:
            params['geography'] = geography
            
        if measures:
            if isinstance(measures, list):
                params['measures'] = ','.join(measures)
            else:
                params['measures'] = measures
        
        return self.get('dataset', params=params)
    
    def get_bulk_csv(self, dataset_id: str, geography: str = None, 
                     measures: str = None, time: str = 'latest') -> str:
        """Get data as bulk CSV"""
        url = f"https://www.nomisweb.co.uk/api/v01/dataset/{dataset_id}.bulk.csv"
        
        params = {'time': time}
        if geography:
            params['geography'] = geography
        if measures:
            params['measures'] = measures
        
        try:
            response = self.session.get(url, params=params, timeout=120)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Bulk CSV download failed: {e}")
            raise
    
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
    """Enhanced ONS client with better endpoint handling"""
    
    def __init__(self):
        super().__init__('https://api.beta.ons.gov.uk/v1', timeout=60)
    
    def get_datasets(self, limit: int = 100) -> Dict[str, Any]:
        """Get datasets with pagination support"""
        return self.get('datasets', params={'limit': limit})
    
    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Get specific dataset with validation"""
        if not dataset_id:
            raise ValueError("Dataset ID cannot be empty")
            
        return self.get(f'datasets/{dataset_id}')
    
    def get_dataset_editions(self, dataset_id: str) -> Dict[str, Any]:
        """Get editions for a dataset"""
        return self.get(f'datasets/{dataset_id}/editions')
    
    def get_dataset_data(self, dataset_id: str, edition: str = 'time-series') -> Dict[str, Any]:
        """Get data from a dataset edition"""
        return self.get(f'datasets/{dataset_id}/editions/{edition}/versions/1')
    
    def download_csv(self, download_url: str, output_path: str) -> bool:
        """Enhanced CSV download with validation"""
        try:
            if not download_url:
                logger.error("No download URL provided")
                return False
                
            logger.info(f"Downloading CSV from ONS: {download_url}")
            
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            response = self.session.get(download_url, timeout=300, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validate CSV
            file_size = Path(output_path).stat().st_size
            if file_size < 100:
                logger.error(f"Downloaded CSV too small: {file_size} bytes")
                Path(output_path).unlink(missing_ok=True)
                return False
            
            logger.success(f"CSV downloaded successfully: {file_size} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download CSV: {e}")
            if Path(output_path).exists():
                Path(output_path).unlink(missing_ok=True)
            return False