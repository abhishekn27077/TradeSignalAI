from datetime import datetime
from typing import Any


class StatisticsTracker:
    """Tracks daily and monthly statistics for paper accounts."""
    
    def __init__(self):
        self.daily_pnl: dict[str, float] = {}
        self.trade_count: dict[str, int] = {}
        self.win_count: dict[str, int] = {}
        self.loss_count: dict[str, int] = {}

    def record_trade(self, account_id: str, pnl: float):
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"{account_id}_{date_str}"
        
        self.daily_pnl[key] = self.daily_pnl.get(key, 0.0) + pnl
        self.trade_count[key] = self.trade_count.get(key, 0) + 1
        
        if pnl > 0:
            self.win_count[key] = self.win_count.get(key, 0) + 1
        else:
            self.loss_count[key] = self.loss_count.get(key, 0) + 1

    def get_daily_stats(self, account_id: str, date: datetime = None) -> dict[str, Any]:
        target_date = date or datetime.utcnow()
        date_str = target_date.strftime("%Y-%m-%d")
        key = f"{account_id}_{date_str}"
        
        trades = self.trade_count.get(key, 0)
        wins = self.win_count.get(key, 0)
        win_rate = wins / trades if trades > 0 else 0.0
        
        return {
            "date": date_str,
            "daily_pnl": self.daily_pnl.get(key, 0.0),
            "trades": trades,
            "win_rate": win_rate
        }

stats_tracker = StatisticsTracker()
