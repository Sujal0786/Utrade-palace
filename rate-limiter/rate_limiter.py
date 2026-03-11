"""
Main Rate Limiter Manager

Coordinates multiple rate limiting algorithms and provides a unified interface.
Thread-safe implementation that manages different algorithms per client.
"""

import json
import time
from typing import Dict, Any
from algorithms.fixed_window import FixedWindowLimiter
from algorithms.token_bucket import TokenBucketLimiter


class RateLimiter:
    """
    Main Rate Limiter Manager
    
    Manages multiple rate limiting algorithms and provides a unified interface
    for checking request permissions across different algorithms.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the rate limiter with configuration.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.limiters = self._initialize_limiters()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in configuration file: {e}")
    
    def _initialize_limiters(self) -> Dict[str, Any]:
        """Initialize rate limiting algorithms based on configuration."""
        limiters = {}
        
        # Initialize Fixed Window Limiter
        if 'fixed_window' in self.config:
            fw_config = self.config['fixed_window']
            limiters['fixed_window'] = FixedWindowLimiter(
                max_requests=fw_config['max_requests'],
                window_seconds=fw_config['window_seconds']
            )
        
        # Initialize Token Bucket Limiter
        if 'token_bucket' in self.config:
            tb_config = self.config['token_bucket']
            limiters['token_bucket'] = TokenBucketLimiter(
                bucket_size=tb_config['bucket_size'],
                refill_rate=tb_config['refill_rate']
            )
        
        return limiters
    
    def check_request(self, client_id: str, algorithm: str) -> tuple:
        """
        Check if a request is allowed for the given client and algorithm.
        
        Args:
            client_id: Unique identifier for the client
            algorithm: Name of the algorithm to use ('fixed_window' or 'token_bucket')
            
        Returns:
            Tuple of (is_allowed, timestamp, client_id, algorithm, result_string)
        """
        if algorithm not in self.limiters:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        timestamp = int(time.time())
        limiter = self.limiters[algorithm]
        
        # Check if request is allowed
        is_allowed = limiter.is_allowed(client_id)
        result = "ALLOWED" if is_allowed else "RATE_LIMITED"
        
        return (is_allowed, timestamp, client_id, algorithm, result)
    
    def get_algorithm_info(self, algorithm: str, client_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an algorithm's state for a client.
        
        Args:
            algorithm: Name of the algorithm
            client_id: Unique identifier for the client
            
        Returns:
            Dictionary with algorithm-specific information
        """
        if algorithm not in self.limiters:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        limiter = self.limiters[algorithm]
        return limiter.get_client_info(client_id)
    
    def get_available_algorithms(self) -> list:
        """Get list of available algorithms."""
        return list(self.limiters.keys())
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
