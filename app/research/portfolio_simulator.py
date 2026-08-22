from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

class PortfolioSimulator:
    """
    Simulates equity curves across custom capital requirements.
    """
    def __init__(self):
        pass

    def run_simulation(self, initial_capital: float, trade_list: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Takes a list of trades from a backtest and simulates an equity curve.
        """
        equity = initial_capital
        curve = [{"step": 0, "equity": equity}]
        
        peak = equity
        max_drawdown = 0.0
        
        for i, trade in enumerate(trade_list):
            pnl = trade.get("pnl", 0.0)
            equity += pnl
            
            peak = max(peak, equity)
            
            dd = (peak - equity) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, dd)
                
            curve.append({"step": i+1, "equity": equity})
            
        return {
            "final_equity": equity,
            "return_pct": ((equity - initial_capital) / initial_capital) * 100,
            "max_drawdown_pct": max_drawdown * 100,
            "curve": curve
        }

portfolio_simulator = PortfolioSimulator()
