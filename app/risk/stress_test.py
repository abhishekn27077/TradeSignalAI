from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class StressTestEngine:
    SCENARIOS = {
        "market_crash": {"name": "Market Crash", "description": "Simulates a sudden market crash", "default_impact": -0.15},
        "flash_crash": {"name": "Flash Crash", "description": "Rapid price drop and recovery", "default_impact": -0.08},
        "gap_risk": {"name": "Gap Risk", "description": "Overnight gap in prices", "default_impact": -0.05},
        "volatility_shock": {"name": "Volatility Shock", "description": "Sudden volatility spike", "default_impact": -0.03},
        "liquidity_crisis": {"name": "Liquidity Crisis", "description": "Widening spreads, low volume", "default_impact": -0.10},
        "interest_rate_hike": {"name": "Interest Rate Hike", "description": "Unexpected rate increase", "default_impact": -0.06},
    }

    def get_scenario(self, scenario_name: str) -> dict[str, Any] | None:
        scenario = self.SCENARIOS.get(scenario_name)
        if scenario is None:
            logger.warning(f"Unknown scenario: {scenario_name}")
            names = list(self.SCENARIOS.keys())
            return {
                "name": scenario_name,
                "description": "Unknown scenario",
                "default_impact": -0.05,
                "available_scenarios": names,
            }
        return dict(scenario)

    def list_scenarios(self) -> dict[str, dict[str, Any]]:
        return dict(self.SCENARIOS)

    def run_scenario(self, scenario_name: str, portfolio_value: float = 100000.0) -> dict[str, Any]:
        scenario = self.get_scenario(scenario_name)
        impact = scenario.get("default_impact", -0.05) if scenario else -0.05
        loss = portfolio_value * abs(impact)
        return {
            "scenario": scenario_name,
            "description": scenario.get("description", "") if scenario else "",
            "portfolio_value": portfolio_value,
            "estimated_loss": loss,
            "loss_pct": abs(impact) * 100,
            "remaining": portfolio_value - loss,
        }


stress_test_engine = StressTestEngine()