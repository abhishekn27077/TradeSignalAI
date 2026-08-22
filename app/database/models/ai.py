from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DecisionHistoryModel(Base):
    """
    SQLAlchemy Model for logging final trading decisions made by the Chief Trader.
    """
    __tablename__ = "ai_decision_history"

    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True)
    signal = Column(String) # BUY, SELL, WAIT
    confidence = Column(Float)
    reasoning = Column(String)
    risk_score = Column(Float)
    market_summary = Column(String)
    timestamp = Column(DateTime(timezone=True), index=True)
    
    # AI Learning Data for Future ML Training
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    mae = Column(Float, nullable=True) # Maximum Adverse Excursion
    mfe = Column(Float, nullable=True) # Maximum Favorable Excursion
    duration_minutes = Column(Integer, nullable=True)
    indicators_state = Column(JSON, nullable=True)
    structure_state = Column(JSON, nullable=True)
    liquidity_state = Column(JSON, nullable=True)
    news_status = Column(String, nullable=True)
    trade_result = Column(String, nullable=True) # WIN, LOSS, BREAKEVEN

class TokenUsageModel(Base):
    """
    SQLAlchemy Model for tracking LLM API usage costs across providers.
    """
    __tablename__ = "ai_token_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String, index=True)
    agent_role = Column(String, index=True)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    estimated_cost_usd = Column(Float)
    timestamp = Column(DateTime(timezone=True))

class ReasoningLogModel(Base):
    """
    SQLAlchemy Model for logging raw prompts and responses for debugging and fine-tuning later.
    """
    __tablename__ = "ai_reasoning_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, index=True)
    prompt_used = Column(String)
    raw_response = Column(JSON)
    latency_ms = Column(Float)
    timestamp = Column(DateTime(timezone=True))
