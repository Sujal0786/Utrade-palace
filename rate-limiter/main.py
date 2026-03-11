"""
Main Entry Point for Rate Limiter Project

This script demonstrates the thread-safe rate limiter with multiple algorithms
and concurrent client simulation. Also supports HTTP server mode.
"""

import sys
import os
import argparse
from rate_limiter import RateLimiter
from stats import Statistics
from test_harness import TestHarness
from http_server import RateLimitHTTPServer


def main():
    """Main function to run the rate limiter demonstration."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Thread-Safe Rate Limiter')
    parser.add_argument('--mode', choices=['demo', 'server'], default='demo',
                       help='Run mode: demo (default) or server')
    parser.add_argument('--host', default='0.0.0.0',
                       help='HTTP server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                       help='HTTP server port (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode for HTTP server')
    
    args = parser.parse_args()
    
    # Check if running in server mode
    if args.mode == 'server':
        print("="*60)
        print("RATE LIMITER HTTP SERVER MODE")
        print("="*60)
        
        try:
            # Initialize and run HTTP server
            server = RateLimitHTTPServer()
            server.run(host=args.host, port=args.port, debug=args.debug)
        except Exception as e:
            print(f"Error starting HTTP server: {e}")
            sys.exit(1)
    
    # Default demo mode
    print("="*60)
    print("THREAD-SAFE RATE LIMITER DEMONSTRATION")
    print("="*60)
    
    try:
        # Initialize rate limiter with configuration
        config_path = "config.json"
        rate_limiter = RateLimiter(config_path)
        statistics = Statistics()
        test_harness = TestHarness(rate_limiter, statistics)
        
        # Display configuration
        config = rate_limiter.get_config()
        print(f"\nConfiguration loaded from {config_path}:")
        for algorithm, settings in config.items():
            print(f"  {algorithm}: {settings}")
        
        # Display available algorithms
        algorithms = rate_limiter.get_available_algorithms()
        print(f"\nAvailable algorithms: {', '.join(algorithms)}")
        
        # Run basic test
        print(f"\n{'='*60}")
        print("BASIC TEST: 5 clients, 20 requests each")
        test_harness.run_test(num_clients=5, requests_per_client=20)
        
        # Display statistics
        statistics.print_summary()
        
        # Reset statistics for next test
        statistics.reset()
        
        # Run stress test
        print(f"\n{'='*60}")
        print("STRESS TEST: Continuous requests for 5 seconds")
        test_harness.run_stress_test(duration_seconds=5)
        
        # Display final statistics
        statistics.print_summary()
        
        print(f"\n{'='*60}")
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
