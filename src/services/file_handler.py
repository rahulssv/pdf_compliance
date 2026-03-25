"""File handler service for managing PDF file locators"""
import os
import requests
from urllib.parse import urlparse, unquote
from pathlib import Path
from typing import Optional, Tuple


class FileHandler:
    """Handles different types of file locators (HTTPS, file://, absolute paths)"""
    
    def __init__(self):
        self.temp_dir = "/tmp/pdf_compliance"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def get_file_path(self, file_url: str) -> Tuple[str, str]:
        """
        Convert a file locator to a local file path
        
        Args:
            file_url: File locator (HTTPS URL, file:// URL, or absolute path)
            
        Returns:
            Tuple of (local_file_path, original_filename)
            
        Raises:
            ValueError: If the locator format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        parsed = urlparse(file_url)
        
        # Handle HTTPS/HTTP URLs
        if parsed.scheme in ['http', 'https']:
            return self._download_from_url(file_url)
        
        # Handle file:// URLs
        elif parsed.scheme == 'file':
            return self._handle_file_url(file_url)
        
        # Handle absolute paths (no scheme or empty scheme)
        elif parsed.scheme == '' or len(parsed.scheme) == 1:  # Single letter = Windows drive
            return self._handle_absolute_path(file_url)
        
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    
    def _download_from_url(self, url: str) -> Tuple[str, str]:
        """Download PDF from HTTPS/HTTP URL"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Extract filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename or not filename.endswith('.pdf'):
                filename = 'downloaded.pdf'
            
            # Save to temp directory
            local_path = os.path.join(self.temp_dir, filename)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return local_path, filename
            
        except requests.RequestException as e:
            raise FileNotFoundError(f"Failed to download file from {url}: {str(e)}")
    
    def _handle_file_url(self, file_url: str) -> Tuple[str, str]:
        """Handle file:// URL format"""
        # Parse file:// URL
        parsed = urlparse(file_url)
        
        # Reconstruct the path
        if parsed.netloc:
            # file://host/path format (UNC path on Windows)
            path = f"//{parsed.netloc}{parsed.path}"
        else:
            # file:///path format
            path = unquote(parsed.path)
        
        # Handle Windows paths
        if os.name == 'nt' and path.startswith('/') and len(path) > 2 and path[2] == ':':
            path = path[1:]  # Remove leading slash for Windows absolute paths
        
        return self._handle_absolute_path(path)
    
    def _handle_absolute_path(self, path: str) -> Tuple[str, str]:
        """Handle absolute file system path"""
        # Normalize path
        path = os.path.normpath(path)
        
        # Check if file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        if not os.path.isfile(path):
            raise ValueError(f"Path is not a file: {path}")
        
        # Extract filename
        filename = os.path.basename(path)
        
        return path, filename
    
    def cleanup_temp_files(self):
        """Clean up temporary downloaded files"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")

