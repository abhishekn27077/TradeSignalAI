import os
import pandas as pd
from datetime import datetime

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.logs.logger import get_logger

logger = get_logger("phase29_friday_monday")

ARTIFACTS_DIR = r"C:\Users\Abhis\.gemini\antigravity-ide\brain\d1f3a00e-4c5b-494d-8d0b-14018e87107f"
FM_TRACKER_PATH = os.path.join(ARTIFACTS_DIR, "PHASE29_FRIDAY_MONDAY_TRACKER.csv")

class FridayMondayStudy:
    def __init__(self):
        pass

    def _ensure_csv(self):
        if not os.path.exists(FM_TRACKER_PATH):
            pd.DataFrame(columns=[
                "asset", "friday_close", "weekend_gap", "monday_open", "monday_direction"
            ]).to_csv(FM_TRACKER_PATH, index=False)

    def generate_report(self):
        """
        Creates the Phase 29 Friday-Monday statistical report.
        """
        self._ensure_csv()
        df = pd.read_csv(FM_TRACKER_PATH)
        
        sample_count = len(df)
        
        report = f"""# PHASE 29.3: FRIDAY-MONDAY MARKET STUDY

> [!WARNING]
> **CURRENT STATUS: INSUFFICIENT DATA**
> This report requires significantly more weekend transitions to establish statistical significance.

## Executive Summary
This study mathematically determines if a Friday close direction has a statistically reliable relationship with the Monday open/direction across Forex, Crypto, Indices, and Gold.

## 1. Sample Size
- Total Transitions Observed: **{sample_count}**

## 2. Statistical Analysis
- Directional Agreement Rate: **PENDING**
- Gap Statistics (Average): **PENDING**
- Confidence Interval: **PENDING**
- p-value: **PENDING**

## 3. FINAL VERDICT
**INSUFFICIENT DATA**
Do NOT assume Friday predicts Monday. The system will continue to collect observations until a reliable edge is proven or disproven.
"""
        report_path = os.path.join(ARTIFACTS_DIR, "PHASE29_3_FRIDAY_MONDAY_REPORT.md")
        with open(report_path, "w") as f:
            f.write(report)
        logger.info(f"Generated {report_path}")

    def run(self):
        logger.info("Running Phase 29.3 Friday-Monday Study Engine")
        self.generate_report()
        logger.info("Friday-Monday study complete.")

if __name__ == "__main__":
    study = FridayMondayStudy()
    study.run()
