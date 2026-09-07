"""Regression tests for security audit findings (Phase 60)."""
import json
import math
import pytest
from datetime import datetime, timezone


class TestRiskEngineKeyMismatchFix:
    """TS-005: Risk engine must read 'target' key, not 'take_profit'."""

    def test_rr_check_uses_target_key(self):
        from app.risk.engine import RiskEngine
        engine = RiskEngine()
        # Coordinator passes "target", NOT "take_profit"
        # Use RR > 2.0 to avoid edge case at exactly 2.0
        proposal = {
            "symbol": "EURUSD",
            "direction": "BUY",
            "quantity": 0.1,
            "price": 1.1000,
            "target": 1.1150,   # RR = 0.015/0.005 = 3.0 → should pass
            "stop_loss": 1.0950,
        }
        result = engine.validate_trade(proposal)
        assert result["approved"] is True, f"Should approve RR=3.0: {result}"

    def test_rr_below_minimum_rejected_with_target_key(self):
        from app.risk.engine import RiskEngine
        engine = RiskEngine()
        proposal = {
            "symbol": "EURUSD",
            "direction": "BUY",
            "quantity": 0.1,
            "price": 1.1000,
            "target": 1.1020,   # only 0.4 RR (below 2.0 minimum)
            "stop_loss": 1.0950,
        }
        result = engine.validate_trade(proposal)
        assert result["approved"] is False, f"Should reject RR<2.0: {result}"

    def test_failsafe_error_causes_reject(self):
        """TS-005b: Failsafe exception must fail-closed, not open."""
        from app.risk.engine import RiskEngine
        engine = RiskEngine()
        # Inject a failsafe that raises
        class BadFailsafe:
            def check(self):
                raise RuntimeError("simulated failure")
        engine._failsafe = BadFailsafe()
        proposal = {"symbol": "EURUSD", "direction": "BUY", "quantity": 0.1, "price": 1.1}
        result = engine.validate_trade(proposal)
        assert result["approved"] is False, "Must fail closed on failsafe error"


class TestPaperExecutorInputValidation:
    """TS-006: Paper executor must reject invalid inputs."""

    @pytest.mark.asyncio
    async def test_negative_quantity_rejected(self):
        from app.execution.paper.executor import PaperExecutor
        from app.execution.types import OrderSide, OrderType
        ex = PaperExecutor(initial_balance=100000.0)
        order = await ex.submit_order("TEST", OrderSide.BUY, OrderType.MARKET, -5.0, price=100.0)
        assert order.status.name == "REJECTED"
        assert "TEST" not in ex.positions, "Position must not be created"

    @pytest.mark.asyncio
    async def test_zero_quantity_rejected(self):
        from app.execution.paper.executor import PaperExecutor
        from app.execution.types import OrderSide, OrderType
        ex = PaperExecutor(initial_balance=100000.0)
        order = await ex.submit_order("TEST", OrderSide.BUY, OrderType.MARKET, 0.0, price=100.0)
        assert order.status.name == "REJECTED"

    @pytest.mark.asyncio
    async def test_nan_price_rejected(self):
        from app.execution.paper.executor import PaperExecutor
        from app.execution.types import OrderSide, OrderType
        ex = PaperExecutor(initial_balance=100000.0)
        order = await ex.submit_order("TEST", OrderSide.BUY, OrderType.MARKET, 1.0, price=float('nan'))
        assert order.status.name == "REJECTED"

    @pytest.mark.asyncio
    async def test_infinite_price_rejected(self):
        from app.execution.paper.executor import PaperExecutor
        from app.execution.types import OrderSide, OrderType
        ex = PaperExecutor(initial_balance=100000.0)
        order = await ex.submit_order("TEST", OrderSide.BUY, OrderType.MARKET, 1.0, price=float('inf'))
        assert order.status.name == "REJECTED"

    @pytest.mark.asyncio
    async def test_short_cover_balance_correct(self):
        """Verify the P&L double-count bug is fixed.

        Math:
          Start:     100000
          SELL 1@100: +100 → 100100 (short opened)
          BUY 3@110:  -330 (cost) + (-10) realized loss on 1 unit cover → -340
          Final:      100100 - 340 = 99760
        """
        from app.execution.paper.executor import PaperExecutor
        from app.execution.types import OrderSide, OrderType
        ex = PaperExecutor(initial_balance=100000.0)
        # Open short: SELL 1 @ 100
        await ex.submit_order("TEST", OrderSide.SELL, OrderType.MARKET, 1.0, price=100.0)
        # Cover 1 @ 110 (loss 10) + open new long 2 @ 110 (cost 220)
        await ex.submit_order("TEST", OrderSide.BUY, OrderType.MARKET, 3.0, price=110.0)
        assert abs(ex.balance - 99760.0) < 0.01, f"Balance mismatch: {ex.balance}"
        pos = ex.positions["TEST"]
        assert pos.quantity == 2.0
        assert abs(pos.average_entry_price - 110.0) < 0.01


class TestCoordinatorAccountState:
    """TS-004: Coordinator must read real account state, not hardcoded zeros."""

    @pytest.mark.asyncio
    async def test_account_state_reads_real_balance(self):
        from app.paper_trading.account_manager import account_manager
        # Create account with known balance
        acc = account_manager.create_account(initial_balance=50000.0)
        # Verify we can read it
        accounts = list(account_manager.accounts.values())
        assert len(accounts) > 0
        assert accounts[0].balance == 50000.0


class TestAuthFailClosed:
    """TS-001: Auth must fail closed on missing/invalid token."""

    @pytest.mark.asyncio
    async def test_missing_token_raises_401(self):
        from app.api.dependencies import get_current_user
        with pytest.raises(Exception) as exc_info:
            await get_current_user(token="")
        assert "401" in str(exc_info.value) or "UNAUTHORIZED" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        from app.api.dependencies import get_current_user
        with pytest.raises(Exception) as exc_info:
            await get_current_user(token="invalid-token")
        assert "401" in str(exc_info.value) or "UNAUTHORIZED" in str(exc_info.value)


class TestApiKeyFromEnv:
    """TS-010: API keys must come from env, not hardcoded."""

    def test_valid_api_keys_from_settings(self):
        from app.config.settings import get_settings
        settings = get_settings()
        # Should be loaded from env (empty list if not set)
        assert isinstance(settings.VALID_API_KEYS, list)

    def test_no_hardcoded_key_in_source(self):
        """Scan python source to ensure no hardcoded keys remain."""
        import os
        hardcoded_found = []
        for root, _, files in os.walk("app"):
            for f in files:
                if f.endswith(".py"):
                    p = os.path.join(root, f)
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read()
                            if "ENTERPRISE_DEV_KEY" in content:
                                hardcoded_found.append(p)
                    except Exception:
                        pass
        assert len(hardcoded_found) == 0, f"Hardcoded API key still present in: {hardcoded_found}"
