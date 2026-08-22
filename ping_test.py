import urllib.request
import json

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read().decode('utf-8')
            print(f"--- SUCCESS: {url} ---")
            print(content[:500])
    except Exception as e:
        print(f"--- ERROR: {url} ---")
        print(e)

if __name__ == "__main__":
    fetch("http://localhost:8000/docs")
    fetch("http://localhost:8000/api/v1/forecast/predictions/current")
    fetch("http://localhost:3000")
