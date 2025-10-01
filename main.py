from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from statistics import mean
import math

app = FastAPI(title="eShopCo Latency Metrics")

# ✅ Enable CORS for all routes and origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=False,
    allow_methods=["*"],  # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# ✅ Load telemetry data
DATA_PATH = Path(__file__).resolve().parent / "data" / "telemetry.json"
if DATA_PATH.exists():
    with DATA_PATH.open() as f:
        TELEMETRY = json.load(f)
else:
    TELEMETRY = []

# ✅ P95 helper
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

# ✅ POST endpoint for latency metrics
from fastapi.responses import JSONResponse
@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    print(f"[DEBUG] {request.method} {request.url.path} headers={response.headers}")
    return response

@app.post("/api/latency")
def latency_metrics(payload: dict = Body(...)):
    regions = payload.get("regions")
    threshold = payload.get("threshold_ms")
    
    if not isinstance(regions, list) or not all(isinstance(r, str) for r in regions):
        return JSONResponse(
            status_code=400,
            content={"detail": "`regions` must be a list of strings"},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
    if not isinstance(threshold, (int, float)):
        return JSONResponse(
            status_code=400,
            content={"detail": "`threshold_ms` must be a number"},
            headers={"Access-Control-Allow-Origin": "*"}
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
    
    return JSONResponse(content=out, headers={"Access-Control-Allow-Origin": "*"})


# ✅ Healthcheck route
@app.get("/api/ping")
def ping():
    return {"msg": "pong"}

# ✅ Explicit OPTIONS handler (optional, improves compatibility with some serverless platforms)
from fastapi.responses import JSONResponse

@app.options("/api/latency")
def latency_options():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )
