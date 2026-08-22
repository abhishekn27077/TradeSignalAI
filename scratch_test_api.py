import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

endpoints_to_test = [
    "/system/health",
    "/market/symbols",
    "/agents/status",
    "/strategies/active",
    "/signals/live",
    "/news/latest",
    "/backtest/history",
    "/paper/account",
    "/journal/entries",
    "/memory/status",
    "/risk/metrics",
    "/portfolio/summary",
    "/execution/status",
    "/brokers/status",
    "/analytics/summary",
    "/forecast/scanners/status",
    "/forecast/outlook",
    "/forecast/heatmap/current",
    "/research/reports",
    "/decision/logs",
    "/validation/reports"
]

results = {"passed": [], "failed": [], "unreachable": []}

print(f"Testing {len(endpoints_to_test)} API endpoints...")

for endpoint in endpoints_to_test:
    url = f"{BASE_URL}{endpoint}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            if status < 400:
                results["passed"].append(endpoint)
                print(f"[OK] {endpoint} ({status})")
            else:
                results["failed"].append((endpoint, status))
                print(f"[FAILED] {endpoint} ({status})")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            results["unreachable"].append(endpoint)
            print(f"[404] {endpoint}")
        else:
            results["failed"].append((endpoint, e.code))
            print(f"[FAILED] {endpoint} ({e.code})")
    except Exception as e:
        results["unreachable"].append(endpoint)
        print(f"[ERROR] {endpoint} - {e}")
    time.sleep(0.1)

print("\n--- Summary ---")
print(f"Passed: {len(results['passed'])}")
print(f"Failed: {len(results['failed'])}")
print(f"Unreachable/404: {len(results['unreachable'])}")

with open("api_test_report.json", "w") as f:
    json.dump(results, f, indent=2)
