from flask import Flask, request
import requests
import time
import random
import statistics
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_requests(load_balancer_url, strategy, num_requests=10):
    print(f"Sending {num_requests} requests to {load_balancer_url} with {strategy}")
    response_times = []
    server_counts = {}
    
    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.get(f"{load_balancer_url}/process/{strategy}", timeout=5)
            elapsed = time.time() - start_time
            response_times.append(elapsed)
            if response.status_code == 200:
                data = response.json()
                server = data['server']
                server_counts[server] = server_counts.get(server, 0) + 1
                print(f"Request {i+1}: Server {server}, Workload {data['workload']:.3f}s, Response time {elapsed:.3f}s")
            else:
                print(f"Request {i+1}: Failed with status {response.status_code}, {response.json()}")
        except requests.RequestException as e:
            print(f"Request {i+1}: Failed - {str(e)}")
        time.sleep(random.uniform(0.1, 0.5))  # Random delay between requests

    # Calculate local metrics
    request_counts = [server_counts.get(f"localhost:{port}", 0) for port in [5000, 5001, 5002]]
    load_imbalance = statistics.stdev(request_counts) if len(request_counts) > 1 else 0
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    print(f"\nLocal Metrics for {strategy}:")
    print(f"Request counts per server: {request_counts}")
    print(f"Load imbalance (std dev): {load_imbalance:.3f}")
    print(f"Average response time: {avg_response_time:.3f}s")

    # Fetch server-side metrics
    try:
        response = requests.get(f"{load_balancer_url}/metrics/{strategy}", timeout=5)
        metrics = response.json()
        print(f"\nServer Metrics for {strategy}:")
        print(f"Request counts per server: {metrics['request_counts']}")
        print(f"Load imbalance (std dev): {metrics['load_imbalance']:.3f}")
        print(f"Average response time: {metrics['avg_response_time']:.3f}s")
    except requests.RequestException as e:
        print(f"Failed to fetch server metrics: {str(e)}")

if __name__ == '__main__':
    print("Testing Static Load Balancer")
    send_requests('http://localhost:8000', 'round-robin', num_requests=10)
    send_requests('http://localhost:8000', 'random', num_requests=10)

    print("\nTesting Dynamic Load Balancer")
    send_requests('http://localhost:8001', 'least-connection', num_requests=10)
    send_requests('http://localhost:8001', 'weighted-response', num_requests=10)