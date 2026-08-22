"""
Phase 40 — Immutable Forecast Snapshot Model.

Every forecast produced by the system is stored as a snapshot record.
Original prediction fields are IMMUTABLE once generated.
Outcome fields (outcome, exit_price, net_pnl, etc.) are APPEND-ONLY:
they may be written once when the forecast horizon closes, but never modified.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from app.database.core import Base


class ForecastSnapshotModel(Base):
    """
    Stores every forecast snapshot across all timeframes and types.
    Designed for zero-lookahead walk-forward replay and prediction ledger.
    """

    __tablename__ = "forecast_snapshots"

    # ── Identity ────────────────────────────────────────────────────────────
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    forecast_id = Column(String(64), unique=True, index=True, nullable=False)
    trace_id = Column(String(36), index=True, nullable=True)

    # ── Classification ──────────────────────────────────────────────────────
    asset = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    forecast_type = Column(
        String(20), index=True, nullable=False
    )  # TODAY, TOMORROW, H4, SWING

    # ── Temporal Discipline (Zero Lookahead) ────────────────────────────────
    generated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    forecast_for = Column(
        DateTime(timezone=True), nullable=False
    )  # Date/time the forecast targets
    data_cutoff_timestamp = Column(
        DateTime(timezone=True), nullable=False
    )  # Latest candle included
    input_snapshot_hash = Column(
        String(64), nullable=False
    )  # SHA-256 of input data for reproducibility

    # ── Core Prediction (IMMUTABLE after generation) ────────────────────────
    direction = Column(String(10), nullable=False)  # BUY, SELL, NEUTRAL
    confidence = Column(Float, nullable=False)  # 0.0 – 1.0
    probability = Column(Float, nullable=True)  # 0.0 – 1.0
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    expected_move_pct = Column(Float, nullable=True)
    risk_reward_ratio = Column(Float, nullable=True)
    market_regime = Column(
        String(30), nullable=True
    )  # TRENDING_UP, TRENDING_DOWN, RANGEBOUND, VOLATILE

    # ── Independent Model Predictions (JSON blobs) ──────────────────────────
    quant_prediction = Column(JSON, nullable=True)
    kronos_prediction = Column(JSON, nullable=True)
    faiss_prediction = Column(JSON, nullable=True)
    time_pattern_prediction = Column(JSON, nullable=True)
    regime_prediction = Column(JSON, nullable=True)
    macro_prediction = Column(JSON, nullable=True)
    news_prediction = Column(JSON, nullable=True)
    ai_prediction = Column(JSON, nullable=True)

    # ── Consensus ───────────────────────────────────────────────────────────
    consensus_score = Column(Float, nullable=True)
    consensus_agreement_pct = Column(Float, nullable=True)
    models_contributing = Column(Integer, default=0)
    consensus_breakdown = Column(JSON, nullable=True)

    # ── Event & Scenario Risk ───────────────────────────────────────────────
    event_risk = Column(
        String(20), nullable=True
    )  # NONE, LOW, MEDIUM, HIGH, EXTREME
    upcoming_events = Column(JSON, nullable=True)
    scenarios = Column(
        JSON, nullable=True
    )  # { HOT: {...}, IN_LINE: {...}, COOL: {...} }

    # ── Trade Signal Qualification ──────────────────────────────────────────
    is_trade_signal_qualified = Column(Boolean, default=False)
    trade_signal_decision = Column(
        String(20), nullable=True
    )  # TAKE_NOW, NO_TRADE
    trade_disqualification_reason = Column(
        String(100), nullable=True
    )  # CONSENSUS_BELOW_THRESHOLD, INSUFFICIENT_RR, etc.

    # ── AI Reasoning ────────────────────────────────────────────────────────
    ai_reasoning = Column(Text, nullable=True)
    key_factors = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    invalidation_levels = Column(JSON, nullable=True)

    # ── Append-Only Outcome Fields (written ONCE after horizon closes) ──────
    outcome = Column(
        String(20), nullable=True
    )  # CORRECT, WRONG, TP_HIT, SL_HIT, TIME_EXIT, AMBIGUOUS
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    actual_move_pct = Column(Float, nullable=True)
    directional_correct = Column(Boolean, nullable=True)

    gross_pnl = Column(Float, nullable=True)
    spread_cost = Column(Float, nullable=True)
    slippage_cost = Column(Float, nullable=True)
    broker_fee = Column(Float, nullable=True)
    net_pnl = Column(Float, nullable=True)
    r_multiple = Column(Float, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    # ── Composite Indexes ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_fs_asset_type_date", "asset", "forecast_type", "generated_at"),
        Index("ix_fs_type_date", "forecast_type", "generated_at"),
    )

    def __repr__(self):
        return (
            f"<ForecastSnapshot {self.asset} {self.forecast_type} "
            f"{self.direction} {self.confidence:.0%} @ {self.generated_at}>"
        )

    @staticmethod
    def compute_input_hash(data: dict) -> str:
        """Deterministic SHA-256 of input data for reproducibility verification."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
