"""
HTTP Server for Rate Limiter

Provides REST API endpoints for rate limiting requests and statistics.
Uses Flask for HTTP server functionality.
"""

from flask import Flask, request, jsonify
from rate_limiter import RateLimiter
from stats import Statistics
import threading
import time


class RateLimitHTTPServer:
    """
    HTTP Server wrapper for the rate limiter system.
    
    Provides REST API endpoints:
    - POST /request?client_id=X&algorithm=Y
    - GET /stats
    - GET /health
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the HTTP server.
        
        Args:
            config_path: Path to configuration file
        """
        self.app = Flask(__name__)
        self.rate_limiter = RateLimiter(config_path)
        self.statistics = Statistics()
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/request', methods=['POST'])
        def handle_request():
            """
            Handle rate limiting requests.
            
            Query Parameters:
            - client_id (required): Unique client identifier
            - algorithm (optional): Algorithm to use (fixed_window or token_bucket)
            
            Returns:
            JSON response with rate limiting decision
            """
            try:
                # Get query parameters
                client_id = request.args.get('client_id')
                algorithm = request.args.get('algorithm')
                
                # Validate required parameters
                if not client_id:
                    return jsonify({
                        'error': 'client_id parameter is required',
                        'status': 'error'
                    }), 400
                
                # Use default algorithm if not specified
                if not algorithm:
                    algorithms = self.rate_limiter.get_available_algorithms()
                    if not algorithms:
                        return jsonify({
                            'error': 'No algorithms available',
                            'status': 'error'
                        }), 500
                    algorithm = algorithms[0]
                
                # Validate algorithm
                if algorithm not in self.rate_limiter.get_available_algorithms():
                    return jsonify({
                        'error': f'Invalid algorithm: {algorithm}',
                        'available_algorithms': self.rate_limiter.get_available_algorithms(),
                        'status': 'error'
                    }), 400
                
                # Process request through rate limiter
                is_allowed, timestamp, _, alg, result = self.rate_limiter.check_request(
                    client_id, algorithm
                )
                
                # Record in statistics
                self.statistics.record_request(client_id, algorithm, is_allowed)
                
                # Return response
                return jsonify({
                    'client_id': client_id,
                    'algorithm': algorithm,
                    'timestamp': timestamp,
                    'allowed': is_allowed,
                    'result': result,
                    'status': 'success'
                })
                
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """
            Get rate limiting statistics.
            
            Returns:
            JSON response with comprehensive statistics
            """
            try:
                global_stats = self.statistics.get_global_stats()
                client_stats = self.statistics.get_client_stats()
                algorithm_stats = self.statistics.get_algorithm_stats()
                
                return jsonify({
                    'global': global_stats,
                    'clients': client_stats,
                    'algorithms': algorithm_stats,
                    'available_algorithms': self.rate_limiter.get_available_algorithms(),
                    'configuration': self.rate_limiter.get_config(),
                    'status': 'success'
                })
                
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500
        
        @self.app.route('/stats/client/<client_id>', methods=['GET'])
        def get_client_stats(client_id):
            """
            Get statistics for a specific client.
            
            Path Parameters:
            - client_id: Unique client identifier
            
            Returns:
            JSON response with client-specific statistics
            """
            try:
                client_stats = self.statistics.get_client_stats()
                
                if client_id not in client_stats:
                    return jsonify({
                        'error': f'Client {client_id} not found',
                        'status': 'error'
                    }), 404
                
                # Get algorithm-specific info for this client
                algorithm_info = {}
                for algorithm in self.rate_limiter.get_available_algorithms():
                    algorithm_info[algorithm] = self.rate_limiter.get_algorithm_info(
                        algorithm, client_id
                    )
                
                return jsonify({
                    'client_id': client_id,
                    'statistics': client_stats[client_id],
                    'algorithm_info': algorithm_info,
                    'status': 'success'
                })
                
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """
            Health check endpoint.
            
            Returns:
            JSON response with server health status
            """
            try:
                return jsonify({
                    'status': 'healthy',
                    'timestamp': int(time.time()),
                    'available_algorithms': self.rate_limiter.get_available_algorithms(),
                    'total_requests': self.statistics.get_global_stats()['total_requests']
                })
                
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e)
                }), 500
        
        @self.app.route('/reset', methods=['POST'])
        def reset_stats():
            """
            Reset statistics.
            
            Returns:
            JSON response confirming reset
            """
            try:
                self.statistics.reset()
                return jsonify({
                    'message': 'Statistics reset successfully',
                    'status': 'success'
                })
                
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500
        
        @self.app.route('/', methods=['GET'])
        def index():
            """
            Root endpoint with API information.
            
            Returns:
            JSON response with API documentation
            """
            return jsonify({
                'title': 'Rate Limiter HTTP API',
                'version': '1.0.0',
                'endpoints': {
                    'POST /request': {
                        'description': 'Check if request is allowed',
                        'parameters': {
                            'client_id': 'required - Client identifier',
                            'algorithm': 'optional - Algorithm (fixed_window or token_bucket)'
                        }
                    },
                    'GET /stats': {
                        'description': 'Get comprehensive statistics'
                    },
                    'GET /stats/client/<client_id>': {
                        'description': 'Get client-specific statistics'
                    },
                    'GET /health': {
                        'description': 'Health check endpoint'
                    },
                    'POST /reset': {
                        'description': 'Reset all statistics'
                    }
                },
                'available_algorithms': self.rate_limiter.get_available_algorithms()
            })
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Run the HTTP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        print(f"Starting Rate Limiter HTTP Server on http://{host}:{port}")
        print(f"Available algorithms: {', '.join(self.rate_limiter.get_available_algorithms())}")
        print("\nAPI Endpoints:")
        print("  POST /request?client_id=X&algorithm=Y")
        print("  GET /stats")
        print("  GET /stats/client/<client_id>")
        print("  GET /health")
        print("  POST /reset")
        print("  GET /")
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)
