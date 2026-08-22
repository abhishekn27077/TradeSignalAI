import pytest
from app.execution.simulator import (
    ExecutionSimulator,
    SimulatedOrder,
    OrderSide,
    OrderType,
    ExecutionMode,
    FillStatus
)


def test_execution_simulator_market_order():
    sim = ExecutionSimulator(
        mode=ExecutionMode.PAPER,
        base_spread_pips=1.5,
        base_slippage_pips=0.5,
        commission_per_lot=7.0,
        simulated_latency_ms=50.0
    )

    order = SimulatedOrder(
        order_id="ord_test_01",
        asset="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        requested_price=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        requested_lots=1.0
    )

    fill = sim.simulate_execution(order, current_market_price=1.1000)

    assert fill.fill_status == FillStatus.FILLED
    assert fill.fill_price > 1.1000  # Proves Ask price incorporates spread + slippage
    assert fill.spread_cost_usd == 15.0
    assert fill.commission_cost_usd == 7.0
    assert fill.latency_ms >= 50.0


def test_execution_simulator_limit_order_untriggered():
    sim = ExecutionSimulator(mode=ExecutionMode.PAPER)

    # BUY Limit at 1.0950, but candle Low only reached 1.0980 (not filled)
    order = SimulatedOrder(
        order_id="ord_test_02",
        asset="EURUSD",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        requested_price=1.0950,
        stop_loss=1.0920,
        take_profit=1.1000,
        requested_lots=1.0
    )

    fill = sim.simulate_execution(order, current_market_price=1.1000, current_candle_low=1.0980)

    assert fill.fill_status == FillStatus.REJECTED
    assert "Limit price not touched" in fill.details["reason"]
