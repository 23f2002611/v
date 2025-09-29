# Deploy Notes (Python on Vercel)

**Fix:** Remove `vercel.json`. The Python runtime is auto-detected from `.py` files in `/api`.
Do not set `"functions": {"api/**/*.py": {"runtime": "python3.xx"}}` — that triggers the
legacy "now-php@1.0.0" runtime-version error.

Structure:
- `api/latency.py` (ASGI `app` is auto-detected)
- `requirements.txt` (FastAPI dependency)
- `data/telemetry.json` (sample bundle)

After pushing to GitHub, Vercel will deploy the function at:
`https://<your-project>.vercel.app/api/latency`
