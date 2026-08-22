from datetime import datetime


class EquityCurveGenerator:
    """Formats equity data for charting."""
    
    @staticmethod
    def format_curve(equity_history: list[tuple[datetime, float]]) -> list[dict]:
        return [
            {"time": ts.isoformat(), "equity": eq} 
            for ts, eq in equity_history
        ]

class PerformanceAnalyzer:
    """Analyzes benchmark vs strategy performance."""
    
    @staticmethod
    def compare_to_benchmark(strategy_return: float, benchmark_return: float) -> float:
        """Returns alpha (outperformance)."""
        return strategy_return - benchmark_return
