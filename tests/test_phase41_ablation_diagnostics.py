"""
Phase 41 — Test Suite for Model Ablation & Signal Generation Diagnostics.

Verifies:
  - 8-configuration empirical ablation comparison (Quant only vs Ensemble)
  - Incremental alpha calculations vs baseline
  - Scan-level diagnostics across all 9 assets
  - Transparent gate-level rejection reasons for disqualified setups
"""
import pytest
from app.analytics.ablation_engine import model_ablation_engine
from app.analytics.signal_diagnostics_engine import signal_diagnostics_engine, CORE_ASSETS


class TestAblationEngine:
    def test_ablation_benchmark_results(self):
        res = model_ablation_engine.run_ablation_benchmark(sample_limit=100)
        assert res["status"] == "SUCCESS"
        assert "ablation_results" in res
        assert len(res["ablation_results"]) == 8

        # Verify baseline exists
        baseline = next(r for r in res["ablation_results"] if r["config_id"] == "quant_only")
        assert baseline is not None
        assert baseline["win_rate_pct"] > 0

        # Verify full consensus ensemble
        ensemble = next(r for r in res["ablation_results"] if r["config_id"] == "full_consensus")
        assert ensemble["win_rate_pct"] > baseline["win_rate_pct"]
        assert ensemble["profit_factor"] > baseline["profit_factor"]
        assert ensemble["contribution_vs_baseline"]["win_rate_delta_pct"] > 0


@pytest.mark.asyncio
class TestSignalDiagnosticsEngine:
    async def test_diagnostics_for_all_9_assets(self):
        res = await signal_diagnostics_engine.get_diagnostics()
        assert res["total_assets_scanned"] == len(CORE_ASSETS)
        assert len(res["diagnostics"]) == len(CORE_ASSETS)

        for diag in res["diagnostics"]:
            assert diag["asset"] in CORE_ASSETS
            assert "forecast_direction" in diag
            assert "forecast_probability" in diag
            assert "risk_decision" in diag
            assert diag["risk_decision"] in ["APPROVED", "BLOCKED"]
            assert diag["final_state"] in ["TRADE_SIGNAL_EMITTED", "NO_VALID_SETUP"]

            # If NO_VALID_SETUP, must have non-empty rejection reason
            if diag["final_state"] == "NO_VALID_SETUP":
                assert len(diag["summary_reason"]) > 0
                assert len(diag["rejection_reasons"]) > 0

    async def test_rejection_summary_categories(self):
        res = await signal_diagnostics_engine.get_diagnostics()
        assert "rejection_summary" in res
        summary = res["rejection_summary"]
        expected_keys = ["CONSENSUS_BELOW_THRESHOLD", "HIGH_EVENT_RISK", "RR_BELOW_MINIMUM", "DATA_STALE", "NEUTRAL_BIAS"]
        for k in expected_keys:
            assert k in summary
            assert summary[k] >= 0
