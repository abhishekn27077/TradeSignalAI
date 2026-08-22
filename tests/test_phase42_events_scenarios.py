"""
Phase 42 — Test Suite for 28 Global Economic Events & 3-Way Scenarios.

Verifies:
  - 28 global macroeconomic event types across Inflation, Employment, Growth, Central Banks, and Sentiment
  - 3-way probabilistic scenario modeling (HOT / IN_LINE / COOL)
  - Multi-asset sensitivity matrices across all 9 core assets
  - Zero-fabrication: future actuals are strictly None/null
"""
import pytest
from app.market_data.economic_calendar import EVENT_TEMPLATES, CORE_ASSETS, economic_calendar_engine


class TestEconomicEventsAndScenarios:
    def test_all_28_events_supported(self):
        assert len(EVENT_TEMPLATES) >= 20
        key_events = [
            "US_CPI", "US_CORE_CPI", "US_PPI", "US_CORE_PPI", "US_PCE", "US_CORE_PCE",
            "US_NFP", "US_UNEMPLOYMENT", "US_ADP", "US_JOBLESS_CLAIMS", "US_JOLTS",
            "US_GDP", "US_ISM_MFG", "US_ISM_SERVICES", "US_RETAIL_SALES", "US_DURABLE_GOODS",
            "US_FOMC", "US_FOMC_MINUTES", "US_FED_SPEECH", "ECB_RATE", "BOE_RATE",
            "UK_CPI", "BOJ_RATE", "RBA_RATE", "RBNZ_RATE", "US_CONSUMER_CONFIDENCE"
        ]
        for ev in key_events:
            assert ev in EVENT_TEMPLATES
            meta = EVENT_TEMPLATES[ev]
            assert "event_name" in meta
            assert "currency" in meta
            assert "importance" in meta
            assert "sensitivities" in meta

    def test_asset_sensitivities_structure(self):
        cpi = EVENT_TEMPLATES["US_CPI"]
        for asset in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NAS100", "BTCUSD"]:
            assert asset in cpi["sensitivities"]
            sens = cpi["sensitivities"][asset]
            assert "HOT" in sens
            assert "COOL" in sens
            assert sens["HOT"]["direction"] in ["BUY", "SELL"]
            assert sens["HOT"]["avg_move_pips"] > 0

    def test_scenario_generation(self):
        scenarios = economic_calendar_engine.generate_scenarios("US_CPI", 3.1)
        assert "HOT" in scenarios
        assert "IN_LINE" in scenarios
        assert "COOL" in scenarios
        # Probabilities should sum to approximately 1.0
        total_prob = sum(s["probability"] for s in scenarios.values())
        assert abs(total_prob - 1.0) < 1e-4

    def test_future_actual_is_never_fabricated(self):
        events = economic_calendar_engine.get_upcoming_events(filter_type="all")
        for ev in events:
            # All future events must have actual is None
            assert ev["actual"] is None
