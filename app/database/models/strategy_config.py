from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database.core import Base


class StrategyConfigModel(Base):
    __tablename__ = "strategy_configs"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="ENABLED")
    priority = Column(Integer, default=5)
    weight = Column(Float, default=1.0)
    max_concurrent_trades = Column(Integer, default=3)
    daily_trade_limit = Column(Integer, default=10)
    allowed_sessions = Column(JSON, default=lambda: ["all"])
    allowed_assets = Column(JSON, default=lambda: ["all"])
    allowed_timeframes = Column(JSON, default=lambda: ["all"])
    min_trade_quality = Column(Integer, default=60)
    min_ai_confidence = Column(Float, default=0.5)
    config_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class StrategyAnalyticsModel(Base):
    __tablename__ = "strategy_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String, index=True, nullable=False)
    total_trades = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    sortino_ratio = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    avg_profit = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    avg_hold_time_minutes = Column(Float, default=0.0)
    avg_r_multiple = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    regime_performance = Column(JSON, default=dict)
    asset_performance = Column(JSON, default=dict)
    session_performance = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
