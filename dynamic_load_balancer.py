import random
from flask import Flask, request
import requests
import time
import statistics
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of backend servers with metrics
servers = [
    {'url': 'http://localhost:5000', 'connections': 0, 'response_time': 0.5},
    {'url': 'http://localhost:5001', 'connections': 0, 'response_time': 0.5},
    {'url': 'http://localhost:5002', 'connections': 0, 'response_time': 0.5}
]
response_times = []

def least_connection():
    # Ensure servers with zero connections are prioritized
    min_connections = min(s['connections'] for s in servers)
    candidates = [s for s in servers if s['connections'] == min_connections]
    return random.choice(candidates) if candidates else min(servers, key=lambda x: x['connections'])

def weighted_response():
    return min(servers, key=lambda x: x['response_time'])

@app.route('/process/<strategy>', methods=['GET'])
def balance(strategy):
    server = least_connection() if strategy == 'least-connection' else weighted_response()
    server['connections'] += 1
    try:
        start_time = time.time()
        logger.info(f"Forwarding to {server['url']} for strategy {strategy}")
        response = requests.get(f"{server['url']}/process", timeout=5)
        elapsed = time.time() - start_time
        response_times.append(elapsed)
        # Update response time (exponential moving average)
        alpha = 0.3
        server['response_time'] = alpha * elapsed + (1 - alpha) * server['response_time']
        server['connections'] -= 1
        logger.info(f"Response from {server['url']} in {elapsed:.3f}s")
        return response.json()
    except requests.RequestException as e:
        server['response_time'] += 1.0
        server['connections'] -= 1
        logger.error(f"Server {server['url']} failed: {str(e)}")
        return {"error": f"Server {server['url']} failed: {str(e)}"}, 503

@app.route ('/metrics/<strategy>', methods=['GET'])
def metrics(strategy):
    request_counts = []
    for server in servers:
        try:
            response = requests.get(f"{server['url']}/metrics", timeout=2)
            request_counts.append(response.json()['request_count'])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch metrics from {server['url']}: {str(e)}")
            request_counts.append(0)
    load_imbalance = statistics.stdev(request_counts) if len(request_counts) > 1 else 0
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    return {
        "strategy": strategy,
        "request_counts": request_counts,
        "load_imbalance": load_imbalance,
        "avg_response_time": avg_response_time
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)