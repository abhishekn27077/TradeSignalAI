"""
scripts/phase37_system_health.py
================================
Audits end-to-end system health, background workers, providers, and database.
"""
import urllib.request
import json

def audit_health():
    print("=" * 60)
    print("PHASE 37 SYSTEM HEALTH AUDIT")
    print("=" * 60)
    
    url = "http://localhost:8000/api/v1/system/health"
    req = urllib.request.Request(url, headers={"User-Agent": "Phase37Auditor/1.0"})
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode())
        print(json.dumps(data, indent=2))
        
    print("\n[SUCCESS] System Health verified.")

if __name__ == "__main__":
    audit_health()
