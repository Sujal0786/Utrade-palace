# 🚀 Rate Limiter - Quick Testing Guide

This guide shows you exactly how to test and verify the HTTP rate limiter functionality step by step.

## 📋 Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Start the HTTP Server

```bash
# Start the server (default port 5000)
python main.py --mode server

# You should see output like:
# Starting Rate Limiter HTTP Server on http://0.0.0.0:5000
# Available algorithms: fixed_window, token_bucket
```

### 2. Test the Server is Running

Open a new terminal and run:

```bash
# Health check
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","timestamp":1710000000,"available_algorithms":["fixed_window","token_bucket"],"total_requests":0}
```

### 3. Check Available Endpoints

```bash
# Get API documentation
curl http://localhost:5000/

# Expected response shows all available endpoints
```

## 🧪 Testing Rate Limiting

### Test 1: Basic Rate Limiting Check

```bash
# Make a request for a new client
curl -X POST "http://localhost:5000/request?client_id=test_user&algorithm=fixed_window"

# Expected response (first request should be allowed):
# {"client_id":"test_user","algorithm":"fixed_window","timestamp":1710000000,"allowed":true,"result":"ALLOWED","status":"success"}
```

### Test 2: Rate Limiting in Action

```bash
# Make multiple requests quickly (should hit the limit)
for i in {1..12}; do
    echo "Request $i:"
    curl -s -X POST "http://localhost:5000/request?client_id=test_user&algorithm=fixed_window" | jq '.result'
    sleep 0.1
done

# Expected output:
# Request 1: ALLOWED
# Request 2: ALLOWED
# ...
# Request 10: ALLOWED
# Request 11: RATE_LIMITED  <-- Limit reached
# Request 12: RATE_LIMITED
```

### Test 3: Different Clients Are Independent

```bash
# Test with a different client (should have fresh limits)
curl -X POST "http://localhost:5000/request?client_id=another_user&algorithm=fixed_window"

# Expected response: ALLOWED (even though test_user is rate limited)
```

### Test 4: Token Bucket Algorithm

```bash
# Test token bucket (allows bursts)
for i in {1..8}; do
    echo "Request $i:"
    curl -s -X POST "http://localhost:5000/request?client_id=bucket_test&algorithm=token_bucket" | jq '.result'
    sleep 0.05
done

# Wait for tokens to refill
echo "Waiting for tokens to refill..."
sleep 3

# Try again (should have some tokens available)
curl -X POST "http://localhost:5000/request?client_id=bucket_test&algorithm=token_bucket"
```

## 📊 Testing Statistics

### Check Global Statistics

```bash
# Get comprehensive statistics
curl -s http://localhost:5000/stats | jq

# Expected response shows:
# - Total requests made
# - Allowed vs rejected counts
# - Per-client breakdown
# - Per-algorithm breakdown
```

### Check Specific Client Statistics

```bash
# Get stats for a specific client
curl -s http://localhost:5000/stats/client/test_user | jq

# Shows detailed stats for just that client
```

### Reset Statistics

```bash
# Reset all statistics
curl -X POST http://localhost:5000/reset

# Expected response:
# {"message":"Statistics reset successfully","status":"success"}
```

## 🔍 Advanced Testing Scenarios

### Scenario 1: Concurrent Requests

```bash
# Open multiple terminals and run simultaneously:
# Terminal 1:
for i in {1..20}; do
    curl -s -X POST "http://localhost:5000/request?client_id=concurrent1&algorithm=fixed_window" | jq '.result' &
done

# Terminal 2:
for i in {1..20}; do
    curl -s -X POST "http://localhost:5000/request?client_id=concurrent2&algorithm=fixed_window" | jq '.result' &
done

# Both clients should be rate limited independently
```

### Scenario 2: Algorithm Comparison

```bash
# Test both algorithms with same client
echo "=== Fixed Window Test ==="
for i in {1..15}; do
    curl -s -X POST "http://localhost:5000/request?client_id=compare_test&algorithm=fixed_window" | jq '.result'
    sleep 0.1
done

echo "=== Token Bucket Test ==="
for i in {1..15}; do
    curl -s -X POST "http://localhost:5000/request?client_id=compare_test&algorithm=token_bucket" | jq '.result'
    sleep 0.1
done

# Compare the behavior patterns
```

### Scenario 3: Window Reset Test

```bash
# Fill up the fixed window
for i in {1..10}; do
    curl -s -X POST "http://localhost:5000/request?client_id=window_test&algorithm=fixed_window" | jq '.result'
done

# Should be rate limited now
curl -s -X POST "http://localhost:5000/request?client_id=window_test&algorithm=fixed_window" | jq '.result'

# Wait for window to reset (60 seconds based on config)
echo "Waiting 60 seconds for window to reset..."
sleep 60

# Should be allowed again
curl -s -X POST "http://localhost:5000/request?client_id=window_test&algorithm=fixed_window" | jq '.result'
```

