"""
app/core/execution_abstraction.py
=================================
Modular Execution & Research-to-Live Parity Abstraction for TradeSignalAI-v3 (Phase 66).

Inspired by NautilusTrader & QuantConnect LEAN, decouples strategy policies from execution environments.
Guarantees the identical SignalPolicy executes across historical replay, paper simulation, and live demo.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.config.settings import get_settings


@dataclass
class OrderIntent:
    order_id: str
    asset: str
    direction: str  # "BUY", "SELL"
    order_type: str  # "LIMIT", "MARKET"
    quantity: float
    limit_price: float
    stop_loss: float
    take_profit: float
    time_in_force: str = "GTC"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ExecutionReport:
    report_id: str
    order_id: str
    asset: str
    direction: str
    filled_quantity: float
    fill_price: float
    spread_paid: float
    slippage_paid: float
    commission_paid: float
    status: str  # "FILLED", "REJECTED", "CANCELLED", "SIMULATED_PAPER"
    execution_time: str
    is_live_broker: bool = False


class MarketDataProvider(ABC):
    """Abstract interface for point-in-time market data access."""

    @abstractmethod
    def get_latest_price(self, asset: str, cutoff_time: Optional[datetime] = None) -> float:
        pass

    @abstractmethod
    def get_candles(self, asset: str, timeframe: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        pass


class SignalPolicy(ABC):
    """Abstract trading policy executed equivalently in replay and live modes."""

    @abstractmethod
    def evaluate_setup(self, asset: str, timeframe: str, context: Dict[str, Any]) -> Optional[OrderIntent]:
        pass


class BrokerAdapter(ABC):
    """Abstract broker interface with strict paper-mode safety gates."""

    @abstractmethod
    def submit_order(self, order: OrderIntent) -> ExecutionReport:
        pass

    @abstractmethod
    def get_portfolio_state(self) -> Dict[str, Any]:
        pass


class PaperBrokerAdapter(BrokerAdapter):
    """
    Certified Paper Simulation Broker for TradeSignalAI-v3.
    Strictly forbids real money routing.
    """

    def __init__(self, initial_balance: float = 100000.0):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[ExecutionReport] = []

    def submit_order(self, order: OrderIntent) -> ExecutionReport:
        settings = get_settings()
        # Enforce Real Money Safety Lock
        if getattr(settings, "REAL_MONEY_ENABLED", False) or getattr(settings, "BROKER_EXECUTION_ENABLED", False):
            raise PermissionError("REAL_MONEY_EXECUTION_STRICTLY_LOCKED: Broker routing to real exchanges is disabled.")

        spread = 0.00010 if "USD" in order.asset and order.asset not in ["BTCUSD", "ETHUSD"] else (order.limit_price * 0.0002)
        slippage = 0.00005 if "USD" in order.asset and order.asset not in ["BTCUSD", "ETHUSD"] else (order.limit_price * 0.0001)
        commission = 0.00005 if "USD" in order.asset and order.asset not in ["BTCUSD", "ETHUSD"] else (order.limit_price * 0.0001)

        fill_price = order.limit_price + (slippage if order.direction == "BUY" else -slippage)
        report_id = f"EXEC-PAPER-{order.asset}-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:10]}"

        report = ExecutionReport(
            report_id=report_id,
            order_id=order.order_id,
            asset=order.asset,
            direction=order.direction,
            filled_quantity=order.quantity,
            fill_price=round(fill_price, 5),
            spread_paid=spread,
            slippage_paid=slippage,
            commission_paid=commission,
            status="FILLED",
            execution_time=datetime.now(timezone.utc).isoformat(),
            is_live_broker=False,
        )

        self.execution_history.append(report)
        self.open_positions[order.asset] = {
            "order_id": order.order_id,
            "direction": order.direction,
            "entry_price": fill_price,
            "stop_loss": order.stop_loss,
            "take_profit": order.take_profit,
            "quantity": order.quantity,
            "opened_at": report.execution_time,
        }

        return report

    def get_portfolio_state(self) -> Dict[str, Any]:
        return {
            "cash": self.cash,
            "initial_balance": self.initial_balance,
            "open_positions_count": len(self.open_positions),
            "open_positions": self.open_positions,
            "total_executions": len(self.execution_history),
            "execution_mode": "DEMO_PAPER",
            "real_money_enabled": False,
        }


paper_broker_adapter = PaperBrokerAdapter()
