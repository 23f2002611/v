from fastapi import FastAPI, Body, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from statistics import mean
import math

app = FastAPI(title="eShopCo Latency Metrics")

# ======================
# Load telemetry data
# ======================
DATA_PATH = Path(__file__).resolve().parent / "data" / "telemetry.json"
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
# Global CORS + debug middleware
# ======================
@app.middleware("http")
async def add_cors_and_debug(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        response = JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )
    # Force CORS headers on all responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

    # Debug log
    print(f"[DEBUG] {request.method} {request.url.path} headers={response.headers}")

    return response

# ======================
# Latency POST endpoint
# ======================
@app.post("/api/latency")
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
# Healthcheck GET
# ======================
@app.get("/api/ping")
def ping():
    return JSONResponse(content={"msg": "pong"})

# ======================
# OPTIONS preflight handler for all paths
# ======================
@app.options("/{rest_of_path:path}")
async def options_handler(rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# ======================
# Favicon route to prevent portal CORS errors
# ======================
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204, headers={"Access-Control-Allow-Origin": "*"})
