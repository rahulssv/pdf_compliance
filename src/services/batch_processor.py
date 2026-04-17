"""
Batch Processing Service with Queue Management

This module provides batch processing capabilities for handling multiple
PDF documents efficiently using Redis queue management.

Features:
- Asynchronous job processing
- Priority queue support
- Job status tracking
- Retry mechanism
- Progress monitoring
- Result aggregation
"""

import logging
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Batch processing will use in-memory queue.")

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BatchJob:
    """Represents a batch processing job"""
    job_id: str
    file_urls: List[str]
    options: Dict[str, Any]
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchJob':
        """Create from dictionary"""
        data['priority'] = JobPriority(data['priority'])
        data['status'] = JobStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['started_at'] = datetime.fromisoformat(data['started_at']) if data['started_at'] else None
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        return cls(**data)


class BatchProcessor:
    """
    Batch processing service with Redis queue management.
    
    Supports:
    - Asynchronous job processing
    - Priority queues
    - Job status tracking
    - Automatic retries
    - Progress monitoring
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_workers: int = 4,
        job_timeout: int = 3600,
        enable_redis: bool = True
    ):
        """
        Initialize batch processor.
        
        Args:
            redis_url: Redis connection URL (optional)
            max_workers: Maximum number of concurrent workers
            max_workers: Maximum concurrent processing workers
            job_timeout: Job timeout in seconds
            enable_redis: Whether to use Redis (falls back to in-memory if False)
        """
        self.max_workers = max_workers
        self.job_timeout = job_timeout
        self.use_redis = enable_redis and REDIS_AVAILABLE and redis_url
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info(f"✅ BatchProcessor initialized with Redis queue")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory queue.")
                self.use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info(f"✅ BatchProcessor initialized with in-memory queue")
        
        # In-memory fallback
        self.memory_queue: List[BatchJob] = []
        self.memory_jobs: Dict[str, BatchJob] = {}
        
        # Processing callback
        self.process_callback: Optional[Callable] = None
    
    def set_process_callback(self, callback: Callable) -> None:
        """
        Set the callback function for processing individual files.
        
        Args:
            callback: Function that takes (file_url, options) and returns result
        """
        self.process_callback = callback
    
    def submit_job(
        self,
        file_urls: List[str],
        options: Optional[Dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> str:
        """
        Submit a new batch job.
        
        Args:
            file_urls: List of file URLs to process
            options: Processing options
            priority: Job priority
            
        Returns:
            str: Job ID
        """
        job_id = str(uuid.uuid4())
        
        job = BatchJob(
            job_id=job_id,
            file_urls=file_urls,
            options=options or {},
            priority=priority,
            status=JobStatus.QUEUED,
            created_at=datetime.now()
        )
        
        if self.use_redis:
            self._redis_enqueue(job)
        else:
            self._memory_enqueue(job)
        
        logger.info(f"Job {job_id} submitted with {len(file_urls)} files (priority: {priority.name})")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dict with job status or None if not found
        """
        if self.use_redis:
            return self._redis_get_job(job_id)
        else:
            return self._memory_get_job(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or queued job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if cancelled, False otherwise
        """
        job_data = self.get_job_status(job_id)
        
        if not job_data:
            return False
        
        if job_data['status'] in [JobStatus.PENDING.value, JobStatus.QUEUED.value]:
            if self.use_redis:
                self._redis_update_job_status(job_id, JobStatus.CANCELLED)
            else:
                self._memory_update_job_status(job_id, JobStatus.CANCELLED)
            
            logger.info(f"Job {job_id} cancelled")
            return True
        
        return False
    
    def process_jobs(self, max_jobs: Optional[int] = None) -> int:
        """
        Process pending jobs from the queue.
        
        Args:
            max_jobs: Maximum number of jobs to process (None = all)
            
        Returns:
            int: Number of jobs processed
        """
        if not self.process_callback:
            raise ValueError("Process callback not set. Use set_process_callback() first.")
        
        processed = 0
        
        while max_jobs is None or processed < max_jobs:
            # Get next job
            job = self._dequeue_job()
            
            if not job:
                break
            
            # Process job
            try:
                self._process_job(job)
                processed += 1
            except Exception as e:
                logger.error(f"Error processing job {job.job_id}: {e}", exc_info=True)
                self._handle_job_failure(job, str(e))
        
        return processed
    
    def start_worker(self, daemon: bool = True) -> None:
        """
        Start a background worker to process jobs continuously.
        
        Args:
            daemon: Whether to run as daemon thread
        """
        import threading
        
        def worker():
            logger.info("Batch processor worker started")
            while True:
                try:
                    self.process_jobs(max_jobs=1)
                    time.sleep(1)  # Poll interval
                except Exception as e:
                    logger.error(f"Worker error: {e}", exc_info=True)
                    time.sleep(5)
        
        thread = threading.Thread(target=worker, daemon=daemon)
        thread.start()
        logger.info("Background worker thread started")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dict with queue statistics
        """
        if self.use_redis:
            return self._redis_get_stats()
        else:
            return self._memory_get_stats()
    
    def _process_job(self, job: BatchJob) -> None:
        """Process a single job"""
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        self._update_job(job)
        
        logger.info(f"Processing job {job.job_id} with {len(job.file_urls)} files")
        
        results = []
        total_files = len(job.file_urls)
        
        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.process_callback, url, job.options): url
                for url in job.file_urls
            }
            
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=self.job_timeout)
                    results.append({
                        'file_url': url,
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    results.append({
                        'file_url': url,
                        'success': False,
                        'error': str(e)
                    })
                
                # Update progress
                completed += 1
                job.progress = (completed / total_files) * 100
                self._update_job(job)
        
        # Mark as completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        job.progress = 100.0
        job.results = {
            'total_files': total_files,
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }
        self._update_job(job)
        
        duration = (job.completed_at - job.started_at).total_seconds()
        logger.info(f"Job {job.job_id} completed in {duration:.2f}s")
    
    def _handle_job_failure(self, job: BatchJob, error: str) -> None:
        """Handle job failure with retry logic"""
        job.error = error
        job.retry_count += 1
        
        if job.retry_count < job.max_retries:
            job.status = JobStatus.RETRY
            logger.warning(f"Job {job.job_id} failed, retry {job.retry_count}/{job.max_retries}")
            
            # Re-queue with delay
            time.sleep(2 ** job.retry_count)  # Exponential backoff
            if self.use_redis:
                self._redis_enqueue(job)
            else:
                self._memory_enqueue(job)
        else:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            logger.error(f"Job {job.job_id} failed after {job.max_retries} retries")
        
        self._update_job(job)
    
    def _dequeue_job(self) -> Optional[BatchJob]:
        """Dequeue next job based on priority"""
        if self.use_redis:
            return self._redis_dequeue()
        else:
            return self._memory_dequeue()
    
    def _update_job(self, job: BatchJob) -> None:
        """Update job in storage"""
        if self.use_redis:
            self._redis_update_job(job)
        else:
            self._memory_update_job(job)
    
    # Redis implementations
    def _redis_enqueue(self, job: BatchJob) -> None:
        """Enqueue job in Redis"""
        # Store job data
        self.redis_client.setex(
            f"job:{job.job_id}",
            86400,  # 24 hour TTL
            json.dumps(job.to_dict())
        )
        
        # Add to priority queue
        self.redis_client.zadd(
            "job_queue",
            {job.job_id: job.priority.value}
        )
    
    def _redis_dequeue(self) -> Optional[BatchJob]:
        """Dequeue highest priority job from Redis"""
        # Get highest priority job
        result = self.redis_client.zpopmax("job_queue")
        
        if not result:
            return None
        
        job_id, _ = result[0]
        job_data = self.redis_client.get(f"job:{job_id}")
        
        if not job_data:
            return None
        
        return BatchJob.from_dict(json.loads(job_data))
    
    def _redis_update_job(self, job: BatchJob) -> None:
        """Update job in Redis"""
        self.redis_client.setex(
            f"job:{job.job_id}",
            86400,
            json.dumps(job.to_dict())
        )
    
    def _redis_get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job from Redis"""
        job_data = self.redis_client.get(f"job:{job_id}")
        return json.loads(job_data) if job_data else None
    
    def _redis_update_job_status(self, job_id: str, status: JobStatus) -> None:
        """Update job status in Redis"""
        job_data = self.redis_client.get(f"job:{job_id}")
        if job_data:
            job = BatchJob.from_dict(json.loads(job_data))
            job.status = status
            self._redis_update_job(job)
    
    def _redis_get_stats(self) -> Dict[str, Any]:
        """Get queue stats from Redis"""
        return {
            'backend': 'redis',
            'queued_jobs': self.redis_client.zcard("job_queue"),
            'total_jobs': len(self.redis_client.keys("job:*"))
        }
    
    # In-memory implementations
    def _memory_enqueue(self, job: BatchJob) -> None:
        """Enqueue job in memory"""
        self.memory_queue.append(job)
        self.memory_jobs[job.job_id] = job
        # Sort by priority
        self.memory_queue.sort(key=lambda j: j.priority.value, reverse=True)
    
    def _memory_dequeue(self) -> Optional[BatchJob]:
        """Dequeue highest priority job from memory"""
        if not self.memory_queue:
            return None
        return self.memory_queue.pop(0)
    
    def _memory_update_job(self, job: BatchJob) -> None:
        """Update job in memory"""
        self.memory_jobs[job.job_id] = job
    
    def _memory_get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job from memory"""
        job = self.memory_jobs.get(job_id)
        return job.to_dict() if job else None
    
    def _memory_update_job_status(self, job_id: str, status: JobStatus) -> None:
        """Update job status in memory"""
        if job_id in self.memory_jobs:
            self.memory_jobs[job_id].status = status
    
    def _memory_get_stats(self) -> Dict[str, Any]:
        """Get queue stats from memory"""
        return {
            'backend': 'memory',
            'queued_jobs': len(self.memory_queue),
            'total_jobs': len(self.memory_jobs),
            'by_status': {
                status.value: sum(1 for j in self.memory_jobs.values() if j.status == status)
                for status in JobStatus
            }
        }


# Example usage
if __name__ == '__main__':
    # Initialize processor
    processor = BatchProcessor(
        redis_url="redis://localhost:6379/0",
        max_workers=4
    )
    
    # Define processing callback
    def process_file(file_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Example file processing function"""
        print(f"Processing {file_url}")
        time.sleep(1)  # Simulate processing
        return {'status': 'success', 'file': file_url}
    
    processor.set_process_callback(process_file)
    
    # Submit job
    job_id = processor.submit_job(
        file_urls=['file1.pdf', 'file2.pdf', 'file3.pdf'],
        options={'detect_pii': True},
        priority=JobPriority.HIGH
    )
    
    print(f"Job submitted: {job_id}")
    
    # Process jobs
    processor.process_jobs()
    
    # Check status
    status = processor.get_job_status(job_id)
    print(f"Job status: {status}")

