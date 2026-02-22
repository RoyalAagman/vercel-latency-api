import json
import os
import statistics
from http.server import BaseHTTPRequestHandler

# Load the telemetry data once when the function starts
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')

with open(DATA_FILE, 'r') as f:
    RAW_DATA = json.load(f)

def calculate_metrics(regions, threshold_ms):
    result = {}
    for region in regions:
        # Filter records for this region
        records = [r for r in RAW_DATA if r['region'] == region]
        
        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue
        
        latencies = [r['latency_ms'] for r in records]
        uptimes = [r['uptime_pct'] for r in records]
        
        # Sort latencies for percentile calculation
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        # 95th percentile: index at 95% of the way through the sorted list
        p95_index = int(0.95 * n)
        if p95_index >= n:
            p95_index = n - 1
        
        result[region] = {
            "avg_latency": round(statistics.mean(latencies), 4),
            "p95_latency": round(sorted_latencies[p95_index], 4),
            "avg_uptime": round(statistics.mean(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > threshold_ms)
        }
    
    return result

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        # Read the incoming JSON body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            payload = json.loads(body)
            regions = payload.get('regions', [])
            threshold_ms = payload.get('threshold_ms', 180)
            
            metrics = calculate_metrics(regions, threshold_ms)
            
            response = json.dumps(metrics).encode('utf-8')
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response)
        
        except Exception as e:
            self.send_response(400)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')