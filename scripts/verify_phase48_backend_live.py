"""
Phase 48 — Live Backend Process & HTTP Endpoint Verification.

Sends real HTTP requests to the running Uvicorn server on http://127.0.0.1:8000.
Tests:
  - GET http://127.0.0.1:8000/health
  - GET http://127.0.0.1:8000/api/v1/system/health
  - GET http://127.0.0.1:8000/api/v1/runtime/diagnostics
  - GET http://127.0.0.1:8000/api/v1/live/today
  - GET http://127.0.0.1:8000/api/v1/signals/h4-intelligence
Saves artifacts/phase48/BACKEND_LIVE_VERIFICATION.json
"""
import time
import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def verify_live_backend():
    print(f"[Phase 48] Connecting to Live Backend Process at {BASE_URL}...")
    results = {}

    endpoints = [
        {"name": "root_health", "path": "/health", "method": "GET"},
        {"name": "system_health", "path": "/api/v1/system/health", "method": "GET"},
        {"name": "runtime_diagnostics", "path": "/api/v1/runtime/diagnostics", "method": "GET"},
        {"name": "live_today", "path": "/api/v1/live/today", "method": "GET"},
        {"name": "h4_intelligence", "path": "/api/v1/signals/h4-intelligence", "method": "GET"},
    ]

    for ep in endpoints:
        url = f"{BASE_URL}{ep['path']}"
        t0 = time.time()
        try:
            res = requests.get(url, timeout=15)
            latency_ms = round((time.time() - t0) * 1000, 2)
            results[ep["name"]] = {
                "url": url,
                "status_code": res.status_code,
                "latency_ms": latency_ms,
                "response_json": res.json() if res.status_code == 200 else res.text,
                "is_reachable": True,
            }
            print(f"  [OK] {ep['name']} -> HTTP {res.status_code} in {latency_ms}ms")
        except Exception as e:
            results[ep["name"]] = {
                "url": url,
                "status_code": None,
                "latency_ms": None,
                "error": str(e),
                "is_reachable": False,
            }
            print(f"  [FAIL] {ep['name']} -> Error: {e}")

    out_dir = "artifacts/phase48"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "BACKEND_LIVE_VERIFICATION.json")

    with open(out_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "target_host": BASE_URL,
            "all_endpoints_reachable": all(r.get("is_reachable") for r in results.values()),
            "endpoints": results,
        }, f, indent=2)

    print(f"[Phase 48] Backend Live Verification saved to {out_file}")
    return results

if __name__ == "__main__":
    verify_live_backend()
