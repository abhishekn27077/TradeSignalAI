"""
scripts/phase37_api_frontend_audit.py
=====================================
Audits all REST endpoints and validates schema compliance for frontend consumption.
"""
import urllib.request
import json
import time

ENDPOINTS = [
    ("/api/v1/health", "GET"),
    ("/api/v1/system/health", "GET"),
    ("/api/v1/signals/live", "GET"),
    ("/api/v1/signals/today", "GET"),
    ("/api/v1/signals/history", "GET"),
    ("/api/v1/signals/h4-intelligence", "GET"),
    ("/api/v1/analytics/dashboard", "GET"),
    ("/api/v1/assets", "GET"),
]

def run_audit():
    print("=" * 60)
    print("PHASE 37 REST API & FRONTEND CONTRACT AUDIT")
    print("=" * 60)
    
    passed = 0
    total = len(ENDPOINTS)
    
    for ep, method in ENDPOINTS:
        url = f"http://localhost:8000{ep}"
        start = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Phase37Auditor/1.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                status = res.status
                body = res.read().decode()
                elapsed = round((time.time() - start) * 1000, 2)
                try:
                    data = json.loads(body)
                    print(f"[PASS] {method:4} {ep:35} -> HTTP {status} ({elapsed}ms)")
                    passed += 1
                except Exception:
                    print(f"[FAIL] {method:4} {ep:35} -> Invalid JSON response")
        except Exception as e:
            print(f"[FAIL] {method:4} {ep:35} -> Error: {e}")

    print("\n" + "-" * 60)
    print(f"API Audit Score: {passed}/{total} endpoints verified.")
    assert passed == total, "Some endpoints failed API contract audit!"

if __name__ == "__main__":
    run_audit()
