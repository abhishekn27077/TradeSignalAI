from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String

from app.database.core import Base


class BacktestResultModel(Base):
    __tablename__ = "research_backtest_results"
    
    id = Column(String(36), primary_key=True)
    strategy = Column(String(50), index=True)
    symbol = Column(String(20), index=True)
    timeframe = Column(String(10))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    capital = Column(Float)
    commission = Column(Float)
    spread = Column(Float)
    slippage = Column(Float)
    
    total_trades = Column(Integer)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    
    equity_curve = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

class ConsensusEvaluationModel(Base):
    __tablename__ = "research_consensus_evaluations"
    
    id = Column(String(36), primary_key=True)
    request_id = Column(String(36), index=True) # Linked to ForecastConsensusModel implicitly
    
    direction_correct = Column(Boolean)
    target_hit = Column(Boolean)
    stop_hit = Column(Boolean)
    
    mfe_pct = Column(Float) # Maximum Favorable Excursion
    mae_pct = Column(Float) # Maximum Adverse Excursion
    holding_time_candles = Column(Integer)
    forecast_error = Column(Float)
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)

class ExperimentTrackingModel(Base):
    __tablename__ = "research_experiments"
    
    id = Column(String(36), primary_key=True)
    experiment_name = Column(String(100))
    
    hyperparameters = Column(JSON, default={}) # Forecast horizon, thresholds, weights
    features_used = Column(JSON, default=[])
    
    result_metrics = Column(JSON, default={}) # Accuracy, Sharpe, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelCalibrationModel(Base):
    __tablename__ = "research_model_calibrations"
    
    model_id = Column(String(50), primary_key=True)
    
    rolling_accuracy = Column(Float, default=0.5)
    total_evaluations = Column(Integer, default=0)
    current_weight_multiplier = Column(Float, default=1.0)
    
    calibration_history = Column(JSON, default=[])
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
