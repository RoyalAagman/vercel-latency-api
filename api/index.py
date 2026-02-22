import json
import os
import statistics

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
with open(DATA_FILE, 'r') as f:
    RAW_DATA = json.load(f)

def handler(request):
    # CORS headers for every response
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }

    if request.method == 'OPTIONS':
        return Response('', 200, cors_headers)

    if request.method == 'POST':
        body = json.loads(request.body)
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

        return Response(json.dumps(result), 200, cors_headers)