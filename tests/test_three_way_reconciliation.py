"""
tests/test_three_way_reconciliation.py
======================================
Test Suite for Production 3-Way Position & Order Reconciliation.

Benchmarked against QuantConnect LEAN and NautilusTrader reconciliation models.
Verifies alignment across:
1. Internal Position Manager
2. External / Paper Broker
3. Authoritative Canonical Prospective Ledger
Ensures no silent divergence.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.execution.reconciliation import ReconciliationEngine


class TestThreeWayReconciliation:
    def setup_method(self):
        self.engine = ReconciliationEngine()

    @pytest.mark.asyncio
    async def test_3way_perfect_match(self):
        """When all three sources align, status is MATCHED and mismatch_count is 0."""
        pos_internal = [{"symbol": "EURUSD", "quantity": 1.0, "average_entry_price": 1.1000}]
        pos_external = [{"symbol": "EURUSD", "quantity": 1.0, "average_entry_price": 1.1000}]
        pos_ledger = [{"symbol": "EURUSD", "signal_id": "SIG-1", "entry_price": 1.1000}]

        with patch.object(self.engine, "_get_internal_positions", return_value=pos_internal), \
             patch.object(self.engine, "_get_paper_positions", return_value=(pos_external, True)), \
             patch.object(self.engine, "_get_ledger_positions", return_value=(pos_ledger, True)):

            res = await self.engine.run_3way_reconciliation()
            assert res["status"] == "MATCHED"
            assert res["mismatch_count"] == 0
            assert res["internal_count"] == 1
            assert res["external_count"] == 1
            assert res["ledger_count"] == 1

    @pytest.mark.asyncio
    async def test_3way_detects_ledger_desync(self):
        """When position is active live but missing from ledger, LEDGER_DESYNC is flagged."""
        pos_internal = [{"symbol": "BTCUSD", "quantity": 0.5, "average_entry_price": 60000.0}]
        pos_external = [{"symbol": "BTCUSD", "quantity": 0.5, "average_entry_price": 60000.0}]
        pos_ledger = []  # Missing from ledger!

        with patch.object(self.engine, "_get_internal_positions", return_value=pos_internal), \
             patch.object(self.engine, "_get_paper_positions", return_value=(pos_external, True)), \
             patch.object(self.engine, "_get_ledger_positions", return_value=(pos_ledger, True)):

            res = await self.engine.run_3way_reconciliation()
            assert res["status"] == "MISMATCH"
            issues = [m["issue"] for m in res["mismatches"]]
            assert "LEDGER_DESYNC" in issues

    @pytest.mark.asyncio
    async def test_3way_detects_orphan_ledger_signal(self):
        """When signal is marked ACTIVE in ledger but no live position exists, ORPHAN_LEDGER_SIGNAL is flagged."""
        pos_internal = []
        pos_external = []
        pos_ledger = [{"symbol": "XAUUSD", "signal_id": "SIG-GOLD", "entry_price": 2500.0}]

        with patch.object(self.engine, "_get_internal_positions", return_value=pos_internal), \
             patch.object(self.engine, "_get_paper_positions", return_value=(pos_external, True)), \
             patch.object(self.engine, "_get_ledger_positions", return_value=(pos_ledger, True)):

            res = await self.engine.run_3way_reconciliation()
            assert res["status"] == "MISMATCH"
            issues = [m["issue"] for m in res["mismatches"]]
            assert "ORPHAN_LEDGER_SIGNAL" in issues

    @pytest.mark.asyncio
    async def test_3way_fail_closed_on_source_failure(self):
        """When broker or ledger is unreachable, status resolves to UNKNOWN, never MATCHED."""
        with patch.object(self.engine, "_get_internal_positions", return_value=[]), \
             patch.object(self.engine, "_get_paper_positions", return_value=([], False)), \
             patch.object(self.engine, "_get_ledger_positions", return_value=([], True)):

            res = await self.engine.run_3way_reconciliation()
            assert res["status"] == "UNKNOWN"
            assert res["broker_available"] is False
