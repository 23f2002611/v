from fastapi import FastAPI, Body, HTTPException, Request, Response
from pathlib import Path
import json
from statistics import mean
import math

app = FastAPI(title="eShopCo Latency Metrics")
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry bundle at cold start
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "telemetry.json"
with DATA_PATH.open() as f:
    TELEMETRY = json.load(f)

def p95(values):
    if not values:
        return None
    s = sorted(values)
    k = 0.95 * (len(s) - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return float(d0 + d1)

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/api/latency")
async def options_handler():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/api/latency")
def latency_metrics(payload: dict = Body(...)):
    regions = payload.get("regions")
    threshold = payload.get("threshold_ms")
    
    if not isinstance(regions, list) or not all(isinstance(r, str) for r in regions):
        raise HTTPException(status_code=400, detail="`regions` must be a list of strings")
    if not isinstance(threshold, (int, float)):
        raise HTTPException(status_code=400, detail="`threshold_ms` must be a number")
    
    out = {}
    for region in regions:
        rows = [r for r in TELEMETRY if r.get("region") == region]
        lat = [r["latency_ms"] for r in rows]
        up  = [r["uptime_pct"] for r in rows]
        
        if not rows:
            out[region] = {"avg_latency": 0.0, "p95_latency": 0.0, "avg_uptime": 0.0, "breaches": 0}
            continue
        
        breaches = sum(1 for v in lat if v > threshold)
        metrics = {
            "avg_latency": round(mean(lat), 4),
            "p95_latency": round(p95(lat), 4),
            "avg_uptime": round(mean(up), 4),
            "breaches": breaches
        }
        out[region] = metrics
    
    return out
