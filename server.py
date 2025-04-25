from flask import Flask, request
import time
import random

app = Flask(__name__)
request_count = 0

@app.route('/process', methods=['GET'])
def process_request():
    global request_count
    request_count += 1
    # Simulate variable processing time (e.g., fetching product data)
    workload = random.uniform(0.1, 1.0)  # Random delay between 0.1s and 1s
    time.sleep(workload)
    return {
        "status": "success",
        "workload": workload,
        "server": request.host,
        "request_count": request_count
    }

@app.route('/metrics', methods=['GET'])
def get_metrics():
    return {"request_count": request_count}

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='0.0.0.0', port=port)