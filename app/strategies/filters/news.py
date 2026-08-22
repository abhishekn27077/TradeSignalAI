from datetime import datetime, timedelta
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

class EconomicNewsFilter:
    """
    Fetches economic calendar events and blocks trading around high-impact news.
    """
    def __init__(self, block_before_mins=30, block_after_mins=30):
        self.block_before = timedelta(minutes=block_before_mins)
        self.block_after = timedelta(minutes=block_after_mins)
        self.cached_events = [] # Should be updated via a background task

    def fetch_events(self):
        """
        Placeholder for fetching from ForexFactory, FMP, or similar.
        In production, this should run once a day or via websocket.
        """
        # Mock high impact event today at 13:30 UTC (e.g. CPI/NFP)
        now = datetime.utcnow()
        mock_event_time = now.replace(hour=13, minute=30, second=0, microsecond=0)
        self.cached_events = [
            {"title": "US CPI", "impact": "HIGH", "time": mock_event_time}
        ]

    def analyze(self, current_time: datetime, symbol: str = "ALL") -> dict[str, Any]:
        if not self.cached_events:
            self.fetch_events()
            
        status = "SAFE"
        confidence_adj = 0.0
        affected = []
        impact_level = "NONE"
        recommendation = "Normal Trading"

        for event in self.cached_events:
            if event["impact"] == "HIGH":
                event_time = event["time"]
                # If current_time is within the block window
                if event_time - self.block_before <= current_time <= event_time + self.block_after:
                    status = "BLOCKED"
                    confidence_adj = -0.18 # Phase 6: e.g. -18% for High Impact USD
                    impact_level = "HIGH"
                    affected = ["BTC/USD", "ETH/USD", "EUR/USD"] # Mock list for demo
                    recommendation = "Trading Disabled or Reduced Size"
                    break
                    
        return {
            "news_status": status,
            "can_trade": status == "SAFE",
            "impact": impact_level,
            "affected_symbols": affected,
            "confidence_adjustment": confidence_adj,
            "trading_recommendation": recommendation
        }

news_filter = EconomicNewsFilter()
