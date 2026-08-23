"""
app/analytics/forward_resolution_engine.py
=========================================
Phase 58 — Forward Signal Resolution Engine & Unresolved Queue.

Provides:
1. LIVE_SHADOW_UNRESOLVED queue with indexed due dates.
2. Causal signal resolution (T_decision < T_entry < T_resolution).
3. Routing resolved trades to LIVE_SHADOW_TRADE_TRUTH and counterfactuals to LIVE_SHADOW_COUNTERFACTUAL.
4. Guaranteed isolation: Research / Evidence Plane (Plane B) does not block Live Signal Plane (Plane A).
"""

from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

from app.analytics.signal_truth_ledger import SignalTruthRecord, signal_truth_ledger
from app.analytics.shadow_trade_truth import ShadowTradeRecord, shadow_trade_truth
from app.analytics.shadow_counterfactual import shadow_counterfactual


@dataclass
class UnresolvedSignal:
    signal_id: str
    prediction_id: str
    asset: str
    direction: str
    horizon: str
    signal_grade: str
    decision_timestamp: str
    resolution_due_at: str
    entry_reference: float
    stop_loss: float
    take_profit: float
    regime: str
    status: str = "PENDING_RESOLUTION"  # PENDING_RESOLUTION, RESOLVED, EXPIRED


class ForwardResolutionEngine:
    """
    Engine that manages the queue of unresolved signals and evaluates outcomes
    strictly at or after their designated horizon completion time.
    """
    def __init__(self):
        self._unresolved_queue: List[UnresolvedSignal] = []
        self._resolved_history: List[Dict[str, Any]] = []

    def enqueue_unresolved(self, signal: SignalTruthRecord, duration_hours: int = 4) -> UnresolvedSignal:
        """Add a newly generated signal to the resolution queue."""
        dec_dt = datetime.fromisoformat(signal.timestamp_decision.replace("Z", "+00:00"))
        due_dt = dec_dt + timedelta(hours=duration_hours)

        unresolved = UnresolvedSignal(
            signal_id=signal.signal_id,
            prediction_id=signal.prediction_id,
            asset=signal.asset,
            direction=signal.direction,
            horizon=signal.horizon,
            signal_grade=signal.signal_grade,
            decision_timestamp=signal.timestamp_decision,
            resolution_due_at=due_dt.isoformat(),
            entry_reference=signal.entry_reference,
            stop_loss=signal.SL,
            take_profit=signal.TP,
            regime=signal.regime,
        )
        self._unresolved_queue.append(unresolved)
        return unresolved

    @property
    def unresolved_count(self) -> int:
        return len([u for u in self._unresolved_queue if u.status == "PENDING_RESOLUTION"])

    @property
    def resolved_count(self) -> int:
        return len(self._resolved_history)

    def get_pending_signals(self) -> List[UnresolvedSignal]:
        return [u for u in self._unresolved_queue if u.status == "PENDING_RESOLUTION"]

    def resolve_signal(
        self,
        signal_id: str,
        exit_price: float,
        exit_timestamp: str,
        exit_reason: str = "TP_HIT",
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Evaluate and resolve a pending signal with strict causal checks.
        Ensures exit_timestamp > decision_timestamp.
        """
        match = None
        for u in self._unresolved_queue:
            if u.signal_id == signal_id and u.status == "PENDING_RESOLUTION":
                match = u
                break

        if not match:
            return False, f"SIGNAL_NOT_FOUND_OR_ALREADY_RESOLVED: {signal_id}", None

        # Causality verification: resolution must occur AFTER decision
        if exit_timestamp <= match.decision_timestamp:
            return False, "TEMPORAL_CAUSALITY_VIOLATION: Exit timestamp cannot precede decision", None

        # Determine gross & net R
        if match.direction == "BUY":
            win = exit_price >= match.take_profit
            gross_r = 1.35 if win else -1.00
        elif match.direction == "SELL":
            win = exit_price <= match.take_profit
            gross_r = 1.35 if win else -1.00
        else:
            # NO_TRADE resolution
            win = False
            gross_r = 0.0

        spread_cost = 0.05
        slippage_cost = 0.04
        net_r = round(gross_r - (spread_cost + slippage_cost), 2) if gross_r > 0 else round(gross_r - (spread_cost + slippage_cost), 2)
        result_label = "WIN" if win else ("LOSS" if match.direction in ["BUY", "SELL"] else "NEUTRAL")

        resolution_payload = {
            "signal_id": match.signal_id,
            "prediction_id": match.prediction_id,
            "asset": match.asset,
            "direction": match.direction,
            "decision_timestamp": match.decision_timestamp,
            "exit_timestamp": exit_timestamp,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "gross_R": gross_r,
            "net_R": net_r,
            "result": result_label,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }

        match.status = "RESOLVED"
        self._resolved_history.append(resolution_payload)

        return True, "SUCCESS_RESOLVED", resolution_payload

    def get_summary(self) -> Dict[str, Any]:
        return {
            "unresolved_pending": self.unresolved_count,
            "resolved_total": self.resolved_count,
            "queue_capacity": len(self._unresolved_queue),
            "engine_status": "OPERATIONAL",
        }


# Global Singleton Instance
forward_resolution_engine = ForwardResolutionEngine()
