from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MarketStructureModel(Base):
    __tablename__ = "smc_market_structure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    trend = Column(String)  # BULLISH, BEARISH, SIDEWAYS
    structure_type = Column(String)  # HH, HL, LH, LL
    bos = Column(Boolean, default=False)
    choch = Column(Boolean, default=False)
    is_internal = Column(Boolean, default=False)
    price_level = Column(Float)

class LiquidityZoneModel(Base):
    __tablename__ = "smc_liquidity_zones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    zone_type = Column(String)  # EQH, EQL, BSL, SSL
    price_level = Column(Float)
    swept = Column(Boolean, default=False)
    sweep_time = Column(DateTime(timezone=True), nullable=True)
    confidence = Column(Float)  # Ranking 0-100

class FVGModel(Base):
    __tablename__ = "smc_fvg"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    fvg_type = Column(String)  # BULLISH, BEARISH
    top_price = Column(Float)
    bottom_price = Column(Float)
    gap_size = Column(Float)
    gap_strength = Column(Float)
    fill_percentage = Column(Float, default=0.0)
    mitigated = Column(Boolean, default=False)

class OrderBlockModel(Base):
    __tablename__ = "smc_order_blocks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    ob_type = Column(String)  # BULLISH, BEARISH, BREAKER
    top_price = Column(Float)
    bottom_price = Column(Float)
    probability = Column(Float)  # 0-100
    mitigated = Column(Boolean, default=False)
    invalidated = Column(Boolean, default=False)

class ConfidenceScoreModel(Base):
    __tablename__ = "smc_confidence_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    total_score = Column(Float)
    category = Column(String)  # Very Strong, Strong, Medium, Weak
    breakdown = Column(JSON)  # Store exact scores for Trend, Structure, Liquidity, etc.

class QuantFilterModel(Base):
    __tablename__ = "quant_filters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    atr = Column(Float)
    adx = Column(Float)
    session = Column(String)  # ASIAN, LONDON, NY, OVERLAP
    news_impact = Column(String)  # HIGH, MEDIUM, LOW, NONE
