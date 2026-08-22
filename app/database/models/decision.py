import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)

from app.database.core import Base


class DecisionHistoryModel(Base):
    __tablename__ = "decision_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), ForeignKey("forecast_requests.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Qualification
    qualification_score = Column(Float, nullable=False)
    trade_grade = Column(String(10), nullable=False)  # A+, A, B, C, D
    is_approved = Column(Boolean, default=False)
    
    # Confidence & Agreement
    confidence = Column(Float, nullable=False)
    model_agreement_pct = Column(Float, nullable=False)
    
    # Risk Reward
    risk_reward_ratio = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    max_drawdown_estimate = Column(Float, nullable=True)
    probability_of_success = Column(Float, nullable=True)
    
    # Regime & Session
    market_regime = Column(String(50), nullable=True)
    session_score = Column(Float, nullable=True)
    active_session = Column(String(50), nullable=True)
    
    # Entry & Exit
    entry_quality = Column(Float, nullable=True)
    recommended_profit_target = Column(Float, nullable=True)
    recommended_stop_loss = Column(Float, nullable=True)
    recommended_trailing_stop = Column(Float, nullable=True)
    
    # Explanations
    explanation = Column(Text, nullable=True)
    warnings = Column(JSON, default=[])
    rejection_reasons = Column(JSON, default=[])
    
    # Lifecycle
    status = Column(String(20), default="EVALUATED") # EVALUATED, PUBLISHED, REJECTED, EXPIRED, COMPLETED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f"<DecisionHistoryModel {self.id} (Grade: {self.trade_grade}, Approved: {self.is_approved})>"
