from typing import Any

import numpy as np

from app.logs.logger import get_logger

logger = get_logger(__name__)

class MonteCarloEngine:
    """
    Phase 11: Monte Carlo Simulation Engine
    Resamples historical trades to simulate N different equity curves,
    calculating Risk of Ruin and expected max drawdowns.
    """
    def __init__(self, num_simulations: int = 1000, risk_of_ruin_threshold_pct: float = 20.0):
        self.num_simulations = num_simulations
        self.risk_of_ruin_threshold_pct = risk_of_ruin_threshold_pct

    def run_simulation(self, initial_capital: float, trades: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Runs Monte Carlo simulation on an array of trade dicts containing 'pnl' (in USD).
        """
        if not trades:
            return {"error": "No trades to simulate"}
            
        pnls = [t.get("pnl", 0.0) for t in trades]
        num_trades = len(pnls)
        
        simulated_equity_curves = []
        ruin_count = 0
        max_drawdowns = []
        
        ruin_value = initial_capital * (1 - (self.risk_of_ruin_threshold_pct / 100))
        
        for i in range(self.num_simulations):
            # Sample with replacement
            sampled_pnls = np.random.choice(pnls, size=num_trades, replace=True)
            
            # Create equity curve
            equity_curve = initial_capital + np.cumsum(sampled_pnls)
            simulated_equity_curves.append(equity_curve)
            
            # Check Risk of Ruin
            if np.any(equity_curve <= ruin_value):
                ruin_count += 1
                
            # Calculate Max Drawdown
            running_max = np.maximum.accumulate(equity_curve)
            drawdowns = (running_max - equity_curve) / running_max
            max_drawdowns.append(np.max(drawdowns))
            
        risk_of_ruin_prob = (ruin_count / self.num_simulations) * 100
        median_max_dd = np.median(max_drawdowns) * 100
        worst_max_dd = np.max(max_drawdowns) * 100
        
        return {
            "simulations_run": self.num_simulations,
            "risk_of_ruin_prob_pct": round(float(risk_of_ruin_prob), 2),
            "median_max_dd_pct": round(float(median_max_dd), 2),
            "worst_case_dd_pct": round(float(worst_max_dd), 2)
        }

monte_carlo_engine = MonteCarloEngine()
