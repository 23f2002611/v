from fastapi import FastAPI, Body, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from statistics import mean
import math

app = FastAPI(title="eShopCo Latency Metrics")

# ======================
# CORS - Critical for Vercel
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Load telemetry data
# ======================
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "telemetry.json"
if DATA_PATH.exists():
    with DATA_PATH.open() as f:
        TELEMETRY = json.load(f)
else:
    TELEMETRY = []

# ======================
# P95 helper function
# ======================
def p95(values):
    if not values:
        return 0.0
    s = sorted(values)
    k = 0.95 * (len(s) - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return float(d0 + d1)

# ======================
# Root handler (for redirects)
# ======================
@app.get("/")
def root():
    return JSONResponse(
        content={"status": "ok", "service": "eShopCo Latency Metrics"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ======================
# Latency POST endpoint
# ======================
@app.post("/api/latency")
@app.post("/latency")
def latency_metrics(payload: dict = Body(...)):
    regions = payload.get("regions")
    threshold = payload.get("threshold_ms")
    
    if not isinstance(regions, list) or not all(isinstance(r, str) for r in regions):
        return JSONResponse(
            status_code=400,
            content={"detail": "`regions` must be a list of strings"}
        )
    
    if not isinstance(threshold, (int, float)):
        return JSONResponse(
            status_code=400,
            content={"detail": "`threshold_ms` must be a number"}
        )
    
    out = {}
    for region in regions:
        rows = [r for r in TELEMETRY if r.get("region") == region]
        lat = [r["latency_ms"] for r in rows]
        up  = [r["uptime_pct"] for r in rows]
        
        if not rows:
            out[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0,
            }
            continue
        
        breaches = sum(1 for v in lat if v > threshold)
        metrics = {
            "avg_latency": round(mean(lat), 4),
            "p95_latency": round(p95(lat), 4),
            "avg_uptime": round(mean(up), 4),
            "breaches": breaches
        }
        out[region] = metrics
    
    return JSONResponse(content=out)

# ======================
# Healthcheck
# ======================
@app.get("/api/ping")
@app.get("/ping")
def ping():
    return JSONResponse(content={"msg": "pong"})

# ======================
# Favicon handler
# ======================
@app.get("/favicon.ico")
def favicon():
    return Response(content=b"", media_type="image/x-icon")

# ======================
# Vercel serverless handler
# ======================
handler = app
