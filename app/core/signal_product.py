"""
app/core/signal_product.py
==========================
Formal Signal Product & Lifecycle Model for TradeSignalAI-v3 (Phase 64).

Defines the immutable canonical signal representation, lifecycle state machine,
and execution cost attribution according to zero-trust causal quantitative standards.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import uuid
from enum import Enum


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


class SignalQualityTier(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    WATCH = "WATCH"
    REJECTED = "REJECTED"


class SignalLifecycleStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    QUALIFIED = "QUALIFIED"
    PUBLISHED = "PUBLISHED"
    ACTIVE = "ACTIVE"
    RESOLVING = "RESOLVING"
    WON = "WON"
    LOST = "LOST"
    TIME_EXIT = "TIME_EXIT"
    AMBIGUOUS = "AMBIGUOUS"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class CausalViolationError(Exception):
    """Raised when an attempt is made to evaluate or inject data timestamped after T0."""
    pass


@dataclass(frozen=True)
class SignalProduct:
    """
    Formal immutable Signal Product Model.
    All attributes are time-locked and tamper-evident.
    """
    signal_id: str
    asset: str
    asset_class: str  # "FX", "CRYPTO", "INDICES", "COMMODITIES"
    direction: str    # "BUY", "SELL", "WAIT"
    timeframe: str    # "5m", "15m", "30m", "1H", "2H", "4H", "12H", "1D", "SWING"
    signal_scope: str # "INTRADAY", "SWING", "SCALP"
    created_at: str   # ISO 8601 UTC (Immutable generation timestamp)
    data_cutoff_time: str # ISO 8601 UTC (T0 barrier)
    entry_price: float
    stop_loss: float
    take_profit: float
    expiry_time: str
    expected_hold_time: str

    confidence: float
    calibrated_probability: float
    agreement_percentage: float

    quality_tier: str  # "A+", "A", "B", "C", "WATCH", "REJECTED"
    expected_net_r: float

    spread_cost: float
    slippage_cost: float
    fee_cost: float

    market_regime: str
    volatility_regime: str
    session: str
    event_risk: str

    mtf_alignment_score: float
    mtf_conflict_score: float

    contributing_models: List[str]
    excluded_models: List[str]
    model_weights: Dict[str, float]

    indicator_evidence: Dict[str, Any]
    tradingview_evidence: Dict[str, Any]
    historical_analogue_evidence: Dict[str, Any]

    decision_trace: Dict[str, Any]

    snapshot_id: str
    snapshot_content_hash: str
    git_commit: str
    config_hash: str
    engine_version: str

    status: str  # SignalLifecycleStatus
    outcome: Optional[str] = None
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    realized_r: Optional[float] = None
    net_pnl: Optional[float] = None
    display_signal_type: Optional[str] = None  # "CALL", "PUT", "BUY", "SELL"

    def __post_init__(self):
        # Validate causal barrier
        created_dt = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        cutoff_dt = datetime.fromisoformat(self.data_cutoff_time.replace("Z", "+00:00"))
        if cutoff_dt > created_dt + timedelta(seconds=1.0):
            raise CausalViolationError(
                f"Causal barrier violated: data_cutoff_time ({self.data_cutoff_time}) cannot be in future of created_at ({self.created_at})"
            )

    @property
    def risk_reward(self) -> float:
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)
        return round(reward / risk, 2) if risk > 0 else 0.0

    @property
    def telegram_display_text(self) -> str:
        """Returns Telegram-style formatted single-line display representation."""
        call_put = "CALL" if self.direction == "BUY" else ("PUT" if self.direction == "SELL" else "WAIT")
        time_str = self.created_at[11:16] if len(self.created_at) >= 16 else self.created_at
        status_badge = "✓" if self.outcome == "WON" else ("✕" if self.outcome == "LOST" else ("•" if self.status == "ACTIVE" else "○"))
        r_str = f"{self.realized_r:+.1f}R" if self.realized_r is not None else ""
        return f"{time_str} {call_put} {self.quality_tier} {int(self.calibrated_probability * 100)}% {status_badge} {r_str}".strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "asset": self.asset,
            "asset_class": self.asset_class,
            "direction": self.direction,
            "display_signal_type": self.display_signal_type or ("CALL" if self.direction == "BUY" else ("PUT" if self.direction == "SELL" else "WAIT")),
            "timeframe": self.timeframe,
            "signal_scope": self.signal_scope,
            "created_at": self.created_at,
            "data_cutoff_time": self.data_cutoff_time,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward": self.risk_reward,
            "expiry_time": self.expiry_time,
            "expected_hold_time": self.expected_hold_time,
            "confidence": round(self.confidence, 4),
            "calibrated_probability": round(self.calibrated_probability, 4),
            "agreement_percentage": round(self.agreement_percentage, 1),
            "quality_tier": self.quality_tier,
            "expected_net_r": round(self.expected_net_r, 4),
            "spread_cost": self.spread_cost,
            "slippage_cost": self.slippage_cost,
            "fee_cost": self.fee_cost,
            "market_regime": self.market_regime,
            "volatility_regime": self.volatility_regime,
            "session": self.session,
            "event_risk": self.event_risk,
            "mtf_alignment_score": round(self.mtf_alignment_score, 2),
            "mtf_conflict_score": round(self.mtf_conflict_score, 2),
            "contributing_models": self.contributing_models,
            "excluded_models": self.excluded_models,
            "model_weights": self.model_weights,
            "indicator_evidence": self.indicator_evidence,
            "tradingview_evidence": self.tradingview_evidence,
            "historical_analogue_evidence": self.historical_analogue_evidence,
            "decision_trace": self.decision_trace,
            "snapshot_id": self.snapshot_id,
            "snapshot_content_hash": self.snapshot_content_hash,
            "git_commit": self.git_commit,
            "config_hash": self.config_hash,
            "engine_version": self.engine_version,
            "status": self.status,
            "outcome": self.outcome,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time,
            "realized_r": self.realized_r,
            "net_pnl": self.net_pnl,
            "telegram_display": self.telegram_display_text,
        }
