"""
Token Bucket Rate Limiting Algorithm

Implements token bucket algorithm that allows bursts while maintaining average rate.
Thread-safe implementation using locks.
"""

import time
import threading
from typing import Dict


class TokenBucketLimiter:
    """
    Token Bucket Rate Limiter
    
    Each client has a bucket with max_tokens that refills at refill_rate tokens/second.
    Requests consume tokens; if insufficient tokens, request is rate limited.
    """
    
    def __init__(self, bucket_size: int, refill_rate: int):
        """
        Initialize the token bucket limiter.
        
        Args:
            bucket_size: Maximum number of tokens in the bucket
            refill_rate: Number of tokens to add per second
        """
        self.bucket_size = bucket_size
        self.refill_rate = refill_rate
        
        # Per-client state: {client_id: (current_tokens, last_refill_timestamp)}
        self.client_buckets: Dict[str, tuple] = {}
        
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
        current_time = time.time()
        
        with self.lock:
            # Get or initialize client bucket
            if client_id not in self.client_buckets:
                # Start with full bucket for new clients
                self.client_buckets[client_id] = (self.bucket_size, current_time)
            
            current_tokens, last_refill = self.client_buckets[client_id]
            
            # Calculate tokens to add based on elapsed time
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            
            # Refill tokens (but don't exceed bucket size)
            current_tokens = min(self.bucket_size, current_tokens + tokens_to_add)
            
            # Check if we have at least 1 token
            if current_tokens >= 1:
                # Consume 1 token
                current_tokens -= 1
                self.client_buckets[client_id] = (current_tokens, current_time)
                return True
            else:
                # Update last refill time even when rate limited
                self.client_buckets[client_id] = (current_tokens, current_time)
                return False
    
    def get_client_info(self, client_id: str) -> Dict:
        """
        Get current bucket information for a client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Dictionary with client bucket info
        """
        with self.lock:
            if client_id not in self.client_buckets:
                return {
                    'current_tokens': self.bucket_size,
                    'bucket_size': self.bucket_size,
                    'refill_rate': self.refill_rate,
                    'time_to_next_token': 0
                }
            
            current_tokens, last_refill = self.client_buckets[client_id]
            current_time = time.time()
            
            # Calculate current tokens after potential refill
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * self.refill_rate
            current_tokens = min(self.bucket_size, current_tokens + tokens_to_add)
            
            # Time until next token is available
            if current_tokens < 1:
                time_to_next_token = (1 - current_tokens) / self.refill_rate
            else:
                time_to_next_token = 0
            
            return {
                'current_tokens': current_tokens,
                'bucket_size': self.bucket_size,
                'refill_rate': self.refill_rate,
                'time_to_next_token': time_to_next_token
            }
