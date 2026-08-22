import enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.sql import func

from app.database.core import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"

class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    
    balance = Column(Float, default=10000.0)
    equity = Column(Float, default=10000.0)
    used_margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=10000.0)
    
    realized_pnl = Column(Float, default=0.0)
    floating_pnl = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("paper_accounts.id"))
    
    symbol = Column(String, index=True)
    order_type = Column(String) # MARKET, LIMIT, STOP
    side = Column(String) # BUY, SELL
    
    requested_price = Column(Float, nullable=True)
    fill_price = Column(Float, nullable=True)
    
    quantity = Column(Float)
    filled_quantity = Column(Float, default=0.0)
    
    take_profit = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    status = Column(String, default=OrderStatus.PENDING.value)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("paper_accounts.id"))
    
    symbol = Column(String, index=True)
    side = Column(String) # LONG, SHORT
    
    entry_price = Column(Float)
    quantity = Column(Float)
    
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trailing_stop = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
