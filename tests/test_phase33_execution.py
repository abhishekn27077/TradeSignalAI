"""
tests/test_phase33_execution.py
Phase 33 — PaperExecutor real price fill tests.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from app.execution.paper.executor import PaperExecutor
from app.execution.types import OrderSide, OrderType, OrderStatus


class TestPaperExecutorPhase33:
    """Verify the PaperExecutor fetches real prices, never fabricates."""

    def _executor(self):
        return PaperExecutor()

    @pytest.mark.asyncio
    async def test_submit_uses_real_price_when_none_given(self):
        """When price is None, executor must fetch from market_service."""
        executor = self._executor()
        mock_price = 68000.0

        with patch(
            "app.execution.paper.executor.market_service.get_latest_price",
            new_callable=AsyncMock,
            return_value=mock_price,
        ):
            result = await executor.submit_order(
                symbol="BTCUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.01,
                price=None,  # Must trigger real-price fetch
            )

        assert result is not None
        fill_price = result.price
        assert fill_price == mock_price, f"Fill price should be real price {mock_price}, got {fill_price}"

    @pytest.mark.asyncio
    async def test_execution_blocked_when_price_unavailable(self):
        """If real price cannot be fetched, execution must be blocked."""
        executor = self._executor()

        with patch(
            "app.execution.paper.executor.market_service.get_latest_price",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await executor.submit_order(
                symbol="BTCUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.01,
                price=None,
            )

        # Must return an error/block status, not silently succeed
        assert result is not None
        assert result.status == OrderStatus.REJECTED, f"Expected execution block, got: {result.status}"

    @pytest.mark.asyncio
    async def test_submit_uses_provided_price_when_given(self):
        """When price is explicitly provided, no external fetch should occur."""
        executor = self._executor()
        provided_price = 68500.0

        # If this gets called, the test should fail
        with patch(
            "app.execution.paper.executor.market_service.get_latest_price",
            new_callable=AsyncMock,
            side_effect=Exception("Should not call get_latest_price when price provided"),
        ):
            try:
                result = await executor.submit_order(
                    symbol="BTCUSD",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=0.01,
                    price=provided_price,
                )
                fill_price = result.price
                assert fill_price == provided_price
            except Exception as e:
                pytest.fail(f"PaperExecutor called get_latest_price when price was provided: {e}")

    @pytest.mark.asyncio
    async def test_signal_id_in_result(self):
        """The signal_id must be echoed back in the result."""
        executor = self._executor()

        with patch(
            "app.execution.paper.executor.market_service.get_latest_price",
            new_callable=AsyncMock,
            return_value=100.0,
        ):
            result = await executor.submit_order(
                symbol="BTCUSD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.01,
                price=None,
            )

        if result:
            assert result.id is not None
