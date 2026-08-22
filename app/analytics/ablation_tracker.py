import pandas as pd
from pathlib import Path
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EVIDENCE_DIR = Path("validation_outputs")
SIGNAL_CSV = EVIDENCE_DIR / "PHASE35_SIGNAL_LEDGER.csv"
OUTCOME_CSV = EVIDENCE_DIR / "PHASE35_OUTCOME_LEDGER.csv"

class AblationTracker:
    """
    Phase 35 Ablation Tracker.
    Analyzes the 3-Way Ablation Experiment data (MODE_A, MODE_B, MODE_C).
    Zero-Trust Principle: Metrics are derived strictly from empirical evidence ledgers.
    """
    
    def __init__(self):
        EVIDENCE_DIR.mkdir(exist_ok=True)
        
    def _load_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        signals = pd.read_csv(SIGNAL_CSV) if SIGNAL_CSV.exists() else pd.DataFrame()
        outcomes = pd.read_csv(OUTCOME_CSV) if OUTCOME_CSV.exists() else pd.DataFrame()
        return signals, outcomes

    def _compute_metrics(self, outcomes_df: pd.DataFrame) -> dict:
        if outcomes_df.empty:
            return {}
            
        metrics = {}
        for mode in ["MODE_A", "MODE_B", "MODE_C"]:
            if "ablation_mode" not in outcomes_df.columns:
                metrics[mode] = {"trades": 0}
                continue
                
            mode_df = outcomes_df[outcomes_df["ablation_mode"] == mode].copy()
            if mode_df.empty:
                metrics[mode] = {"trades": 0}
                continue
                
            # Basic stats
            wins = len(mode_df[mode_df["net_pnl"] > 0])
            losses = len(mode_df[mode_df["net_pnl"] < 0])
            total = len(mode_df)
            
            # Confidence Calibration Binning (50-60, 60-70, 70-80, 80-90, 90+)
            calibration = {}
            if "confidence" in mode_df.columns:
                bins = [0, 60, 70, 80, 90, 100]
                labels = ["<60", "60-70", "70-80", "80-90", "90+"]
                mode_df["conf_bin"] = pd.cut(mode_df["confidence"], bins=bins, labels=labels, right=False)
                for bin_label in labels:
                    bin_df = mode_df[mode_df["conf_bin"] == bin_label]
                    bin_total = len(bin_df)
                    bin_wins = len(bin_df[bin_df["net_pnl"] > 0])
                    calibration[bin_label] = {
                        "trades": bin_total,
                        "win_rate": round(bin_wins / bin_total * 100, 2) if bin_total > 0 else 0
                    }
                    
            # Friday -> Monday Gap Study
            friday_monday_stats = {}
            if "generated_at" in mode_df.columns:
                # Convert to datetime to check day of week
                mode_df["day_of_week"] = pd.to_datetime(mode_df["generated_at"]).dt.dayofweek
                # 4 is Friday, 0 is Monday
                friday_trades = mode_df[mode_df["day_of_week"] == 4]
                monday_trades = mode_df[mode_df["day_of_week"] == 0]
                
                f_total = len(friday_trades)
                f_wins = len(friday_trades[friday_trades["net_pnl"] > 0])
                m_total = len(monday_trades)
                m_wins = len(monday_trades[monday_trades["net_pnl"] > 0])
                
                friday_monday_stats = {
                    "friday": {
                        "trades": f_total,
                        "win_rate": round(f_wins / f_total * 100, 2) if f_total > 0 else 0
                    },
                    "monday": {
                        "trades": m_total,
                        "win_rate": round(m_wins / m_total * 100, 2) if m_total > 0 else 0
                    }
                }
            
            metrics[mode] = {
                "trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / total * 100, 2) if total > 0 else 0,
                "total_net_pnl": round(mode_df["net_pnl"].sum(), 2),
                "total_r_multiple": round(mode_df["R"].sum(), 2) if "R" in mode_df.columns else 0.0,
                "avg_r_multiple": round(mode_df["R"].mean(), 2) if "R" in mode_df.columns and total > 0 else 0.0,
                "confidence_calibration": calibration,
                "friday_monday_study": friday_monday_stats
            }
        return metrics

    def generate_report(self, report_type: str = "daily") -> str:
        """
        Generates a summary report. Types: 'daily', 'weekly', 'final'
        """
        signals, outcomes = self._load_data()
        
        if outcomes.empty:
            return json.dumps({"status": "no_outcomes_yet"})
            
        metrics = self._compute_metrics(outcomes)
        
        report = {
            "report_type": report_type,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_signals_generated": len(signals),
            "total_outcomes_resolved": len(outcomes),
            "mode_performance": metrics
        }
        
        report_file = EVIDENCE_DIR / f"PHASE35_{report_type.upper()}_REPORT.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            logger.info(f"Generated {report_type} report: {report_file}")
            return str(report_file)
        except Exception as e:
            logger.error(f"Failed to write report: {e}")
            return str(e)
            
    def generate_daily_report(self):
        return self.generate_report("daily")
        
    def generate_weekly_report(self):
        return self.generate_report("weekly")
        
    def generate_final_certification(self):
        return self.generate_report("final")

ablation_tracker = AblationTracker()
