"""
tests/test_order_state_machine.py
=================================
Test Suite for Finite Order State Machine and Partial Fill Lifecycle.

Benchmarked against NautilusTrader's order execution model.
"""

import pytest

from app.execution.orders.state_machine import (
    OrderStateMachine,
    OrderState,
    IllegalStateTransitionError,
)
from app.core.events import (
    OrderCreated,
    OrderSubmitted,
    OrderAccepted,
    OrderRejected,
    OrderFilled,
)


class TestOrderStateMachine:
    def setup_method(self):
        self.osm = OrderStateMachine()

    def test_full_happy_path_lifecycle(self):
        order, evt_created = self.osm.create_order(
            symbol="EURUSD",
            side="BUY",
            quantity=1.0,
            requested_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            order_type="MARKET",
        )
        assert order.state == OrderState.CREATED
        assert isinstance(evt_created, OrderCreated)
        assert order.remaining_quantity == 1.0

        # Submit
        order, evt_sub = self.osm.submit_order(order.order_id, broker="PAPER")
        assert order.state == OrderState.SUBMITTED
        assert isinstance(evt_sub, OrderSubmitted)

        # Accept
        order, evt_acc = self.osm.accept_order(order.order_id, broker_order_id="BRK-12345")
        assert order.state == OrderState.ACCEPTED
        assert order.broker_order_id == "BRK-12345"
        assert isinstance(evt_acc, OrderAccepted)

        # Partial fill 1: 0.4 @ 1.1005
        order, evt_fill1 = self.osm.record_fill(
            order_id=order.order_id,
            fill_price=1.1005,
            fill_quantity=0.4,
            fee=0.50,
            slippage=0.0005,
        )
        assert order.state == OrderState.PARTIALLY_FILLED
        assert order.filled_quantity == 0.4
        assert order.remaining_quantity == 0.6
        assert order.average_fill_price == 1.1005
        assert evt_fill1.is_partial is True
        assert len(order.fills) == 1

        # Partial fill 2 (completes order): 0.6 @ 1.1015
        order, evt_fill2 = self.osm.record_fill(
            order_id=order.order_id,
            fill_price=1.1015,
            fill_quantity=0.6,
            fee=0.75,
            slippage=0.0015,
        )
        assert order.state == OrderState.FILLED
        assert order.filled_quantity == 1.0
        assert order.remaining_quantity == 0.0
        # Weighted average: (0.4 * 1.1005 + 0.6 * 1.1015) / 1.0 = 0.4402 + 0.6609 = 1.1011
        assert pytest.approx(order.average_fill_price, 0.00001) == 1.1011
        assert order.total_fees == 1.25
        assert evt_fill2.is_partial is False
        assert len(order.fills) == 2

    def test_rejection_lifecycle(self):
        order, _ = self.osm.create_order(
            symbol="BTCUSD",
            side="SELL",
            quantity=0.5,
            requested_price=65000.0,
            stop_loss=66000.0,
            take_profit=63000.0,
        )
        order, evt_rej = self.osm.reject_order(order.order_id, reason="EXCESSIVE_SLIPPAGE")
        assert order.state == OrderState.REJECTED
        assert order.rejection_reason == "EXCESSIVE_SLIPPAGE"
        assert isinstance(evt_rej, OrderRejected)

    def test_cancellation_lifecycle(self):
        order, _ = self.osm.create_order(
            symbol="XAUUSD",
            side="BUY",
            quantity=2.0,
            requested_price=2500.0,
            stop_loss=2480.0,
            take_profit=2540.0,
        )
        self.osm.submit_order(order.order_id)
        self.osm.accept_order(order.order_id, broker_order_id="BRK-GOLD")
        self.osm.request_cancel(order.order_id)
        assert order.state == OrderState.PENDING_CANCEL

        self.osm.confirm_cancel(order.order_id)
        assert order.state == OrderState.CANCELLED

    def test_illegal_state_transition_raises_error(self):
        order, _ = self.osm.create_order(
            symbol="EURUSD",
            side="BUY",
            quantity=1.0,
            requested_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
        )
        # Cannot transition directly from CREATED to FILLED
        with pytest.raises(IllegalStateTransitionError):
            self.osm.record_fill(order.order_id, fill_price=1.1000, fill_quantity=1.0)

    def test_overfill_quantity_raises_value_error(self):
        order, _ = self.osm.create_order(
            symbol="EURUSD",
            side="BUY",
            quantity=1.0,
            requested_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
        )
        self.osm.submit_order(order.order_id)
        self.osm.accept_order(order.order_id, broker_order_id="BRK-1")

        with pytest.raises(ValueError, match="exceeds remaining quantity"):
            self.osm.record_fill(order.order_id, fill_price=1.1000, fill_quantity=1.5)
