import time
from flask import Flask, request
import requests
import random
import statistics
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of backend servers
servers = ['http://localhost:5000', 'http://localhost:5001', 'http://localhost:5002']
current_server = 0
response_times = []

def round_robin():
    global current_server
    server = servers[current_server]
    current_server = (current_server + 1) % len(servers)
    return server

def random_select():
    return random.choice(servers)

@app.route('/process/<strategy>', methods=['GET'])
def balance(strategy):
    server = round_robin() if strategy == 'round-robin' else random_select()
    try:
        start_time = time.time()
        logger.info(f"Forwarding to {server} for strategy {strategy}")
        response = requests.get(f"{server}/process", timeout=5)
        elapsed = time.time() - start_time
        response_times.append(elapsed)
        logger.info(f"Response from {server} in {elapsed:.3f}s")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Server {server} failed: {str(e)}")
        return {"error": f"Server {server} failed: {str(e)}"}, 503

@app.route('/metrics/<strategy>', methods=['GET'])
def metrics(strategy):
    request_counts = []
    for server in servers:
        try:
            response = requests.get(f"{server}/metrics", timeout=2)
            request_counts.append(response.json()['request_count'])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch metrics from {server}: {str(e)}")
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
    app.run(host='0.0.0.0', port=8000)