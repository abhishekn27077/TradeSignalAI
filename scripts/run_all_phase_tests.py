"""
Phase 47 — Comprehensive Multi-Phase Pytest Regression Runner.
Discovers and executes all test suites from Phase 40 through Phase 47.
"""
import os
import glob
import subprocess
import sys

def run_tests():
    test_files = []
    for phase in range(40, 49):
        matches = glob.glob(f"tests/test_phase{phase}*.py")
        test_files.extend(matches)

    test_files = sorted(list(set(test_files)))
    print(f"Discovered {len(test_files)} test files across Phases 40-48:")
    for tf in test_files:
        print(f"  - {tf}")

    cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v"]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    run_tests()
