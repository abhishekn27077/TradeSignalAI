from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd

from app.core.market_clock import MarketClockService
from app.market_data.quality.models import DataQualityState


@dataclass
class MarketDataSnapshot:
    """
    Authoritative Canonical Market Data Snapshot.
    All downstream analytical and decision engines must consume this standard object.
    """
    asset: str
    provider: str
    symbol: str
    timeframe: str
    timestamp_utc: str
    timestamp_ist: str
    open: float
    high: float
    low: float
    close: float
    bid: float
    ask: float
    mid: float
    volume: float
    data_age_ms: float
    candle_closed: bool
    quality_state: DataQualityState
    is_valid_for_trading: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "provider": self.provider,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp_utc": self.timestamp_utc,
            "timestamp_ist": self.timestamp_ist,
            "open": round(float(self.open), 5),
            "high": round(float(self.high), 5),
            "low": round(float(self.low), 5),
            "close": round(float(self.close), 5),
            "bid": round(float(self.bid), 5),
            "ask": round(float(self.ask), 5),
            "mid": round(float(self.mid), 5),
            "volume": round(float(self.volume), 2),
            "data_age_ms": round(float(self.data_age_ms), 1),
            "candle_closed": self.candle_closed,
            "quality_state": self.quality_state.value,
            "is_valid_for_trading": self.is_valid_for_trading,
            "details": self.details,
        }


class CanonicalMarketDataService:
    """
    Canonical Market Data Normalizer & Factory.
    """

    @staticmethod
    def create_snapshot(
        asset: str,
        df: pd.DataFrame,
        provider: str = "YAHOO_FINANCE",
        symbol_override: Optional[str] = None,
        timeframe: str = "1H",
        spread_pips: float = 1.2,
    ) -> MarketDataSnapshot:
        if df is None or df.empty:
            now_utc = datetime.now(timezone.utc)
            return MarketDataSnapshot(
                asset=asset,
                provider=provider,
                symbol=symbol_override or asset,
                timeframe=timeframe,
                timestamp_utc=now_utc.isoformat(),
                timestamp_ist=MarketClockService.format_ist(now_utc),
                open=0.0,
                high=0.0,
                low=0.0,
                close=0.0,
                bid=0.0,
                ask=0.0,
                mid=0.0,
                volume=0.0,
                data_age_ms=999999.0,
                candle_closed=False,
                quality_state=DataQualityState.DATA_UNAVAILABLE,
                is_valid_for_trading=False,
                details={"error": "Empty or None DataFrame"}
            )

        last_row = df.iloc[-1]
        ts = pd.to_datetime(last_row.get("timestamp", datetime.now(timezone.utc)), utc=True)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        age_ms = max(0.0, (now_utc - ts).total_seconds() * 1000.0)

        close_p = float(last_row.get("close", 0.0))
        open_p = float(last_row.get("open", close_p))
        high_p = float(last_row.get("high", close_p))
        low_p = float(last_row.get("low", close_p))
        volume = float(last_row.get("volume", 0.0))

        if "bid" in last_row and "ask" in last_row and pd.notna(last_row["bid"]) and pd.notna(last_row["ask"]):
            bid = float(last_row["bid"])
            ask = float(last_row["ask"])
            mid = (bid + ask) / 2.0
        else:
            pip_scale = 0.01 if "JPY" in asset or "XAU" in asset else (1.0 if "BTC" in asset or "ETH" in asset or "NAS" in asset else 0.0001)
            half_spread = (spread_pips * pip_scale) / 2.0
            bid = close_p - half_spread
            ask = close_p + half_spread
            mid = close_p

        # Validation
        is_corrupted = (low_p > high_p) or (open_p < 0) or (close_p < 0) or (high_p < 0) or (low_p < 0)
        is_stale = (age_ms > 3600 * 2.5 * 1000.0)

        if is_corrupted:
            quality = DataQualityState.DATA_CORRUPTED
            valid = False
        elif is_stale:
            quality = DataQualityState.DATA_STALE
            valid = False
        else:
            quality = DataQualityState.DATA_QUALITY_GOOD
            valid = True

        return MarketDataSnapshot(
            asset=asset,
            provider=provider,
            symbol=symbol_override or asset,
            timeframe=timeframe,
            timestamp_utc=ts.isoformat(),
            timestamp_ist=MarketClockService.format_ist(ts),
            open=open_p,
            high=high_p,
            low=low_p,
            close=close_p,
            bid=bid,
            ask=ask,
            mid=mid,
            volume=volume,
            data_age_ms=age_ms,
            candle_closed=True,
            quality_state=quality,
            is_valid_for_trading=valid,
            details={"pip_scale": pip_scale, "spread_pips": spread_pips}
        )
