import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.analytics.ablation_tracker import ablation_tracker
from app.logs.logger import get_logger

logger = get_logger("phase35_weekly_report")

def main():
    logger.info("Generating Phase 35 Weekly Report...")
    report_path = ablation_tracker.generate_weekly_report()
    print(f"\n========================================================")
    print(f"Phase 35 Weekly Report generated successfully.")
    print(f"Location: {report_path}")
    print(f"========================================================")

if __name__ == "__main__":
    main()
