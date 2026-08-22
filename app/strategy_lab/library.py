from typing import Any


class StrategyLibrary:
    def __init__(self):
        self.strategies = [
            {
                "id": "strat_101",
                "name": "Mean Reversion Alpha",
                "version": "1.0.0",
                "creator": "System",
                "created_at": "2026-07-28T10:00:00Z",
                "performance": {"win_rate": 62.4, "profit_factor": 1.45},
                "supported_assets": ["BTCUSD", "ETHUSD"],
                "timeframes": ["H4", "D1"],
                "status": "Qualified"
            },
            {
                "id": "strat_102",
                "name": "Volatility Breakout Delta",
                "version": "2.1.0",
                "creator": "System",
                "created_at": "2026-07-29T08:00:00Z",
                "performance": {"win_rate": 51.2, "profit_factor": 1.10},
                "supported_assets": ["EURUSD", "GBPUSD"],
                "timeframes": ["H1"],
                "status": "Walk-Forward Tested"
            }
        ]

    def get_all(self) -> list[dict[str, Any]]:
        return self.strategies

strategy_library = StrategyLibrary()
