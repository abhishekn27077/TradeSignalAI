"""
PHASE 16 — MASTER ORCHESTRATOR
Runs all experiments in sequence after verifying each .done sentinel.
Usage: python scripts/phase16_orchestrate.py
"""
import subprocess
import os
import sys
import time
from datetime import datetime

SCRIPTS_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ROOT  = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "validation_outputs"))
PYTHON       = sys.executable
ENV          = {**os.environ, "PYTHONIOENCODING": "utf-8"}

EXPERIMENTS = [
    # (script_name, done_sentinel_relative_to_OUTPUT_ROOT)
    ("phase16_ablation_engine.py",              "ablation/phase16_ablation_engine.done"),
    ("phase16_memory_ablation.py",              "memory_ablation/phase16_memory_ablation.done"),
    ("phase16_analytics.py",                    "phase16_exp4.done"),
    ("phase16_live_validation.py",              "live_validation/phase16_live_validation.done"),
    ("phase16_market_source_verification.py",   "market_source/phase16_market_source_verification.done"),
    ("phase16_final_test.py",                   "final_test/phase16_final_test.done"),
    ("phase16_final_report.py",                 "phase16_final_report.done"),
]


def run_experiment(script_name: str, done_path: str):
    full_done = os.path.join(OUTPUT_ROOT, done_path)
    script    = os.path.join(SCRIPTS_DIR, script_name)
    project   = os.path.abspath(os.path.join(SCRIPTS_DIR, ".."))

    if os.path.exists(full_done):
        print(f"  [SKIP] {script_name} already done ({full_done})")
        return True

    print(f"\n{'='*60}")
    print(f"[RUN ] {script_name}")
    print(f"  Started: {datetime.now().strftime('%H:%M:%S IST')}")
    print(f"{'='*60}")

    result = subprocess.run(
        [PYTHON, script],
        cwd=project,
        env=ENV,
        capture_output=False,  # stream to console
        text=True,
    )

    if result.returncode != 0:
        print(f"\n[ERROR] {script_name} exited with code {result.returncode}")
        return False

    if os.path.exists(full_done):
        print(f"\n[OK] {script_name} completed.")
        return True
    else:
        print(f"\n[WARN] {script_name} returned 0 but done sentinel not found: {full_done}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("PHASE 16 — MASTER ORCHESTRATOR")
    print(f"Started: {datetime.now()}")
    print("="*60)

    # Wait for swing engine to finish first
    swing_done = os.path.join(OUTPUT_ROOT, "swing", "phase16_swing_engine.done")
    if not os.path.exists(swing_done):
        print("\n[WAIT] Swing engine is still running. Waiting for it to complete...")
        while not os.path.exists(swing_done):
            time.sleep(15)
            print("  ... still waiting for swing engine ...", flush=True)
        print("[OK] Swing engine done.")
    else:
        print("[OK] Swing engine already done.")

    # Run remaining experiments
    failed = []
    for script_name, done_path in EXPERIMENTS:
        ok = run_experiment(script_name, done_path)
        if not ok:
            failed.append(script_name)
            print(f"[WARNING] Continuing despite failure in {script_name}")

    print("\n" + "="*60)
    print("ORCHESTRATOR COMPLETE")
    if failed:
        print(f"FAILED experiments: {failed}")
    else:
        print("All experiments completed successfully.")
    print(f"Final report: {os.path.abspath(os.path.join(SCRIPTS_DIR, '..', 'PHASE16_COMPLETE_INTELLIGENCE_REPORT.md'))}")
    print("="*60)
