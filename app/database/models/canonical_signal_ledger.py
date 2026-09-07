"""
app/database/models/canonical_signal_ledger.py
==============================================
Immutable Canonical Signal Ledger Models for TradeSignalAI-v3.

Ensures strict persistence for:
- Canonical Signals (across all timeframes)
- Shadow Signals (rejected setups tracked for risk alpha)
- Indicator Registry Records
- Historical State Analogue Records
- Model Ablation & Champion/Challenger Benchmarks
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    JSON,
    Text,
)
from app.database.core import Base


class CanonicalSignalEntity(Base):
    """
    Immutable ledger of all generated signals across timeframes.
    """
    __tablename__ = "canonical_signal_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(100), unique=True, index=True, nullable=False)
    asset = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    horizon = Column(String(10), nullable=False)
    direction = Column(String(10), nullable=False)  # BUY, SELL, WAIT

    generated_at = Column(String(50), nullable=False, index=True)
    information_cutoff_time = Column(String(50), nullable=False)
    expiry_time = Column(String(50), nullable=False)

    current_price = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    risk_reward = Column(Float, nullable=False)

    raw_confidence = Column(Float, nullable=False)
    calibrated_probability = Column(Float, nullable=False)
    p_tp_first = Column(Float, nullable=False)
    p_sl_first = Column(Float, nullable=False)
    p_time_exit = Column(Float, nullable=False)
    expected_gross_r = Column(Float, nullable=False)
    expected_net_r = Column(Float, nullable=False)

    quality_grade = Column(String(10), index=True, nullable=False)  # A+, A, B, C, WATCH, REJECTED
    consensus_agreement = Column(String(20), nullable=False)
    consensus_pct = Column(Float, nullable=False)
    regime = Column(String(50), nullable=False)
    session = Column(String(50), nullable=False)
    event_risk = Column(String(20), nullable=False)

    htf_alignment_score = Column(Float, nullable=True)
    mtf_conflict_score = Column(Float, nullable=True)

    status = Column(String(30), index=True, nullable=False)  # QUALIFIED, WATCHLIST, REJECTED, ACTIVE, RESOLVED
    decision = Column(String(30), nullable=False)
    decision_trace = Column(JSON, nullable=True)
    model_evidence = Column(JSON, nullable=True)
    indicator_clusters = Column(JSON, nullable=True)
    historical_analogues_summary = Column(JSON, nullable=True)

    is_shadow_tracked = Column(Boolean, default=False, index=True)
    outcome = Column(String(30), nullable=True)  # TP_HIT, SL_HIT, TIME_EXIT, AMBIGUOUS
    net_r = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_time = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
