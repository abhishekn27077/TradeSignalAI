import sys
import asyncio
from app.main import app
from fastapi.testclient import TestClient

def check_backend():
    print("Testing backend startup...")
    try:
        client = TestClient(app)
        response = client.get("/api/v1/health")
        if response.status_code == 200:
            print("Backend is healthy!")
        else:
            print(f"Backend returned: {response.status_code}")
    except Exception as e:
        print(f"Backend failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_backend()
