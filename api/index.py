import json
import os
import statistics
from http.server import BaseHTTPRequestHandler

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
with open(DATA_FILE, 'r') as f:
    RAW_DATA = json.load(f)

class handler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        regions = body.get('regions', [])
        threshold_ms = body.get('threshold_ms', 180)

        result = {}
        for region in regions:
            records = [r for r in RAW_DATA if r['region'] == region]
            if not records:
                result[region] = {"avg_latency": None, "p95_latency": None, "avg_uptime": None, "breaches": 0}
                continue
            latencies = sorted([r['latency_ms'] for r in records])
            uptimes = [r['uptime_pct'] for r in records]
            p95_idx = min(int(0.95 * len(latencies)), len(latencies) - 1)
            result[region] = {
                "avg_latency": round(statistics.mean(latencies), 4),
                "p95_latency": round(latencies[p95_idx], 4),
                "avg_uptime": round(statistics.mean(uptimes), 4),
                "breaches": sum(1 for l in latencies if l > threshold_ms)
            }

        out = json.dumps(result).encode()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)