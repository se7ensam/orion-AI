"""
Distributed Worker for Processing Filings

Worker process that runs in Docker containers to process filings in parallel.
"""

import os
import sys
import time
import json
import signal
import logging
from pathlib import Path
from typing import Optional, Dict, List
from services.database.neo4j_connection import Neo4jConnection
from services.graph_builder.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class FilingWorker:
    """Worker that processes filings from a queue."""
    
    def __init__(self, worker_id: str, queue_dir: Path, neo4j_conn: Neo4jConnection):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique identifier for this worker
            queue_dir: Directory containing work queue files
            neo4j_conn: Neo4j connection instance
        """
        self.worker_id = worker_id
        self.queue_dir = queue_dir
        self.conn = neo4j_conn
        self.running = True
        self.processed_count = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        # Create queue directories
        self.pending_dir = queue_dir / "pending"
        self.processing_dir = queue_dir / "processing"
        self.completed_dir = queue_dir / "completed"
        self.failed_dir = queue_dir / "failed"
        
        for dir_path in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"[Worker {self.worker_id}] Received shutdown signal. Finishing current work...")
        self.running = False
    
    def _get_next_job(self) -> Optional[Path]:
        """Get the next pending job from the queue."""
        pending_jobs = sorted(self.pending_dir.glob("*.json"))
        if pending_jobs:
            job_file = pending_jobs[0]
            # Move to processing directory
            processing_file = self.processing_dir / f"{self.worker_id}_{job_file.name}"
            try:
                job_file.rename(processing_file)
                return processing_file
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] Error moving job to processing: {e}")
                return None
        return None
    
    def _mark_job_complete(self, job_file: Path, success: bool = True):
        """Mark a job as complete or failed."""
        try:
            if success:
                target_dir = self.completed_dir
            else:
                target_dir = self.failed_dir
            
            target_file = target_dir / job_file.name
            job_file.rename(target_file)
        except Exception as e:
            logger.error(f"[Worker {self.worker_id}] Error marking job complete: {e}")
    
    def _process_job(self, job_file: Path) -> bool:
        """Process a single job file."""
        try:
            # Read job data
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            filing_path = Path(job_data['filing_path'])
            
            if not filing_path.exists():
                logger.warning(f"[Worker {self.worker_id}] Filing not found: {filing_path}")
                return False
            
            logger.info(f"[Worker {self.worker_id}] Processing: {filing_path.name}")
            
            # Create graph builder
            builder = GraphBuilder(self.conn)
            
            # Process the filing
            stats = builder.process_filing(filing_path)
            
            # Update job with results
            job_data['stats'] = stats
            job_data['worker_id'] = self.worker_id
            job_data['completed_at'] = time.time()
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
            
            logger.info(f"[Worker {self.worker_id}] Completed: {filing_path.name} "
                       f"(People: {stats.get('people', 0)}, Relationships: {stats.get('relationships', 0)})")
            
            return True
            
        except Exception as e:
            logger.error(f"[Worker {self.worker_id}] Error processing job: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """Main worker loop."""
        logger.info(f"[Worker {self.worker_id}] Started. Waiting for jobs...")
        
        while self.running:
            job_file = self._get_next_job()
            
            if job_file:
                success = self._process_job(job_file)
                self._mark_job_complete(job_file, success)
                self.processed_count += 1
            else:
                # No jobs available, wait a bit
                time.sleep(1)
        
        logger.info(f"[Worker {self.worker_id}] Stopped. Processed {self.processed_count} jobs.")


def main():
    """Main entry point for worker."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker_id = os.getenv("WORKER_ID", f"worker-{os.getpid()}")
    queue_dir = Path(os.getenv("QUEUE_DIR", "/app/data/queue"))
    
    logger.info(f"[Worker {worker_id}] Initializing...")
    logger.info(f"  Queue directory: {queue_dir}")
    logger.info(f"  Worker ID: {worker_id}")
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    if not conn.connect():
        logger.error(f"[Worker {worker_id}] Failed to connect to Neo4j")
        sys.exit(1)
    
    try:
        # Setup schema if needed
        conn.setup_schema()
        
        # Create and run worker
        worker = FilingWorker(worker_id, queue_dir, conn)
        worker.run()
        
    except KeyboardInterrupt:
        logger.info(f"\n[Worker {worker_id}] Interrupted by user")
    except Exception as e:
        logger.error(f"[Worker {worker_id}] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

