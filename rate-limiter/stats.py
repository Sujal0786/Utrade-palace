"""
Statistics Tracking for Rate Limiter

Thread-safe statistics collection and reporting for rate limiting operations.
"""

import threading
from typing import Dict, Any
from collections import defaultdict


class Statistics:
    """
    Thread-safe statistics tracker for rate limiting operations.
    
    Tracks total requests, allowed/rejected counts, and per-client statistics.
    """
    
    def __init__(self):
        """Initialize statistics tracking."""
        # Global counters
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0
        
        # Per-client statistics: {client_id: {'allowed': X, 'rejected': Y}}
        self.client_stats = defaultdict(lambda: {'allowed': 0, 'rejected': 0})
        
        # Per-algorithm statistics: {algorithm: {'allowed': X, 'rejected': Y}}
        self.algorithm_stats = defaultdict(lambda: {'allowed': 0, 'rejected': 0})
        
        # Thread safety lock
        self.lock = threading.Lock()
    
    def record_request(self, client_id: str, algorithm: str, is_allowed: bool):
        """
        Record a rate limiting decision.
        
        Args:
            client_id: Unique identifier for the client
            algorithm: Name of the algorithm used
            is_allowed: Whether the request was allowed or rejected
        """
        with self.lock:
            self.total_requests += 1
            
            if is_allowed:
                self.allowed_requests += 1
                self.client_stats[client_id]['allowed'] += 1
                self.algorithm_stats[algorithm]['allowed'] += 1
            else:
                self.rejected_requests += 1
                self.client_stats[client_id]['rejected'] += 1
                self.algorithm_stats[algorithm]['rejected'] += 1
    
    def get_global_stats(self) -> Dict[str, int]:
        """Get global statistics."""
        with self.lock:
            return {
                'total_requests': self.total_requests,
                'allowed_requests': self.allowed_requests,
                'rejected_requests': self.rejected_requests
            }
    
    def get_client_stats(self) -> Dict[str, Dict[str, int]]:
        """Get per-client statistics."""
        with self.lock:
            return dict(self.client_stats)
    
    def get_algorithm_stats(self) -> Dict[str, Dict[str, int]]:
        """Get per-algorithm statistics."""
        with self.lock:
            return dict(self.algorithm_stats)
    
    def print_summary(self):
        """Print a comprehensive statistics summary."""
        global_stats = self.get_global_stats()
        client_stats = self.get_client_stats()
        algorithm_stats = self.get_algorithm_stats()
        
        print("\n" + "="*60)
        print("RATE LIMITING STATISTICS SUMMARY")
        print("="*60)
        
        # Global statistics
        print(f"\nGLOBAL STATISTICS:")
        print(f"  TOTAL REQUESTS: {global_stats['total_requests']}")
        print(f"  ALLOWED: {global_stats['allowed_requests']}")
        print(f"  REJECTED: {global_stats['rejected_requests']}")
        
        if global_stats['total_requests'] > 0:
            allowed_rate = (global_stats['allowed_requests'] / global_stats['total_requests']) * 100
            rejected_rate = (global_stats['rejected_requests'] / global_stats['total_requests']) * 100
            print(f"  ALLOWANCE RATE: {allowed_rate:.1f}%")
            print(f"  REJECTION RATE: {rejected_rate:.1f}%")
        
        # Per-algorithm statistics
        print(f"\nPER-ALGORITHM STATISTICS:")
        for algorithm, stats in algorithm_stats.items():
            total = stats['allowed'] + stats['rejected']
            if total > 0:
                allowed_rate = (stats['allowed'] / total) * 100
                print(f"  {algorithm.upper()}:")
                print(f"    Total: {total}, Allowed: {stats['allowed']}, Rejected: {stats['rejected']}")
                print(f"    Allowance Rate: {allowed_rate:.1f}%")
        
        # Per-client statistics
        print(f"\nPER-CLIENT STATISTICS:")
        for client_id, stats in sorted(client_stats.items()):
            total = stats['allowed'] + stats['rejected']
            if total > 0:
                allowed_rate = (stats['allowed'] / total) * 100
                print(f"  {client_id}:")
                print(f"    Total: {total}, Allowed: {stats['allowed']}, Rejected: {stats['rejected']}")
                print(f"    Allowance Rate: {allowed_rate:.1f}%")
        
        print("="*60)
    
    def reset(self):
        """Reset all statistics."""
        with self.lock:
            self.total_requests = 0
            self.allowed_requests = 0
            self.rejected_requests = 0
            self.client_stats.clear()
            self.algorithm_stats.clear()
