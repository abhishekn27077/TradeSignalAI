from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database.core import Base


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False)
    expected_direction = Column(String)
    bullish_probability = Column(Float)
    bearish_probability = Column(Float)
    neutral_probability = Column(Float)
    expected_holding_hours = Column(Float)
    expected_move_pct = Column(Float)
    expected_price_range = Column(JSON)
    expected_volatility = Column(Float)
    target_price = Column(Float)
    stop_price = Column(Float)
    probability_distribution = Column(JSON)
    confidence = Column(Float)
    strategy_name = Column(String)
    model_name = Column(String)
    candle_close_price = Column(Float)
    created_at = Column(DateTime, default=func.now())
