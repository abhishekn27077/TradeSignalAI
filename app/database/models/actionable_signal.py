"""
Phase 50 — Actionable Signal & Trade Opportunity Model.

Represents an actionable trade opportunity with explicit IST entry windows,
holding envelopes, versioning, anti-whipsaw lineage, and complete position lifecycle.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

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
from app.core.market_clock import market_clock


class ActionableSignalModel(Base):
    """
    Stores human-executable actionable trade opportunities.
    Maintains immutable versioning (parent/superseded signals) and strict temporal contracts.
    """

    __tablename__ = "actionable_signals"

    # ── Identity & Versioning ────────────────────────────────────────────────
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(100), unique=True, index=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    parent_signal_id = Column(String(100), index=True, nullable=True)
    supersedes_signal_id = Column(String(100), index=True, nullable=True)
    revalidation_count = Column(Integer, default=0, nullable=False)
    trace_id = Column(String(36), index=True, nullable=True)

    # ── Asset & Direction ────────────────────────────────────────────────────
    asset = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    direction = Column(String(20), nullable=False)  # BUY, SELL, NEUTRAL
    strategy_name = Column(String(100), default="ConsensusEngine", nullable=False)

    # ── Temporal Discipline (Stored in UTC, Displayed in IST) ────────────────
    forecast_generated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    last_revalidated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    target_time = Column(DateTime(timezone=True), index=True, nullable=False)
    entry_window_start = Column(DateTime(timezone=True), index=True, nullable=False)
    preferred_entry_time = Column(DateTime(timezone=True), nullable=False)
    entry_window_end = Column(DateTime(timezone=True), index=True, nullable=False)
    signal_expiry_time = Column(DateTime(timezone=True), index=True, nullable=False)

    # ── Dynamic Holding Expectations ─────────────────────────────────────────
    expected_hold_min_hours = Column(Float, default=2.0, nullable=False)
    expected_hold_max_hours = Column(Float, default=4.0, nullable=False)
    maximum_hold_hours = Column(Float, default=6.0, nullable=False)

    actual_entry_time = Column(DateTime(timezone=True), nullable=True)
    actual_exit_time = Column(DateTime(timezone=True), nullable=True)

    # ── Intelligence & Risk Metrics ──────────────────────────────────────────
    confidence = Column(Float, nullable=False, default=0.0)
    consensus_score = Column(Float, nullable=True)
    consensus_members = Column(Integer, default=0)
    market_regime = Column(String(50), nullable=True)
    volatility_state = Column(String(30), nullable=True)
    event_risk = Column(String(30), default="NONE", nullable=False)
    news_risk = Column(String(30), default="NEUTRAL", nullable=False)

    model_version = Column(String(50), default="3.2.0-frozen", nullable=False)
    strategy_version = Column(String(50), default="1.0.0", nullable=False)
    configuration_hash = Column(String(64), nullable=True)

    # ── Execution Pricing & Risk/Reward ──────────────────────────────────────
    current_price = Column(Float, nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=True)

    latest_market_candle_time = Column(DateTime(timezone=True), nullable=True)
    data_age_seconds = Column(Float, default=0.0)
    data_freshness_status = Column(String(30), default="FRESH")  # FRESH | DATA_STALE | DATA_UNAVAILABLE

    # ── Actionable State Machine & Human Guidance ────────────────────────────
    status = Column(String(50), default="FORECAST", index=True, nullable=False)
    # States: FORECAST, WATCH, PRE_ENTRY_VALIDATION, VALIDATED, ENTRY_WINDOW_OPEN,
    #         ENTER_NOW, PAPER_TRADE_ACTIVE, HOLD, TP_HIT, SL_HIT, INVALIDATED,
    #         TIME_EXIT, EXPIRED, CANCELLED, NO_TRADE

    primary_action = Column(String(30), default="WAIT", nullable=False)
    # Actions: WAIT, ENTER NOW, HOLD, CLOSE, CANCELLED, EXPIRED, NO TRADE

    invalidation_reason = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    no_trade_reason = Column(String(100), nullable=True)

    # ── Paper Trade Outcome & MFE/MAE Resolution ─────────────────────────────
    paper_trade_id = Column(String(100), nullable=True)
    mfe_r = Column(Float, nullable=True)  # Maximum Favorable Excursion in R
    mae_r = Column(Float, nullable=True)  # Maximum Adverse Excursion in R
    gross_r = Column(Float, nullable=True)
    friction_r = Column(Float, nullable=True)
    net_r = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True)
    holding_duration_seconds = Column(Float, nullable=True)

    # ── Composite Indexes ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_act_asset_target", "asset", "target_time"),
        Index("ix_act_status_expiry", "status", "signal_expiry_time"),
        Index("ix_act_parent_version", "parent_signal_id", "version"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the actionable signal into full IST-formatted representation."""
        return {
            "signal_id": self.signal_id,
            "version": self.version,
            "parent_signal_id": self.parent_signal_id,
            "supersedes_signal_id": self.supersedes_signal_id,
            "revalidation_count": self.revalidation_count,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "direction": self.direction,
            "strategy_name": self.strategy_name,
            # Exact IST time contracts
            "forecast_generated_at_utc": self.forecast_generated_at.isoformat() if self.forecast_generated_at else None,
            "forecast_generated_at_ist": market_clock.format_ist(self.forecast_generated_at) if self.forecast_generated_at else None,
            "last_revalidated_at_utc": self.last_revalidated_at.isoformat() if self.last_revalidated_at else None,
            "last_revalidated_at_ist": market_clock.format_ist(self.last_revalidated_at) if self.last_revalidated_at else None,
            "target_time_utc": self.target_time.isoformat() if self.target_time else None,
            "target_time_ist": market_clock.format_ist(self.target_time) if self.target_time else None,
            "entry_window_start_utc": self.entry_window_start.isoformat() if self.entry_window_start else None,
            "entry_window_start_ist": market_clock.format_ist(self.entry_window_start) if self.entry_window_start else None,
            "preferred_entry_time_utc": self.preferred_entry_time.isoformat() if self.preferred_entry_time else None,
            "preferred_entry_time_ist": market_clock.format_ist(self.preferred_entry_time) if self.preferred_entry_time else None,
            "entry_window_end_utc": self.entry_window_end.isoformat() if self.entry_window_end else None,
            "entry_window_end_ist": market_clock.format_ist(self.entry_window_end) if self.entry_window_end else None,
            "signal_expiry_time_utc": self.signal_expiry_time.isoformat() if self.signal_expiry_time else None,
            "signal_expiry_time_ist": market_clock.format_ist(self.signal_expiry_time) if self.signal_expiry_time else None,
            # Holding envelopes
            "expected_hold_min_hours": self.expected_hold_min_hours,
            "expected_hold_max_hours": self.expected_hold_max_hours,
            "maximum_hold_hours": self.maximum_hold_hours,
            "expected_holding_formatted": f"{self.expected_hold_min_hours:.0f}–{self.expected_hold_max_hours:.0f} hours",
            "maximum_holding_formatted": f"{self.maximum_hold_hours:.0f} hours",
            # Intelligence & Pricing
            "confidence": self.confidence,
            "consensus_score": self.consensus_score,
            "consensus_members": self.consensus_members,
            "market_regime": self.market_regime,
            "volatility_state": self.volatility_state,
            "event_risk": self.event_risk,
            "news_risk": self.news_risk,
            "current_price": self.current_price,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward": self.risk_reward,
            # Status & Human Action
            "status": self.status,
            "primary_action": self.primary_action,
            "invalidation_reason": self.invalidation_reason,
            "change_reason": self.change_reason,
            "no_trade_reason": self.no_trade_reason,
            # Freshness
            "data_age_seconds": self.data_age_seconds,
            "data_freshness_status": self.data_freshness_status,
            # Resolution
            "paper_trade_id": self.paper_trade_id,
            "mfe_r": self.mfe_r,
            "mae_r": self.mae_r,
            "gross_r": self.gross_r,
            "friction_r": self.friction_r,
            "net_r": self.net_r,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
        }