## 🛠️ Python Client Testing

Create a test file `test_client.py`:

```python
import requests
import time
import json

def test_rate_limiter():
    base_url = "http://localhost:5000"
    
    print("=== Rate Limiter Test ===")
    
    # Test 1: Basic functionality
    print("\n1. Testing basic functionality...")
    response = requests.post(f"{base_url}/request", params={
        "client_id": "python_test",
        "algorithm": "fixed_window"
    })
    print(f"First request: {response.json()['result']}")
    
    # Test 2: Rate limiting
    print("\n2. Testing rate limiting...")
    allowed_count = 0
    for i in range(12):
        response = requests.post(f"{base_url}/request", params={
            "client_id": "python_test",
            "algorithm": "fixed_window"
        })
        if response.json()['allowed']:
            allowed_count += 1
        print(f"Request {i+1}: {response.json()['result']}")
    
    print(f"Total allowed: {allowed_count} (should be 10)")
    
    # Test 3: Different client
    print("\n3. Testing different client...")
    response = requests.post(f"{base_url}/request", params={
        "client_id": "another_python_test",
        "algorithm": "fixed_window"
    })
    print(f"Different client: {response.json()['result']}")
    
    # Test 4: Statistics
    print("\n4. Getting statistics...")
    stats = requests.get(f"{base_url}/stats").json()
    print(f"Total requests: {stats['global']['total_requests']}")
    print(f"Allowed: {stats['global']['allowed_requests']}")
    print(f"Rejected: {stats['global']['rejected_requests']}")

if __name__ == "__main__":
    test_rate_limiter()
```

Run the test:
```bash
python test_client.py
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill existing process
   lsof -ti:5000 | xargs kill -9
   
   # Or use different port
   python main.py --mode server --port 8080
   ```

2. **Connection refused**
   ```bash
   # Make sure server is running
   ps aux | grep python
   
   # Check if firewall is blocking
   telnet localhost 5000
   ```

3. **Invalid algorithm**
   ```bash
   # Check available algorithms
   curl http://localhost:5000/ | jq '.available_algorithms'
   
   # Use correct algorithm names
   curl -X POST "http://localhost:5000/request?client_id=test&algorithm=fixed_window"
   ```

### Debug Mode

```bash
# Run server in debug mode for detailed logs
python main.py --mode server --debug
```

## 📈 Expected Behavior

### Fixed Window Algorithm
- Allows exactly 10 requests per 60-second window
- All requests after 10th are rejected until window resets
- Each client has independent windows

### Token Bucket Algorithm  
- Allows bursts up to 10 requests
- Refills at 1 token per second
- Allows gradual recovery after rate limiting

### Statistics
- Tracks all requests across all clients
- Provides per-client and per-algorithm breakdowns
- Shows allowance/rejection rates

## ✅ Success Criteria

Your rate limiter is working correctly if:

1. ✅ Server starts without errors
2. ✅ Health check returns "healthy" status
3. ✅ First 10 requests per client are allowed
4. ✅ Requests beyond limit are rejected
5. ✅ Different clients have independent limits
6. ✅ Statistics accurately track all requests
7. ✅ Both algorithms behave as expected

## 🎯 Quick Validation Script

```bash
#!/bin/bash
# Quick validation script

echo "=== Rate Limiter Validation ==="

# Test server is running
echo "1. Testing server health..."
curl -s http://localhost:5000/health | jq -e '.status == "healthy"' || exit 1

# Test basic functionality
echo "2. Testing rate limiting..."
allowed=0
for i in {1..12}; do
    result=$(curl -s -X POST "http://localhost:5000/request?client_id=validation_test&algorithm=fixed_window" | jq -r '.result')
    if [ "$result" = "ALLOWED" ]; then
        ((allowed++))
    fi
done

if [ $allowed -eq 10 ]; then
    echo "✅ Rate limiting working correctly"
else
    echo "❌ Rate limiting failed (allowed: $allowed, expected: 10)"
    exit 1
fi

# Test statistics
echo "3. Testing statistics..."
total=$(curl -s http://localhost:5000/stats | jq '.global.total_requests')
if [ $total -gt 0 ]; then
    echo "✅ Statistics tracking working"
else
    echo "❌ Statistics not tracking"
    exit 1
fi

echo "🎉 All tests passed! Rate limiter is working correctly."
```

Run this script to quickly validate everything is working:
```bash
chmod +x validate.sh && ./validate.sh
```

---

**That's it!** You now have everything you need to test and verify the HTTP rate limiter functionality. The server supports both algorithms, maintains statistics, and provides a complete REST API for integration.
