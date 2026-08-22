import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Important paths to hash
CRITICAL_FILES = [
    "app/analytics/feature_engine.py",
    "app/strategies/risk_engine.py",
    "app/agents/consensus/engine.py",
    "app/intelligence/faiss_memory.py",
    "app/intelligence/time_pattern.py",
    "app/intelligence/kronos.py",
    "app/intelligence/cross_market.py",
    "requirements.txt",
]

def hash_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        return "FILE_NOT_FOUND"
    
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    except Exception:
        return "UNKNOWN_OR_NOT_GIT"

def main():
    print("Freezing Phase 35 Experiment...")
    out_dir = Path("artifacts/phase35")
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "PHASE35_EXPERIMENT_MANIFEST.json"
    
    file_hashes = {}
    for f in CRITICAL_FILES:
        file_hashes[f] = hash_file(f)
        
    manifest = {
        "schema": "phase35_experiment",
        "status": "FROZEN",
        "experiment_start_time_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "python_version": sys.version,
        "os": platform.platform(),
        "hashes": file_hashes,
        "dependencies": "requirements.txt", 
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest successfully written to {manifest_path}")
    print("The experiment is now FROZEN. Any changes to critical logic will result in CONTAMINATION.")

if __name__ == "__main__":
    main()
