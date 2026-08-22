import requests
import json
import time
import os
import random
from typing import Dict, Any, List

API_URL = "http://localhost:8000"
ARTIFACT_DIR = r"C:\Users\Abhis\.gemini\antigravity-ide\brain\d1f3a00e-4c5b-494d-8d0b-14018e87107f"
REPORT_FILE = os.path.join(ARTIFACT_DIR, "api_certification_report.md")

def get_openapi_spec() -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_URL}/openapi.json")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch OpenAPI spec: {e}")
        return {}

def generate_dummy_data(schema: Dict[str, Any]) -> Any:
    if not schema:
        return {}
        
    type_map = {
        "string": "test_string",
        "integer": 1,
        "number": 1.5,
        "boolean": True,
        "array": [],
        "object": {}
    }
    
    if "type" in schema:
        if schema["type"] == "object" and "properties" in schema:
            return {k: generate_dummy_data(v) for k, v in schema["properties"].items()}
        return type_map.get(schema["type"], "unknown")
    
    # Handle $ref
    if "$ref" in schema:
        return {}
        
    return {}

def certify_endpoints():
    spec = get_openapi_spec()
    if not spec:
        return
        
    paths = spec.get("paths", {})
    results = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete"]:
                continue
                
            test_path = path
            for param in details.get("parameters", []):
                if param.get("in") == "path":
                    test_path = test_path.replace(f"{{{param['name']}}}", "1")

            url = f"{API_URL}{test_path}"
            
            payload = {}
            if method.lower() in ["post", "put"]:
                try:
                    content = details.get("requestBody", {}).get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        payload = generate_dummy_data(schema)
                except Exception:
                    pass
            
            start_time = time.time()
            status_code = 0
            error = None
            try:
                if method.lower() == "get":
                    resp = requests.get(url, timeout=10)
                elif method.lower() == "post":
                    resp = requests.post(url, json=payload, timeout=10)
                elif method.lower() == "put":
                    resp = requests.put(url, json=payload, timeout=10)
                elif method.lower() == "delete":
                    resp = requests.delete(url, timeout=10)
                
                status_code = resp.status_code
            except Exception as e:
                error = str(e)
                
            latency = (time.time() - start_time) * 1000
            
            hard_fail = status_code >= 500 or error is not None
            
            results.append({
                "method": method.upper(),
                "path": path,
                "status": status_code,
                "latency_ms": round(latency, 2),
                "hard_fail": hard_fail,
                "error": error
            })
            print(f"{method.upper()} {path} -> {status_code} ({round(latency, 2)}ms)")
            
    generate_report(results)

def generate_report(results: List[Dict[str, Any]]):
    total = len(results)
    crashes = sum(1 for r in results if r["hard_fail"])
    success = sum(1 for r in results if r["status"] < 400)
    client_errors = sum(1 for r in results if 400 <= r["status"] < 500)
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# API Certification Report\n\n")
        f.write("## Summary\n")
        f.write(f"- **Total Endpoints Tested**: {total}\n")
        f.write(f"- **2xx Success**: {success}\n")
        f.write(f"- **4xx Client Errors**: {client_errors} (Expected for invalid mock data/auth)\n")
        f.write(f"- **5xx Server Crashes (Hard Failures)**: {crashes}\n\n")
        
        f.write("## Detailed Results\n")
        f.write("| Method | Path | Status | Latency (ms) | Pass/Fail |\n")
        f.write("|--------|------|--------|--------------|-----------|\n")
        
        for r in results:
            status_badge = "✅ PASS" if not r["hard_fail"] else "❌ FAIL"
            status_text = r["status"] if not r["error"] else "ERROR"
            f.write(f"| {r['method']} | `{r['path']}` | {status_text} | {r['latency_ms']} | {status_badge} |\n")
            
if __name__ == "__main__":
    print("Starting Full API Certification...")
    time.sleep(2) # Give backend a little time if just started
    certify_endpoints()
    print(f"Report generated at: {REPORT_FILE}")
