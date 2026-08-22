from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    TRAILING_STOP = "TRAILING_STOP"

class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class TradeResult(BaseModel):
    trade_id: str
    symbol: str
    side: PositionSide
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    commission_paid: float
    slippage_incurred: float
    exit_reason: str

class BacktestMetrics(BaseModel):
    net_profit: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    risk_reward_ratio: float
    expectancy: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    recovery_factor: float
    consecutive_wins: int
    consecutive_losses: int

class BacktestConfig(BaseModel):
    strategy_name: str
    symbols: list[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    leverage: float = 1.0
