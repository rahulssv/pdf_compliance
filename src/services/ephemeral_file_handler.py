"""
Ephemeral File Handler
Zero-persistence file handling with in-memory processing
"""
import os
import logging
import requests
from io import BytesIO
from typing import Optional, Tuple, BinaryIO, Dict, Any
from contextlib import contextmanager
from urllib.parse import urlparse, unquote
from pathlib import Path

logger = logging.getLogger(__name__)


class EphemeralFileHandler:
    """
    Handles file operations with zero persistence
    All files are processed in memory and automatically cleaned up
    """
    
    def __init__(self, max_memory_mb: int = 100):
        """
        Initialize ephemeral file handler
        
        Args:
            max_memory_mb: Maximum memory to use for file buffering
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._active_buffers = []
        
        logger.info(f"✅ EphemeralFileHandler initialized (max memory: {max_memory_mb}MB)")
    
    @contextmanager
    def ephemeral_file_context(self, file_url: str):
        """
        Context manager for ephemeral file handling
        
        Usage:
            with handler.ephemeral_file_context(url) as buffer:
                # Process file in memory
                # Automatic cleanup on exit
        
        Args:
            file_url: File locator (HTTPS URL, file:// URL, or absolute path)
        
        Yields:
            BytesIO buffer containing file content
        """
        buffer = None
        filename = None
        
        try:
            # Load file into memory
            buffer, filename = self._load_to_memory(file_url)
            self._active_buffers.append(buffer)
            
            logger.info(f"📂 Loaded {filename} into memory ({buffer.getbuffer().nbytes} bytes)")
            
            yield buffer, filename
            
        finally:
            # Automatic cleanup
            if buffer:
                self._cleanup_buffer(buffer)
                logger.info(f"🗑️ Cleaned up {filename} from memory")
    
    def _load_to_memory(self, file_url: str) -> Tuple[BytesIO, str]:
        """
        Load file into memory buffer
        
        Args:
            file_url: File locator
        
        Returns:
            Tuple of (BytesIO buffer, filename)
        
        Raises:
            ValueError: If file is too large or format unsupported
            FileNotFoundError: If file doesn't exist
        """
        parsed = urlparse(file_url)
        
        # Handle HTTPS/HTTP URLs
        if parsed.scheme in ['http', 'https']:
            return self._load_from_url(file_url)
        
        # Handle file:// URLs
        elif parsed.scheme == 'file':
            return self._load_from_file_url(file_url)
        
        # Handle absolute paths
        elif parsed.scheme == '' or len(parsed.scheme) == 1:
            return self._load_from_path(file_url)
        
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    
    def _load_from_url(self, url: str) -> Tuple[BytesIO, str]:
        """Load file from HTTPS/HTTP URL"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content length
            content_length = int(response.headers.get('content-length', 0))
            if content_length > self.max_memory_bytes:
                raise ValueError(
                    f"File too large: {content_length} bytes "
                    f"(max: {self.max_memory_bytes} bytes)"
                )
            
            # Extract filename
            filename = os.path.basename(urlparse(url).path)
            if not filename or not filename.endswith('.pdf'):
                filename = 'downloaded.pdf'
            
            # Load into memory
            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                buffer.write(chunk)
            
            buffer.seek(0)
            return buffer, filename
            
        except requests.RequestException as e:
            raise FileNotFoundError(f"Failed to download file from {url}: {str(e)}")
    
    def _load_from_file_url(self, file_url: str) -> Tuple[BytesIO, str]:
        """Load file from file:// URL"""
        parsed = urlparse(file_url)
        
        # Reconstruct path
        if parsed.netloc:
            path = f"//{parsed.netloc}{parsed.path}"
        else:
            path = unquote(parsed.path)
        
        # Handle Windows paths
        if os.name == 'nt' and path.startswith('/') and len(path) > 2 and path[2] == ':':
            path = path[1:]
        
        return self._load_from_path(path)
    
    def _load_from_path(self, path: str) -> Tuple[BytesIO, str]:
        """Load file from filesystem path"""
        path = os.path.normpath(path)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        if not os.path.isfile(path):
            raise ValueError(f"Path is not a file: {path}")
        
        # Check file size
        file_size = os.path.getsize(path)
        if file_size > self.max_memory_bytes:
            raise ValueError(
                f"File too large: {file_size} bytes "
                f"(max: {self.max_memory_bytes} bytes)"
            )
        
        # Load into memory
        buffer = BytesIO()
        with open(path, 'rb') as f:
            buffer.write(f.read())
        
        buffer.seek(0)
        filename = os.path.basename(path)
        
        return buffer, filename
    
    def _cleanup_buffer(self, buffer: BytesIO):
        """Clean up memory buffer"""
        if buffer in self._active_buffers:
            self._active_buffers.remove(buffer)
        
        buffer.close()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        total_bytes = sum(
            buf.getbuffer().nbytes 
            for buf in self._active_buffers 
            if not buf.closed
        )
        
        return {
            'active_buffers': len(self._active_buffers),
            'total_bytes': total_bytes,
            'total_mb': round(total_bytes / (1024 * 1024), 2),
            'max_mb': self.max_memory_bytes / (1024 * 1024),
            'usage_percent': round((total_bytes / self.max_memory_bytes) * 100, 2)
        }
    
    def cleanup_all(self):
        """Force cleanup of all active buffers"""
        for buffer in self._active_buffers[:]:
            self._cleanup_buffer(buffer)
        
        logger.info("🗑️ All buffers cleaned up")


class MemoryAwareFileHandler(EphemeralFileHandler):
    """
    Enhanced ephemeral handler with memory monitoring and limits
    """
    
    def __init__(self, max_memory_mb: int = 100, enable_monitoring: bool = True):
        super().__init__(max_memory_mb)
        self.enable_monitoring = enable_monitoring
        self._load_count = 0
        self._total_bytes_processed = 0
    
    @contextmanager
    def ephemeral_file_context(self, file_url: str):
        """Enhanced context manager with monitoring"""
        # Check memory before loading
        if self.enable_monitoring:
            usage = self.get_memory_usage()
            if usage['usage_percent'] > 80:
                logger.warning(
                    f"⚠️ High memory usage: {usage['usage_percent']}% "
                    f"({usage['total_mb']}MB / {usage['max_mb']}MB)"
                )
        
        with super().ephemeral_file_context(file_url) as (buffer, filename):
            self._load_count += 1
            self._total_bytes_processed += buffer.getbuffer().nbytes
            yield buffer, filename
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get handler statistics"""
        usage = self.get_memory_usage()
        
        return {
            'memory_usage': usage,
            'files_processed': self._load_count,
            'total_bytes_processed': self._total_bytes_processed,
            'total_mb_processed': round(self._total_bytes_processed / (1024 * 1024), 2),
            'monitoring_enabled': self.enable_monitoring
        }

# Made with Bob
