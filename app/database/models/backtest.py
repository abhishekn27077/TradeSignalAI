from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.sql import func

from app.database.core import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(String, primary_key=True, index=True)
    strategy_name = Column(String, index=True)
    symbols = Column(JSON)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    initial_capital = Column(Float)
    final_capital = Column(Float)
    
    # Store aggregated metrics as JSON for easy retrieval
    metrics = Column(JSON)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("backtest_runs.id"))
    
    symbol = Column(String, index=True)
    side = Column(String)
    
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Float)
    
    pnl = Column(Float)
    pnl_percent = Column(Float)
    
    commission_paid = Column(Float)
    exit_reason = Column(String)
