from sqlalchemy import JSON, Column, DateTime, Float, String
from sqlalchemy.sql import func

from app.database.core import Base


class HistoricalNews(Base):
    __tablename__ = "historical_news"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    source = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    category = Column(String, index=True)
    affected_assets = Column(JSON) # List of assets
    
    sentiment = Column(String, index=True)
    impact_score = Column(String, index=True)
    confidence = Column(Float)
    
    keywords = Column(JSON)
    named_entities = Column(JSON)
    
    economic_event = Column(String, nullable=True)
    reasoning = Column(String)
