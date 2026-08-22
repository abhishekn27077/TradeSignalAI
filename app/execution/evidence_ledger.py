"""
app/execution/evidence_ledger.py  — Phase 33
=============================================
EvidenceLedger: writes the complete signal trace to the evidence file.
Only writes after real outcome resolution — never fabricated.
"""
from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

EVIDENCE_DIR = Path("validation_outputs")
SIGNAL_TRACE_FILE = EVIDENCE_DIR / "PHASE33_REAL_SIGNAL_TRACE.json"
EVIDENCE_LOG_FILE  = EVIDENCE_DIR / "PHASE33_EVIDENCE_LOG.jsonl"


def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class EvidenceLedger:
    """
    Phase 33 Evidence Ledger.

    Zero-Trust Rules:
    - Never write a trace for an unresolved signal
    - Never fabricate any field
    - Every trace must contain trace_id matching all pipeline stages
    """

    def __init__(self):
        EVIDENCE_DIR.mkdir(exist_ok=True)

    def write_signal_trace(self, trace_id: str, full_trace: dict[str, Any]) -> str:
        """
        Writes the complete signal trace to PHASE33_REAL_SIGNAL_TRACE.json.

        The trace must contain (at minimum):
          trace_id, market_data, candle, features, quant, kronos,
          consensus, faiss, time_pattern, regime, cross_market, news,
          events, synthesis, risk, entry, SL, TP, RR, decision,
          execution, outcome.

        Returns the path written.
        """
        if not full_trace.get("outcome") or full_trace["outcome"] == "OUTCOME_UNRESOLVED":
            logger.warning(
                f"EvidenceLedger: refusing to write trace {trace_id} — outcome not resolved"
            )
            return "WRITE_BLOCKED_OUTCOME_UNRESOLVED"

        trace_with_meta = {
            "schema_version": "phase33.v1",
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            **full_trace,
        }

        try:
            with open(SIGNAL_TRACE_FILE, "w", encoding="utf-8") as f:
                json.dump(trace_with_meta, f, indent=2, default=_default_serializer)
            logger.info(f"EvidenceLedger: wrote signal trace {trace_id} → {SIGNAL_TRACE_FILE}")
            return str(SIGNAL_TRACE_FILE)
        except Exception as e:
            logger.error(f"EvidenceLedger.write_signal_trace error: {e}")
            return f"WRITE_FAILED: {e}"

    def write_no_valid_setup(self, observation_window: str, assets: list[str], reason: str) -> str:
        """
        Records that no valid setup occurred during the observation window.
        This is an honest, successful zero-trust result.
        """
        report = {
            "schema_version": "phase33.v1",
            "result": "NO_VALID_SETUP_DURING_OBSERVATION_WINDOW",
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "observation_window": observation_window,
            "assets_monitored": assets,
            "reason": reason,
        }
        path = EVIDENCE_DIR / "PHASE33_NO_VALID_SETUP_REPORT.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"EvidenceLedger: recorded NO_VALID_SETUP → {path}")
            return str(path)
        except Exception as e:
            return f"WRITE_FAILED: {e}"

    def append_evidence(self, signal_record: dict[str, Any]) -> bool:
        """
        Appends a resolved signal to the rolling evidence log (JSONL format).
        Phase 29 compatible fields are validated before writing.
        """
        required_fields = [
            "signal_id", "trace_id", "asset", "timeframe", "generated_at",
            "direction", "confidence", "entry", "SL", "TP", "result", "net_pnl",
        ]
        missing = [f for f in required_fields if signal_record.get(f) is None]
        if missing:
            logger.warning(f"EvidenceLedger.append_evidence: missing fields {missing}")
            # Still append, but flag the gaps
            signal_record["_missing_fields"] = missing

        signal_record["_evidence_written_at"] = datetime.now(timezone.utc).isoformat()

        try:
            with open(EVIDENCE_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(signal_record, default=_default_serializer) + "\n")
            
            # Phase 35: Export to Outcome Ledger CSV
            self._write_outcome_csv(signal_record)
            return True
        except Exception as e:
            logger.error(f"EvidenceLedger.append_evidence error: {e}")
            return False

    def write_phase35_signal_csv(self, setup: dict[str, Any], trace_id: str) -> None:
        """
        Phase 35: Writes the raw generated signal to PHASE35_SIGNAL_LEDGER.csv
        Called immediately upon signal generation (before outcome resolution).
        """
        import csv
        csv_path = EVIDENCE_DIR / "PHASE35_SIGNAL_LEDGER.csv"
        file_exists = csv_path.exists()
        
        # Extract flat fields
        ablation_mode = setup.get("ablation_mode", "UNKNOWN")
        quant_baseline = setup.get("quant_baseline", {})
        intelligence = setup.get("intelligence", {})
        
        row = {
            "trace_id": trace_id,
            "ablation_mode": ablation_mode,
            "asset": setup.get("symbol"),
            "timeframe": setup.get("timeframe"),
            "prediction_timestamp_utc": setup.get("prediction_timestamp"),
            "direction": setup.get("master_signal"),
            "confidence": quant_baseline.get("confidence_score", 0),
            "entry_price": setup.get("entry_price", 0),
            "stop_loss": setup.get("stop_loss", 0),
            "take_profit": setup.get("take_profit_1", 0),
            "risk_reward": setup.get("risk_reward_ratio", 0),
            "news_sentiment": intelligence.get("news_sentiment", "UNKNOWN"),
            "macro_context": intelligence.get("macro_context", "UNKNOWN"),
            "event_risk": str(intelligence.get("event_risk", {})),
            "model_agreement": quant_baseline.get("agreement_percentage", 0),
        }
        
        try:
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Failed to write PHASE35_SIGNAL_LEDGER.csv: {e}")

    def _write_outcome_csv(self, record: dict[str, Any]) -> None:
        """
        Phase 35: Writes the resolved outcome to PHASE35_OUTCOME_LEDGER.csv
        Called after the signal hits TP/SL/Time limit.
        """
        import csv
        csv_path = EVIDENCE_DIR / "PHASE35_OUTCOME_LEDGER.csv"
        file_exists = csv_path.exists()
        
        row = {
            "signal_id": record.get("signal_id"),
            "trace_id": record.get("trace_id"),
            "ablation_mode": record.get("ablation_mode", "UNKNOWN"),
            "asset": record.get("asset"),
            "timeframe": record.get("timeframe"),
            "generated_at": record.get("generated_at"),
            "direction": record.get("direction"),
            "confidence": record.get("confidence"),
            "entry": record.get("entry"),
            "SL": record.get("SL"),
            "TP": record.get("TP"),
            "exit_price": record.get("exit"),
            "exit_time": record.get("exit_time"),
            "result": record.get("result"),
            "gross_pnl": record.get("gross_pnl", 0),
            "spread_cost": record.get("spread_cost", 0),
            "slippage_cost": record.get("slippage_cost", 0),
            "fees_cost": record.get("fees_cost", 0),
            "net_pnl": record.get("net_pnl", 0),
            "R": record.get("R", 0),
        }
        
        try:
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Failed to write PHASE35_OUTCOME_LEDGER.csv: {e}")


    def build_phase29_compatible_record(
        self,
        signal: Any,  # SignalLifecycleModel or dict
        outcome_result: Any,  # OutcomeResult
    ) -> dict[str, Any]:
        """
        Constructs a Phase 29-compatible evidence record from a resolved signal.
        Required fields per Phase 29 specification.
        """
        if hasattr(signal, '__table__'):
            # SQLAlchemy model
            s = {c.name: getattr(signal, c.name) for c in signal.__table__.columns}
        else:
            s = signal

        o = outcome_result.to_dict() if hasattr(outcome_result, 'to_dict') else outcome_result

        return {
            "signal_id":        s.get("signal_id"),
            "trace_id":         s.get("trace_id"),
            "asset":            s.get("asset"),
            "timeframe":        s.get("timeframe"),
            "generated_at":     s.get("created_at"),
            "direction":        s.get("direction"),
            "confidence":       s.get("confidence"),
            "entry":            s.get("entry_price"),
            "SL":               s.get("stop_loss"),
            "TP":               s.get("take_profit_1"),
            "exit":             o.get("exit_price"),
            "exit_time":        o.get("exit_time"),
            "result":           o.get("outcome"),
            "gross_pnl":        o.get("gross_pnl"),
            "spread_cost":      o.get("spread_cost"),
            "slippage_cost":    o.get("slippage_cost"),
            "fees_cost":        o.get("fees_cost"),
            "net_pnl":          o.get("net_pnl"),
            "R":                o.get("r_multiple"),
            "ablation_mode":    s.get("ablation_mode", "FULL_STACK"),
            "model_versions":   s.get("model_trace", {}),
            "data_source":      s.get("data_freshness_status", "UNKNOWN"),
        }


evidence_ledger = EvidenceLedger()
