from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func

from app.database.core import Base


class StrategyLabModel(Base):
    __tablename__ = "strategy_lab_strategies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(String)
    creator = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    performance = Column(JSON, default=dict)
    supported_assets = Column(JSON, default=list)
    timeframes = Column(JSON, default=list)
    status = Column(String, default="Draft")

class StrategyExperimentModel(Base):
    __tablename__ = "strategy_lab_experiments"
    id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True)
    name = Column(String)
    status = Column(String, default="Running")
    results = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StrategyNotebookModel(Base):
    __tablename__ = "strategy_lab_notebooks"
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StrategyBenchmarkModel(Base):
    __tablename__ = "strategy_lab_benchmarks"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
