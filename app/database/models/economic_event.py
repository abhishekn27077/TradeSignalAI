"""
Phase 40 — Economic Event Model.

Tracks scheduled macroeconomic events (CPI, NFP, FOMC, GDP, etc.)
with 3-way probabilistic scenarios (HOT / IN_LINE / COOL),
asset sensitivity matrices, and post-event surprise resolution.

Future actual values are ALWAYS unknown until officially released.
No lookahead or fabrication of economic data.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from app.database.core import Base


class EconomicEventModel(Base):
    """
    Stores scheduled economic events with pre-event scenarios
    and post-event outcome resolution.
    """

    __tablename__ = "economic_events"

    # ── Identity ────────────────────────────────────────────────────────────
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), unique=True, index=True, nullable=False)

    # ── Event Details ───────────────────────────────────────────────────────
    event_name = Column(String(200), nullable=False)
    event_category = Column(
        String(50), nullable=False
    )  # INFLATION, EMPLOYMENT, CENTRAL_BANK, GDP, TRADE, HOUSING, CONSUMER, PMI
    currency = Column(String(10), index=True, nullable=False)  # USD, EUR, GBP, JPY, AUD
    country = Column(String(50), nullable=False)
    importance = Column(String(10), index=True, nullable=False)  # HIGH, MEDIUM, LOW

    # ── Temporal ────────────────────────────────────────────────────────────
    scheduled_utc = Column(DateTime(timezone=True), index=True, nullable=False)
    scheduled_ist = Column(DateTime(timezone=True), nullable=True)

    # ── Pre-Event Data ──────────────────────────────────────────────────────
    forecast_value = Column(Float, nullable=True)  # Market consensus forecast
    previous_value = Column(Float, nullable=True)  # Prior release
    unit = Column(String(20), nullable=True)  # %, K, B, Index

    # ── Status ──────────────────────────────────────────────────────────────
    status = Column(
        String(20), default="SCHEDULED", index=True
    )  # SCHEDULED, IMMINENT, RELEASED, EVALUATED

    # ── 3-Way Probabilistic Scenarios ───────────────────────────────────────
    # JSON format: { "HOT": { "probability": 0.25, "description": "..." },
    #                "IN_LINE": { "probability": 0.50, "description": "..." },
    #                "COOL": { "probability": 0.25, "description": "..." } }
    scenarios = Column(JSON, nullable=True)

    # ── Asset Sensitivity Matrix ────────────────────────────────────────────
    # JSON format: { "EURUSD": { "HOT": {"direction": "SELL", "expected_move_pips": 40, "historical_win_rate": 0.68},
    #                             "COOL": {"direction": "BUY", "expected_move_pips": 35, "historical_win_rate": 0.71} },
    #                "XAUUSD": { ... } }
    asset_sensitivities = Column(JSON, nullable=True)

    # ── Historical Statistics (from comparable past events) ─────────────────
    # JSON format: { "sample_size": 48, "avg_surprise": 0.12,
    #                "hot_pct": 0.33, "in_line_pct": 0.42, "cool_pct": 0.25,
    #                "avg_eurusd_move_pips": 35, "avg_xauusd_move_pips": 12 }
    historical_stats = Column(JSON, nullable=True)
    comparable_events_count = Column(Integer, default=0)

    # ── Post-Event Resolution (APPEND-ONLY, written once after release) ─────
    actual_value = Column(Float, nullable=True)  # Official released value
    surprise_value = Column(Float, nullable=True)  # actual - forecast
    surprise_pct = Column(Float, nullable=True)  # (actual - forecast) / |forecast|
    scenario_hit = Column(
        String(10), nullable=True
    )  # HOT, IN_LINE, COOL (which scenario materialized)
    released_at = Column(DateTime(timezone=True), nullable=True)

    # ── Post-Event Market Reaction ──────────────────────────────────────────
    # JSON format: { "EURUSD": {"reaction_pips": -42, "reaction_time_min": 15},
    #                "XAUUSD": {"reaction_pips": 18, "reaction_time_min": 30} }
    market_reactions = Column(JSON, nullable=True)

    # ── AI Analysis ─────────────────────────────────────────────────────────
    ai_pre_event_analysis = Column(Text, nullable=True)
    ai_post_event_analysis = Column(Text, nullable=True)

    # ── Metadata ────────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(50), nullable=True)  # forexfactory, investing_com, manual

    # ── Composite Indexes ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_ee_currency_date", "currency", "scheduled_utc"),
        Index("ix_ee_importance_date", "importance", "scheduled_utc"),
        Index("ix_ee_status_date", "status", "scheduled_utc"),
    )

    def __repr__(self):
        return (
            f"<EconomicEvent {self.event_name} ({self.currency}) "
            f"{self.importance} @ {self.scheduled_utc}>"
        )
