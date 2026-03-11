"""
Multi-threaded Test Harness

Simulates concurrent clients making requests through the rate limiter.
Tests thread safety and demonstrates rate limiting behavior under load.
"""

import threading
import time
import random
from typing import List
from rate_limiter import RateLimiter
from stats import Statistics


class TestHarness:
    """
    Multi-threaded test harness for rate limiting.
    
    Simulates multiple clients making concurrent requests to test
    thread safety and rate limiting behavior.
    """
    
    def __init__(self, rate_limiter: RateLimiter, statistics: Statistics):
        """
        Initialize the test harness.
        
        Args:
            rate_limiter: Configured rate limiter instance
            statistics: Statistics tracker instance
        """
        self.rate_limiter = rate_limiter
        self.statistics = statistics
        self.running = False
        self.threads = []
    
    def client_worker(self, client_id: str, num_requests: int, algorithm: str):
        """
        Worker function that simulates a client making requests.
        
        Args:
            client_id: Unique identifier for this client
            num_requests: Number of requests to make
            algorithm: Which rate limiting algorithm to use
        """
        for i in range(num_requests):
            if not self.running:
                break
            
            # Make request through rate limiter
            is_allowed, timestamp, _, alg, result = self.rate_limiter.check_request(
                client_id, algorithm
            )
            
            # Record the request in statistics
            self.statistics.record_request(client_id, algorithm, is_allowed)
            
            # Print request log
            print(f"{timestamp} | {client_id} | {alg} | {result}")
            
            # Random delay between requests (0.01 to 0.1 seconds)
            time.sleep(random.uniform(0.01, 0.1))
    
    def run_test(self, num_clients: int = 5, requests_per_client: int = 20):
        """
        Run the multi-threaded test.
        
        Args:
            num_clients: Number of concurrent clients to simulate
            requests_per_client: Number of requests each client should make
        """
        print(f"\nStarting rate limiting test with {num_clients} clients, "
              f"{requests_per_client} requests per client...")
        print("Format: timestamp | client_id | algorithm | result")
        print("-" * 50)
        
        self.running = True
        self.threads = []
        
        # Get available algorithms
        algorithms = self.rate_limiter.get_available_algorithms()
        if not algorithms:
            print("No algorithms available!")
            return
        
        # Create and start threads for each client
        for i in range(num_clients):
            client_id = f"client_{i + 1}"
            
            # Randomly choose an algorithm for this client
            algorithm = random.choice(algorithms)
            
            # Create worker thread
            thread = threading.Thread(
                target=self.client_worker,
                args=(client_id, requests_per_client, algorithm),
                name=f"Client-{client_id}"
            )
            
            self.threads.append(thread)
            thread.start()
            
            # Small delay between starting threads
            time.sleep(0.01)
        
        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()
        
        print("-" * 50)
        print("Test completed!")
    
    def stop_test(self):
        """Stop the running test."""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=1.0)
    
    def run_stress_test(self, duration_seconds: int = 10):
        """
        Run a stress test with continuous requests for a specified duration.
        
        Args:
            duration_seconds: How long to run the stress test
        """
        print(f"\nStarting stress test for {duration_seconds} seconds...")
        print("Format: timestamp | client_id | algorithm | result")
        print("-" * 50)
        
        self.running = True
        self.threads = []
        
        algorithms = self.rate_limiter.get_available_algorithms()
        if not algorithms:
            print("No algorithms available!")
            return
        
        # Create multiple threads per client for higher concurrency
        num_clients = 5
        threads_per_client = 2
        
        for client_idx in range(num_clients):
            client_id = f"client_{client_idx + 1}"
            algorithm = random.choice(algorithms)
            
            for thread_idx in range(threads_per_client):
                thread = threading.Thread(
                    target=self._stress_worker,
                    args=(client_id, algorithm, duration_seconds),
                    name=f"Stress-{client_id}-{thread_idx}"
                )
                
                self.threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()
        
        print("-" * 50)
        print("Stress test completed!")
    
    def _stress_worker(self, client_id: str, algorithm: str, duration_seconds: int):
        """
        Worker function for stress testing - makes requests continuously.
        
        Args:
            client_id: Unique identifier for this client
            algorithm: Which rate limiting algorithm to use
            duration_seconds: How long to run this worker
        """
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration_seconds:
            # Make request through rate limiter
            is_allowed, timestamp, _, alg, result = self.rate_limiter.check_request(
                client_id, algorithm
            )
            
            # Record the request in statistics
            self.statistics.record_request(client_id, algorithm, is_allowed)
            
            # Print request log
            print(f"{timestamp} | {client_id} | {alg} | {result}")
            
            # Very short delay for high frequency requests
            time.sleep(random.uniform(0.001, 0.01))
