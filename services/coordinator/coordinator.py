"""
Coordinator for Distributed Filing Processing

Creates work queue and monitors worker progress.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from services.data_loader.data_loader import list_filings


class FilingCoordinator:
    """Coordinates work distribution to workers."""
    
    def __init__(self, queue_dir: Path, year: Optional[int] = None, limit: Optional[int] = None):
        """
        Initialize coordinator.
        
        Args:
            queue_dir: Directory for work queue
            year: Optional year filter
            limit: Optional limit on number of filings
        """
        self.queue_dir = queue_dir
        self.year = year
        self.limit = limit
        
        # Create queue directories
        self.pending_dir = queue_dir / "pending"
        self.processing_dir = queue_dir / "processing"
        self.completed_dir = queue_dir / "completed"
        self.failed_dir = queue_dir / "failed"
        
        for dir_path in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_jobs(self, use_ai_extraction: bool = True) -> int:
        """
        Create job files for all filings.
        
        Args:
            use_ai_extraction: Whether to use AI extraction
            
        Returns:
            Number of jobs created
        """
        print("Creating work queue...")
        
        filings = list_filings(self.year)
        
        if self.limit:
            filings = filings[:self.limit]
        
        job_count = 0
        for filing_path in filings:
            job_data = {
                'filing_path': str(filing_path),
                'filing_name': filing_path.name,
                'use_ai_extraction': use_ai_extraction,
                'created_at': time.time()
            }
            
            job_file = self.pending_dir / f"{filing_path.stem}.json"
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
            
            job_count += 1
        
        print(f"✅ Created {job_count} jobs in queue")
        return job_count
    
    def get_status(self) -> Dict:
        """Get current queue status."""
        pending = len(list(self.pending_dir.glob("*.json")))
        processing = len(list(self.processing_dir.glob("*.json")))
        completed = len(list(self.completed_dir.glob("*.json")))
        failed = len(list(self.failed_dir.glob("*.json")))
        
        total = pending + processing + completed + failed
        
        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'progress': (completed / total * 100) if total > 0 else 0
        }
    
    def wait_for_completion(self, check_interval: int = 5, timeout: Optional[int] = None):
        """
        Wait for all jobs to complete.
        
        Args:
            check_interval: Seconds between status checks
            timeout: Maximum time to wait (None = no timeout)
        """
        start_time = time.time()
        
        print("\nMonitoring worker progress...")
        print("=" * 60)
        
        while True:
            status = self.get_status()
            
            elapsed = time.time() - start_time
            
            print(f"\r[{elapsed:.0f}s] "
                  f"Pending: {status['pending']} | "
                  f"Processing: {status['processing']} | "
                  f"Completed: {status['completed']} | "
                  f"Failed: {status['failed']} | "
                  f"Progress: {status['progress']:.1f}%", end='', flush=True)
            
            if status['pending'] == 0 and status['processing'] == 0:
                print("\n")
                break
            
            if timeout and elapsed > timeout:
                print(f"\n⚠️  Timeout reached ({timeout}s)")
                break
            
            time.sleep(check_interval)
        
        return self.get_status()
    
    def get_results(self) -> Dict:
        """Collect results from completed jobs."""
        results = {
            'companies': 0,
            'people': 0,
            'events': 0,
            'relationships': 0,
            'filings_processed': 0
        }
        
        for job_file in self.completed_dir.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                
                stats = job_data.get('stats', {})
                for key in results:
                    if key in stats:
                        results[key] += stats[key]
                
            except Exception as e:
                print(f"Error reading job result {job_file}: {e}")
        
        return results


def main():
    """Main entry point for coordinator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coordinate distributed filing processing")
    parser.add_argument("--year", type=int, help="Year filter")
    parser.add_argument("--limit", type=int, help="Limit number of filings")
    parser.add_argument("--queue-dir", default="/app/data/queue", help="Queue directory")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI extraction")
    parser.add_argument("--wait", action="store_true", help="Wait for completion")
    
    args = parser.parse_args()
    
    queue_dir = Path(args.queue_dir)
    coordinator = FilingCoordinator(queue_dir, year=args.year, limit=args.limit)
    
    # Create jobs
    job_count = coordinator.create_jobs(use_ai_extraction=not args.no_ai)
    
    if args.wait:
        # Wait for completion
        final_status = coordinator.wait_for_completion()
        
        # Show results
        print("\n" + "=" * 60)
        print("Processing Complete")
        print("=" * 60)
        results = coordinator.get_results()
        print(f"✅ Companies created: {results['companies']}")
        print(f"✅ People created: {results['people']}")
        print(f"✅ Events created: {results['events']}")
        print(f"✅ Relationships created: {results['relationships']}")
        print(f"✅ Filings processed: {results['filings_processed']}")
        print(f"\nCompleted: {final_status['completed']}")
        print(f"Failed: {final_status['failed']}")
    else:
        print(f"\n✅ {job_count} jobs queued. Workers will process them.")
        print("Run with --wait to monitor progress.")


if __name__ == "__main__":
    main()

