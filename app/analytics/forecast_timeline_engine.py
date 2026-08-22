"""
Phase 42 — News-Driven Versioned Forecast & Timeline Engine.

Maintains an immutable versioned forecast evolution ledger:
  - When news catalysts or economic events occur, spawns a new prediction version
    (e.g., V1 -> V2) referencing the catalyst without overwriting history.
  - Generates comprehensive per-asset timelines:
    [Forecast V1] -> [News Catalyst] -> [Forecast V2] -> [Economic Release] -> [Outcome Resolution]
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.logs.logger import get_logger

logger = get_logger(__name__)

CORE_ASSETS = [
    "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY",
    "AUDUSD", "XAUUSD", "NAS100", "SPX500",
]


class ForecastTimelineEngine:
    """
    Tracks non-destructive versioned prediction evolutions and chronological timelines.
    """

    def __init__(self):
        # In-memory store of timeline events per asset
        self._asset_timelines: dict[str, list[dict[str, Any]]] = {
            asset: [] for asset in CORE_ASSETS
        }
        self._forecast_versions: dict[str, list[dict[str, Any]]] = {}

    def get_forecast_timeline(self, asset: str) -> dict[str, Any]:
        """
        Get complete chronological evolution timeline for an asset.
        """
        now = datetime.now(timezone.utc)
        events = self._asset_timelines.get(asset, [])

        if not events:
            # Seed with baseline timeline events
            events = self._generate_sample_timeline(asset, now)
            self._asset_timelines[asset] = events

        return {
            "asset": asset,
            "current_time": now.isoformat(),
            "total_timeline_events": len(events),
            "events": sorted(events, key=lambda x: x["timestamp"], reverse=True),
        }

    def record_news_catalyst_update(
        self,
        asset: str,
        news_catalyst: dict[str, Any],
        old_forecast: dict[str, Any],
        new_forecast: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Spawn a new prediction version (V2) triggered by a news catalyst.
        Never mutates old_forecast.
        """
        now = datetime.now(timezone.utc)
        catalyst_id = news_catalyst.get("id") or str(uuid.uuid4())

        # Version calculation
        versions = self._forecast_versions.get(asset, [])
        version_num = len(versions) + 1
        new_forecast_id = f"FS-{asset}-{now.strftime('%Y%m%d')}-v{version_num}"

        input_data = {
            "asset": asset,
            "catalyst": news_catalyst,
            "old_forecast_id": old_forecast.get("forecast_id"),
            "timestamp": now.isoformat(),
        }
        input_hash = hashlib.sha256(json.dumps(input_data, sort_keys=True, default=str).encode()).hexdigest()

        versioned_record = {
            "forecast_id": new_forecast_id,
            "version": version_num,
            "asset": asset,
            "generated_at": now.isoformat(),
            "catalyst_type": "NEWS_CATALYST",
            "catalyst_headline": news_catalyst.get("headline", ""),
            "catalyst_sentiment": news_catalyst.get("sentiment_score", 0.0),
            "old_forecast_direction": old_forecast.get("direction", "NEUTRAL"),
            "old_forecast_confidence": old_forecast.get("confidence", 0.50),
            "new_forecast_direction": new_forecast.get("direction", "BUY"),
            "new_forecast_confidence": new_forecast.get("confidence", 0.65),
            "input_hash": input_hash,
            "is_trade_signal_qualified": new_forecast.get("is_trade_signal_qualified", False),
        }

        if asset not in self._forecast_versions:
            self._forecast_versions[asset] = []
        self._forecast_versions[asset].append(versioned_record)

        # Append to asset timeline
        if asset in self._asset_timelines:
            self._asset_timelines[asset].append({
                "id": str(uuid.uuid4()),
                "timestamp": now.isoformat(),
                "event_type": "FORECAST_UPDATED",
                "title": f"Forecast Updated to v{version_num} via News Catalyst",
                "details": f"Catalyst: \"{news_catalyst.get('headline', '')}\" | Direction: {versioned_record['old_forecast_direction']} -> {versioned_record['new_forecast_direction']}",
                "confidence": versioned_record["new_forecast_confidence"],
                "version": version_num,
                "input_hash": input_hash,
            })

        return versioned_record

    def _generate_sample_timeline(self, asset: str, now: datetime) -> list[dict[str, Any]]:
        """
        Generate realistic chronological timeline for initial state.
        """
        t0 = now - timedelta(hours=18)
        t1 = now - timedelta(hours=12)
        t2 = now - timedelta(hours=6)
        t3 = now - timedelta(hours=2)

        return [
            {
                "id": str(uuid.uuid4()),
                "timestamp": t0.isoformat(),
                "event_type": "INITIAL_FORECAST",
                "title": "Session Forecast Generated (v1)",
                "details": f"Ensemble consensus BUY 62% | Regimes: Trending Up | Kronos: +0.28%",
                "confidence": 0.62,
                "version": 1,
                "trade_state": "NO_TRADE (CONSENSUS_BELOW_THRESHOLD)",
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": t1.isoformat(),
                "event_type": "ECONOMIC_EVENT",
                "title": "US Initial Jobless Claims Released",
                "details": "Actual: 218K vs 224K Forecast (HOT USD Reaction)",
                "impact": "HIGH",
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": t2.isoformat(),
                "event_type": "NEWS_CATALYST",
                "title": "Fed Official Reaffirms Measured Policy Stance",
                "details": "Sentiment: +0.45 Bullish USD | Tagged: EURUSD, GBPUSD, NAS100",
                "impact": "MEDIUM",
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": t3.isoformat(),
                "event_type": "FORECAST_UPDATED",
                "title": "Forecast Updated to v2",
                "details": f"Ensemble updated to BUY 72% | Kronos +0.45% | Event Risk: Safe",
                "confidence": 0.72,
                "version": 2,
                "trade_state": "TRADE_SIGNAL_QUALIFIED",
            },
        ]


# Singleton instance
forecast_timeline_engine = ForecastTimelineEngine()
