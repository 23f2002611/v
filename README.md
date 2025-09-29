# eShopCo Latency Metrics — FastAPI on Vercel

A minimal Python/FastAPI endpoint that computes per‑region latency/uptime metrics from a bundled telemetry JSON file and enables CORS for POST requests.

## Endpoint

After deploying, your POST URL will be:

```
https://<YOUR-PROJECT>.vercel.app/api/latency
```

Send a JSON body like:

```json
{"regions": ["emea", "apac"], "threshold_ms": 187}
```

## Files

- `api/latency.py` — FastAPI app (route mounted at `/api/latency`)
- `data/telemetry.json` — sample telemetry (bundled for demo)
- `requirements.txt` — Python deps
- `vercel.json` — sets the Python runtime for Serverless Functions

## Deploy

1) Push this folder to a new GitHub repo.
2) In Vercel, click **New Project** → import that repo.
3) Keep defaults. Vercel detects Python & installs `requirements.txt`.
4) Once deployed, the function is available at `/api/latency`.

> Tip: You can also run locally with `vercel dev` if you have the Vercel CLI.
