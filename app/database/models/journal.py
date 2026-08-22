from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.core import Base


class TradeRecord(Base):
    """Permanent storage for a completed trade."""
    __tablename__ = "journal_trades"

    id = Column(String, primary_key=True, index=True)
    account_id = Column(String, index=True)
    symbol = Column(String, index=True)
    market = Column(String) # e.g., Crypto, Forex
    timeframe = Column(String)
    direction = Column(String) # BUY / SELL
    
    entry_price = Column(Float)
    exit_price = Column(Float)
    position_size = Column(Float)
    
    risk_pct = Column(Float)
    reward_pct = Column(Float)
    pnl = Column(Float)
    duration_seconds = Column(Integer)
    
    exit_reason = Column(String) # Stop Loss, Take Profit, Manual, AI
    strategy_used = Column(String)
    ai_decision = Column(String)
    confidence = Column(Float)
    
    # Store snapshots/complex state in JSON
    news_context = Column(JSON, default=dict)
    market_snapshot = Column(JSON, default=dict)
    indicators_snapshot = Column(JSON, default=dict)
    
    session = Column(String)
    volatility = Column(Float)
    spread = Column(Float)
    commission = Column(Float)
    slippage = Column(Float)
    
    opened_at = Column(DateTime)
    closed_at = Column(DateTime, default=func.now())
    
    # Relationships
    ai_review = relationship("AIReview", back_populates="trade", uselist=False)

class AIReview(Base):
    """AI analysis of a completed trade."""
    __tablename__ = "journal_ai_reviews"
    
    id = Column(String, primary_key=True, index=True)
    trade_id = Column(String, ForeignKey("journal_trades.id"), unique=True)
    
    why_opened = Column(String)
    why_closed = Column(String)
    mistakes = Column(String)
    correct_decisions = Column(String)
    missed_opportunities = Column(String)
    alternative_scenarios = Column(String)
    improvement_suggestions = Column(String)
    confidence_evaluation = Column(Float)
    
    # Validation fields
    indicators_used = Column(String)
    risk_decision = Column(String)
    news_impact = Column(String)
    similar_historical_trades = Column(String)
    
    created_at = Column(DateTime, default=func.now())
    
    trade = relationship("TradeRecord", back_populates="ai_review")

class TradeTag(Base):
    """Tags for searching and categorizing trades."""
    __tablename__ = "journal_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, ForeignKey("journal_trades.id"))
    tag = Column(String, index=True)

class Recommendation(Base):
    """AI-generated system-level recommendations based on analytics."""
    __tablename__ = "journal_recommendations"
    
    id = Column(String, primary_key=True, index=True)
    category = Column(String, index=True) # e.g., 'Risk', 'Timing', 'Strategy'
    recommendation_text = Column(String)
    confidence = Column(Float)
    action_item = Column(String)
    
    created_at = Column(DateTime, default=func.now())
