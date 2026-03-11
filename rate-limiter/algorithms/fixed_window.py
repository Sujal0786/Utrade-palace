"""
Fixed Window Rate Limiting Algorithm

Implements a simple fixed window counter that resets after each time window.
Thread-safe implementation using locks.
"""

import time
import threading
from typing import Dict


class FixedWindowLimiter:
    """
    Fixed Window Rate Limiter
    
    Allows N requests per T seconds window for each client.
    Maintains separate counters and timestamps per client.
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize the fixed window limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Duration of each window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # Per-client state: {client_id: (request_count, window_start_time)}
        self.client_state: Dict[str, tuple] = {}
        
        # Thread safety lock
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a request from the given client is allowed.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = int(time.time())
        
        with self.lock:
            # Get or initialize client state
            if client_id not in self.client_state:
                self.client_state[client_id] = (0, current_time)
            
            request_count, window_start = self.client_state[client_id]
            
            # Check if window has expired and needs reset
            if current_time - window_start >= self.window_seconds:
                # Reset window
                request_count = 0
                window_start = current_time
            
            # Check if request is allowed
            if request_count < self.max_requests:
                # Increment counter and update state
                request_count += 1
                self.client_state[client_id] = (request_count, window_start)
                return True
            else:
                # Rate limited
                return False
    
    def get_client_info(self, client_id: str) -> Dict:
        """
        Get current rate limiting information for a client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Dictionary with client rate limiting info
        """
        with self.lock:
            if client_id not in self.client_state:
                return {
                    'requests_in_window': 0,
                    'window_start': 0,
                    'window_remaining': self.window_seconds
                }
            
            request_count, window_start = self.client_state[client_id]
            current_time = int(time.time())
            window_remaining = max(0, self.window_seconds - (current_time - window_start))
            
            return {
                'requests_in_window': request_count,
                'window_start': window_start,
                'window_remaining': window_remaining
            }
