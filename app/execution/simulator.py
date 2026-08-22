import uuid
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class ExecutionMode(str, Enum):
    PAPER = "PAPER"
    BACKTEST = "BACKTEST"
    REPLAY = "REPLAY"
    LIVE_ANALYSIS = "LIVE_ANALYSIS"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class FillStatus(str, Enum):
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class SimulatedOrder:
    order_id: str
    asset: str
    side: OrderSide
    order_type: OrderType
    requested_price: float
    stop_loss: float
    take_profit: float
    requested_lots: float
    mode: ExecutionMode = ExecutionMode.PAPER
    submitted_at_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulatedFill:
    fill_id: str
    order_id: str
    asset: str
    side: OrderSide
    order_type: OrderType
    requested_price: float
    fill_price: float
    slippage_pips: float
    spread_cost_usd: float
    commission_cost_usd: float
    filled_lots: float
    fill_status: FillStatus
    latency_ms: float
    executed_at_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "order_id": self.order_id,
            "asset": self.asset,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "requested_price": round(float(self.requested_price), 5),
            "fill_price": round(float(self.fill_price), 5),
            "slippage_pips": round(float(self.slippage_pips), 2),
            "spread_cost_usd": round(float(self.spread_cost_usd), 2),
            "commission_cost_usd": round(float(self.commission_cost_usd), 2),
            "filled_lots": round(float(self.filled_lots), 2),
            "fill_status": self.fill_status.value,
            "latency_ms": round(float(self.latency_ms), 1),
            "executed_at_utc": self.executed_at_utc.isoformat(),
        }


class ExecutionSimulator:
    """
    High-Fidelity Realistic Execution Simulation Engine.
    Models bid/ask spread, latency, order delay, volatility-scaled slippage, and partial fills.
    """

    def __init__(
        self,
        mode: ExecutionMode = ExecutionMode.PAPER,
        base_spread_pips: float = 1.5,
        base_slippage_pips: float = 0.8,
        commission_per_lot: float = 7.0,
        simulated_latency_ms: float = 65.0
    ):
        self.mode = mode
        self.base_spread_pips = base_spread_pips
        self.base_slippage_pips = base_slippage_pips
        self.commission_per_lot = commission_per_lot
        self.simulated_latency_ms = simulated_latency_ms

    def simulate_execution(
        self,
        order: SimulatedOrder,
        current_market_price: float,
        current_candle_high: Optional[float] = None,
        current_candle_low: Optional[float] = None,
        atr_volatility: float = 0.0015
    ) -> SimulatedFill:
        fill_id = f"fill_{uuid.uuid4().hex[:10]}"
        pip_size = 0.01 if "JPY" in order.asset or "XAU" in order.asset else (1.0 if "BTC" in order.asset or "ETH" in order.asset or "NAS" in order.asset else 0.0001)

        # 1. Limit Order Trigger Check
        if order.order_type == OrderType.LIMIT:
            if current_candle_low is not None and order.side == OrderSide.BUY:
                if current_candle_low > order.requested_price:
                    # Not filled yet
                    return SimulatedFill(
                        fill_id=fill_id, order_id=order.order_id, asset=order.asset, side=order.side,
                        order_type=order.order_type, requested_price=order.requested_price, fill_price=0.0,
                        slippage_pips=0.0, spread_cost_usd=0.0, commission_cost_usd=0.0, filled_lots=0.0,
                        fill_status=FillStatus.REJECTED, latency_ms=self.simulated_latency_ms,
                        details={"reason": "Limit price not touched by candle Low."}
                    )
            elif current_candle_high is not None and order.side == OrderSide.SELL:
                if current_candle_high < order.requested_price:
                    # Not filled yet
                    return SimulatedFill(
                        fill_id=fill_id, order_id=order.order_id, asset=order.asset, side=order.side,
                        order_type=order.order_type, requested_price=order.requested_price, fill_price=0.0,
                        slippage_pips=0.0, spread_cost_usd=0.0, commission_cost_usd=0.0, filled_lots=0.0,
                        fill_status=FillStatus.REJECTED, latency_ms=self.simulated_latency_ms,
                        details={"reason": "Limit price not touched by candle High."}
                    )

        # 2. Compute Spread and Volatility-Scaled Slippage
        spread_amount = self.base_spread_pips * pip_size
        vol_factor = max(1.0, (atr_volatility / (0.0010 if pip_size < 0.01 else 10.0)))
        slippage_pips = self.base_slippage_pips * vol_factor * float(np.random.uniform(0.5, 1.5))
        slippage_amount = slippage_pips * pip_size

        # 3. Compute Realized Fill Price
        if order.side == OrderSide.BUY:
            # Ask price = Market price + spread/2 + slippage
            fill_price = current_market_price + (spread_amount / 2.0) + slippage_amount
        else:
            # Bid price = Market price - spread/2 - slippage
            fill_price = current_market_price - (spread_amount / 2.0) - slippage_amount

        # 4. Partial Fill Simulation (For lots > 5.0, 5% chance of 90% partial fill)
        filled_lots = order.requested_lots
        status = FillStatus.FILLED
        if order.requested_lots > 5.0 and np.random.rand() < 0.05:
            filled_lots = round(order.requested_lots * 0.90, 2)
            status = FillStatus.PARTIALLY_FILLED

        # 5. Commission & Spread Cost
        spread_cost_usd = self.base_spread_pips * 10.0 * filled_lots
        commission_cost_usd = self.commission_per_lot * filled_lots

        return SimulatedFill(
            fill_id=fill_id,
            order_id=order.order_id,
            asset=order.asset,
            side=order.side,
            order_type=order.order_type,
            requested_price=order.requested_price,
            fill_price=fill_price,
            slippage_pips=slippage_pips,
            spread_cost_usd=spread_cost_usd,
            commission_cost_usd=commission_cost_usd,
            filled_lots=filled_lots,
            fill_status=status,
            latency_ms=self.simulated_latency_ms + float(np.random.uniform(5.0, 25.0)),
            details={"mode": self.mode.value}
        )
