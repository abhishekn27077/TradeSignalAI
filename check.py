import httpx
import sys

try:
    resp = httpx.get("http://127.0.0.1:8001/api/v1/system/status", timeout=5.0)
    print("STATUS CODE:", resp.status_code)
    print("RESPONSE:", resp.text)
except Exception as e:
    print("ERROR:", e)
