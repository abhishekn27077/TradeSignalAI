from typing import Any

from app.validation.engine import validation_engine


class ValidationReports:
    async def generate(self, period: str) -> dict[str, Any]:
        """
        Generate enterprise validation reports.
        """
        metrics = await validation_engine.compute_metrics(period)
        rankings = await validation_engine.get_rankings(period)
        
        # Format rankings for frontend
        top_assets = [{"asset": item["name"], "win_rate": item["win_rate"]} for item in rankings.get("top_assets", [])]
        top_timeframes = [{"timeframe": item["name"], "win_rate": item["win_rate"]} for item in rankings.get("top_timeframes", [])]
        top_strategies = [{"strategy": item["name"], "profit_factor": item["profit_factor"]} for item in rankings.get("top_strategies", [])]
        
        # Return the actual computed rankings, no mock data
        return {
            "period": period,
            "title": f"{period.capitalize()} Validation Report",
            "summary": f"System computed from actual historical data. Win rate: {metrics.get('win_rate', 0)*100:.1f}%.",
            "metrics": metrics,
            "rankings": {
                "top_assets": top_assets,
                "top_timeframes": top_timeframes,
                "top_strategies": top_strategies
            }
        }

validation_reports = ValidationReports()
