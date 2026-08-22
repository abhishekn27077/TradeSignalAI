"""
Market Intelligence Database Models
====================================
Production-grade schema for historical OHLCV storage, data sync tracking,
quality reporting, and feature persistence.
"""

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
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database.core import Base


class SymbolModel(Base):
    """
    Symbol metadata registry.
    Tracks every tradeable instrument the platform monitors.
    """
    __tablename__ = "symbols"

    symbol = Column(String, primary_key=True, index=True)
    asset_class = Column(String, index=True)  # forex, crypto, indices, commodities
    base_currency = Column(String)
    quote_currency = Column(String)
    exchange = Column(String, index=True)
    description = Column(String, nullable=True)
    price_precision = Column(Integer, default=5)
    quantity_precision = Column(Integer, default=2)
    pip_size = Column(Float, nullable=True)
    pip_value = Column(Float, nullable=True)
    min_lot = Column(Float, default=0.01)
    max_lot = Column(Float, default=100.0)
    market_session = Column(String, nullable=True)
    trading_hours = Column(String, nullable=True)  # e.g. "00:00-23:59 UTC"
    data_provider = Column(String, default="yfinance")
    is_active = Column(Boolean, default=True)
    last_synced = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CandleModel(Base):
    """
    Historical OHLCV candlestick data.
    Supports millions of rows with composite indexing for fast range queries.
    Features are stored as a JSON blob per candle for single-query retrieval.
    """
    __tablename__ = "historical_candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    spread = Column(Float, nullable=True)
    session = Column(String, nullable=True)  # Asian, London, New York, etc.
    provider = Column(String, default="yfinance")
    timezone = Column(String, default="UTC")
    quality_score = Column(Float, nullable=True)
    features_json = Column(JSON, nullable=True)  # Feature store blob

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "timestamp", "provider",
                         name="uq_candle_identity"),
        Index("ix_candle_range", "symbol", "timeframe", "timestamp"),
        Index("ix_candle_provider", "provider", "symbol"),
    )


class DataSyncJobModel(Base):
    """
    Tracks historical data download jobs.
    One row per download task (symbol + timeframe combination).
    """
    __tablename__ = "data_sync_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False)
    provider = Column(String, default="yfinance")
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0.0 - 100.0
    total_candles = Column(Integer, default=0)
    downloaded_candles = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_sync_job_status", "status", "symbol"),
    )


class DataQualityReportModel(Base):
    """
    Persists data quality scan results.
    One row per quality scan of a symbol + timeframe dataset.
    """
    __tablename__ = "data_quality_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False)
    provider = Column(String, default="yfinance")
    total_candles = Column(Integer, default=0)
    missing_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    invalid_count = Column(Integer, default=0)
    negative_price_count = Column(Integer, default=0)
    out_of_order_count = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)  # 0.0 - 100.0
    details_json = Column(JSON, nullable=True)  # Extended diagnostics
    auto_repaired = Column(Boolean, default=False)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_quality_symbol_tf", "symbol", "timeframe"),
    )
