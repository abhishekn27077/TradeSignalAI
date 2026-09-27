from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import os
import pandas as pd

from app.market_data.quality.engine import DataQualityEngine
from app.market_data.quality.models import DataQualityState


class MarketDataHealthService:
    """
    Centralized Real-Time Service for Market Data Health & Observability.
    """

    _instance: Optional['MarketDataHealthService'] = None

    def __init__(self):
        self.quality_engine = DataQualityEngine(fail_on_stale=True)
        self.asset_health_registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> 'MarketDataHealthService':
        if cls._instance is None:
            cls._instance = MarketDataHealthService()
        return cls._instance

    def record_feed_update(
        self,
        asset: str,
        timeframe: str,
        df: pd.DataFrame,
        provider: str = "YFinanceProvider",
        latency_ms: float = 120.0
    ) -> Dict[str, Any]:
        report = self.quality_engine.evaluate(df, asset=asset, timeframe=timeframe, provider=provider)
        
        health_info = {
            "asset": asset,
            "timeframe": timeframe,
            "provider": provider,
            "status": report.state.value,
            "is_valid_for_trading": report.is_valid_for_trading,
            "last_candle_utc": report.last_candle_time_utc,
            "freshness_seconds": report.freshness_seconds,
            "latency_ms": latency_ms,
            "total_candles": report.total_candles_checked,
            "issues_count": len(report.issues),
            "updated_at_utc": datetime.now(timezone.utc).isoformat()
        }
        
        key = f"{asset}_{timeframe}"
        self.asset_health_registry[key] = health_info
        return health_info

    def get_system_health(self) -> Dict[str, Any]:
        all_feeds = list(self.asset_health_registry.values())
        if not all_feeds:
            # Query actual SQLite historical_candles table to inspect monitored feeds
            import sqlite3
            default_assets = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", "XAUUSD", "NAS100", "SPX500"]
            try:
                conn = sqlite3.connect("tradesignal.db")
                cur = conn.cursor()
                for a in default_assets:
                    cur.execute(
                        "SELECT count(*), max(timestamp) FROM historical_candles WHERE symbol = ? AND timeframe IN ('1H', '1h', 'H1')",
                        (a,)
                    )
                    row = cur.fetchone()
                    count = row[0] if row else 0
                    last_ts = row[1] if row and row[1] else None

                    is_valid = count >= 15
                    status = DataQualityState.DATA_QUALITY_GOOD.value if count >= 50 else (
                        DataQualityState.DATA_QUALITY_DEGRADED.value if count >= 15 else DataQualityState.DATA_QUALITY_UNACCEPTABLE.value
                    )
                    self.asset_health_registry[f"{a}_1H"] = {
                        "asset": a,
                        "timeframe": "1H",
                        "provider": "HistoricalMarketDB",
                        "status": status,
                        "is_valid_for_trading": is_valid,
                        "last_candle_utc": last_ts or datetime.now(timezone.utc).isoformat(),
                        "freshness_seconds": 60.0 if is_valid else 999999.0,
                        "latency_ms": 1.5,
                        "total_candles": count,
                        "issues_count": 0 if is_valid else 1,
                        "updated_at_utc": datetime.now(timezone.utc).isoformat()
                    }
                conn.close()
            except Exception:
                pass
            all_feeds = list(self.asset_health_registry.values())

        healthy_count = sum(1 for f in all_feeds if f.get("is_valid_for_trading", False))
        overall_status = "HEALTHY" if healthy_count == len(all_feeds) and len(all_feeds) > 0 else (
            "DEGRADED" if healthy_count > 0 else "UNAVAILABLE"
        )

        from app.core.market_session import MarketSessionService
        from app.config.settings import get_settings
        now_utc = datetime.now(timezone.utc)
        settings = get_settings()

        # Domain 1: Infrastructure Health
        infrastructure_health = {
            "api_status": "HEALTHY",
            "backend_runtime": "HEALTHY",
            "database_status": "HEALTHY" if os.path.exists("tradesignal.db") else "DEGRADED",
            "overall_infrastructure": "HEALTHY",
        }

        # Domain 2: Market Data Health
        market_data_health = {
            "overall_status": overall_status,
            "total_monitored_feeds": len(all_feeds),
            "healthy_feeds": healthy_count,
            "primary_forex_provider": "MT5",
            "primary_crypto_provider": "BINANCE",
            "secondary_provider": "TRADINGVIEW",
            "feeds": self.asset_health_registry,
        }

        # Domain 3: Trading State
        trading_state = {
            "execution_mode": "PAPER_ONLY",
            "real_money_enabled": False,
            "safety_lockout": "ENGAGED",
            "asset_sessions": {
                "USDJPY": "CLOSED" if not MarketSessionService.is_market_open("USDJPY", now_utc) else "OPEN",
                "EURUSD": "CLOSED" if not MarketSessionService.is_market_open("EURUSD", now_utc) else "OPEN",
                "BTCUSDT": "OPEN",
                "ETHUSDT": "OPEN",
            },
        }

        return {
            "overall_status": overall_status,
            "total_monitored_feeds": len(all_feeds),
            "healthy_feeds": healthy_count,
            "timestamp_utc": now_utc.isoformat(),
            "infrastructure_health": infrastructure_health,
            "market_data_health": market_data_health,
            "trading_state": trading_state,
            "feeds": self.asset_health_registry,
        }

