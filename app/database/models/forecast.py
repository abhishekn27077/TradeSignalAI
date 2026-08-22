import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.core import Base


class ForecastModelMetadata(Base):
    __tablename__ = "forecast_model_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, index=True, nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    provider_class = Column(String(200), nullable=False)
    
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=10)
    health_status = Column(String(50), default="unknown")  # healthy, degraded, offline
    
    config = Column(JSON, default={})
    
    # Relationships
    results = relationship("ForecastResultModel", back_populates="model_meta", cascade="all, delete-orphan")
    performance = relationship("ForecastPerformanceModel", back_populates="model_meta", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ForecastModelMetadata {self.name} v{self.version}>"


class ForecastPerformanceModel(Base):
    __tablename__ = "forecast_performance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(36), ForeignKey("forecast_model_metadata.id", ondelete="CASCADE"), unique=True)
    
    total_predictions = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    rmse = Column(Float, default=0.0)
    mae = Column(Float, default=0.0)
    directional_accuracy = Column(Float, default=0.0)
    confidence_calibration = Column(Float, default=0.0)
    reliability_score = Column(Float, default=1.0)
    
    last_evaluated = Column(DateTime(timezone=True), nullable=True)
    
    model_meta = relationship("ForecastModelMetadata", back_populates="performance")


class ForecastRequestModel(Base):
    __tablename__ = "forecast_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), index=True, nullable=False)
    forecast_horizon = Column(Integer, nullable=False)  # e.g., 5 candles
    
    market_regime = Column(String(50), nullable=True)
    
    status = Column(String(50), default="pending")  # pending, completed, failed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(Text, nullable=True)

    # Relationships
    results = relationship("ForecastResultModel", back_populates="request", cascade="all, delete-orphan")
    consensus = relationship("ForecastConsensusModel", back_populates="request", uselist=False, cascade="all, delete-orphan")


class ForecastResultModel(Base):
    __tablename__ = "forecast_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), ForeignKey("forecast_requests.id", ondelete="CASCADE"), index=True)
    model_id = Column(String(36), ForeignKey("forecast_model_metadata.id", ondelete="CASCADE"), index=True)
    
    # Standardized outputs
    direction = Column(String(20), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    confidence = Column(Float, nullable=False)      # 0.0 to 1.0
    expected_move_pct = Column(Float, nullable=True)
    expected_volatility = Column(Float, nullable=True)
    expected_hold_candles = Column(Integer, nullable=True)
    probability = Column(Float, nullable=True)      # 0.0 to 1.0
    
    reasoning_metadata = Column(JSON, default={})
    
    prediction_timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    expiry_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, default=[])
    
    lifecycle_state = Column(String(20), default="CREATED", index=True) # CREATED, VALIDATED, PUBLISHED, ACTIVE, EXPIRED, EVALUATED, ARCHIVED
    
    # Relationships
    request = relationship("ForecastRequestModel", back_populates="results")
    model_meta = relationship("ForecastModelMetadata", back_populates="results")
    evaluation = relationship("ForecastEvaluationModel", back_populates="result", uselist=False, cascade="all, delete-orphan")


class ForecastConsensusModel(Base):
    __tablename__ = "forecast_consensus"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String(36), ForeignKey("forecast_requests.id", ondelete="CASCADE"), unique=True)
    
    combined_direction = Column(String(20), nullable=False)
    combined_confidence = Column(Float, nullable=False)
    combined_probability = Column(Float, nullable=True)
    
    weights_used = Column(JSON, default={})  # e.g., {"kronos": 0.3, "lstm": 0.2}
    models_included = Column(Integer, default=0)
    
    lifecycle_state = Column(String(20), default="CREATED", index=True)
    
    # Phase 5 additions
    agreement_matrix = Column(JSON, default={})
    explainability_data = Column(JSON, default={})
    confidence_breakdown = Column(JSON, default={})
    timeline_events = Column(JSON, default=[])
    quality_grade = Column(String(10), nullable=True) # A+, A, B, C, D
    paper_trade_id = Column(String(36), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    request = relationship("ForecastRequestModel", back_populates="consensus")


class ForecastEvaluationModel(Base):
    __tablename__ = "forecast_evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = Column(String(36), ForeignKey("forecast_results.id", ondelete="CASCADE"), unique=True)
    
    actual_outcome_pct = Column(Float, nullable=False)
    actual_direction = Column(String(20), nullable=False)
    
    prediction_error_pct = Column(Float, nullable=False)
    directional_accuracy = Column(Boolean, nullable=False)
    
    evaluated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    result = relationship("ForecastResultModel", back_populates="evaluation")

class DailyOutlookModel(Base):
    __tablename__ = "daily_outlooks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    market_bias = Column(String(20), nullable=False)
    
    strongest_bullish = Column(JSON, default=[])
    strongest_bearish = Column(JSON, default=[])
    highest_volatility = Column(JSON, default=[])
    lowest_volatility = Column(JSON, default=[])
    
    best_sessions = Column(JSON, default=[])
    upcoming_trades = Column(JSON, default=[])

class WeeklyOutlookModel(Base):
    __tablename__ = "weekly_outlooks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    week_start = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    market_bias = Column(String(20), nullable=False)
    
    best_swing_opportunities = Column(JSON, default=[])
    highest_probability_trades = Column(JSON, default=[])
    
    sector_rotation = Column(JSON, default={})
    asset_rotation = Column(JSON, default={})
    market_regime_summary = Column(Text, nullable=True)
