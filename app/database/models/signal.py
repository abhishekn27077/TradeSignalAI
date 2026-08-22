import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from app.database.core import Base


class SignalLifecycleModel(Base):
    """
    Tracks the full lifecycle of a signal across the platform.
    Phase 33: Extended with trace_id, candle discipline, outcome, PnL, and evidence fields.
    """
    __tablename__ = "signal_lifecycle"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(100), unique=True, index=True, nullable=False)

    # ── Phase 33: Traceability ───────────────────────────────────────────────
    trace_id = Column(String(36), index=True, nullable=True)  # UUID propagated through all stages
    duplicate_protection_hash = Column(String(64), unique=True, nullable=True, index=True)  # SHA-256

    # ── Phase 33: Candle Discipline ──────────────────────────────────────────
    candle_timestamp = Column(DateTime(timezone=True), nullable=True)      # Closed candle used
    prediction_timestamp = Column(DateTime(timezone=True), nullable=True)  # Exact moment of evaluation
    data_age_seconds = Column(Float, nullable=True)
    data_freshness_status = Column(String(20), nullable=True)  # FRESH | DATA_STALE

    # ── Signal State Machine ─────────────────────────────────────────────────
    signal_state = Column(String(30), default="DETECTED", index=True)
    # States: DETECTED, ANALYZING, APPROVED, REJECTED, WAITING, ACTIVE,
    #         EXPIRED, TP_HIT, SL_HIT, TIME_EXIT, AMBIGUOUS, COMPLETED

    # ── Core Signal Fields ───────────────────────────────────────────────────
    asset = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    direction = Column(String(20), nullable=False)  # BUY, SELL, WAIT
    strategy_name = Column(String(100), nullable=False)

    confidence = Column(Float, nullable=False, default=0.0)
    strength = Column(String(20), nullable=False)
    risk_level = Column(String(20), nullable=False)
    trade_quality = Column(String(10), nullable=True)

    current_price = Column(Float, nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)
    take_profit_3 = Column(Float, nullable=True)

    risk_reward = Column(Float, nullable=True)
    expected_move = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    market_trend = Column(String(50), nullable=True)

    reasoning = Column(Text, nullable=True)
    supporting_indicators = Column(JSON, default=[])

    ai_models_used = Column(JSON, default=[])
    consensus_pct = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)

    # ── Phase 33: Model & Intelligence Snapshots ─────────────────────────────
    model_trace = Column(JSON, nullable=True)           # Full per-model trace (XGB/RF/HGB/Kronos)
    intelligence_snapshot = Column(JSON, nullable=True)  # Full intelligence dict at generation

    # ── Execution Status ─────────────────────────────────────────────────────
    status = Column(String(50), default="GENERATED", index=True)
    execution_status = Column(String(50), nullable=True)
    paper_trade_id = Column(String(100), nullable=True)

    # ── Historical ───────────────────────────────────────────────────────────
    historical_accuracy = Column(Float, nullable=True)
    win_probability = Column(Float, nullable=True)
    similar_trades = Column(Integer, default=0)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    expiry_time = Column(DateTime(timezone=True), nullable=True)
    expected_holding_time = Column(Float, nullable=True)  # in hours
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Phase 33: Outcome Resolution ─────────────────────────────────────────
    outcome = Column(String(20), nullable=True)   # TP_HIT | SL_HIT | TIME_EXIT | EXPIRED | AMBIGUOUS
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)

    # ── Phase 33: PnL Engine ─────────────────────────────────────────────────
    gross_pnl = Column(Float, nullable=True)
    spread_cost = Column(Float, nullable=True)
    slippage_cost = Column(Float, nullable=True)
    fees_cost = Column(Float, nullable=True)
    net_pnl = Column(Float, nullable=True)
    r_multiple = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)  # Legacy alias for net_pnl

    def __repr__(self):
        return f"<SignalLifecycle {self.signal_id} [{self.signal_state}] - {self.status}>"

