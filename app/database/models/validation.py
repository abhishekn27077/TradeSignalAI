import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, String

from app.database.core import Base


class ResearchValidationRecord(Base):
    __tablename__ = "research_validations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core identifying information
    prediction_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    asset = Column(String(20), index=True)
    timeframe = Column(String(10), index=True)
    
    # Prediction parameters
    entry_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    
    # Confidence and quality
    confidence = Column(Float, nullable=True)
    consensus_score = Column(Float, nullable=True)
    grade = Column(String(5), nullable=True)
    
    # Holding times
    expected_hold_time_minutes = Column(Float, nullable=True)
    actual_hold_time_minutes = Column(Float, nullable=True)
    
    # Resolution outcomes
    actual_exit_price = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    direction_correct = Column(Boolean, nullable=True)
    target_hit = Column(Boolean, nullable=True)
    stop_hit = Column(Boolean, nullable=True)
    expired = Column(Boolean, default=False)
    
    # Current status
    status = Column(String(20), default="PENDING", index=True) # PENDING, RESOLVED, EXPIRED
    
    # Model tracking
    strategy_name = Column(String(100), nullable=True, index=True)
    model_name = Column(String(100), nullable=True, index=True)
    session = Column(String(50), nullable=True, index=True)
