import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Technical.indicators import compute_adx, compute_atr, compute_rsi


class MarketRegime(str, Enum):
    STRONG_TREND = "STRONG_TREND"
    WEAK_TREND = "WEAK_TREND"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    TRANSITION = "TRANSITION"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class RegimeClassification:
    asset: str
    timeframe: str
    regime: MarketRegime
    adx_value: float
    atr_normalized: float
    rsi_value: float
    trend_direction: str
    confidence: float
    timestamp_utc: datetime
    timestamp_ist: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "regime": self.regime.value if hasattr(self.regime, 'value') else str(self.regime),
            "adx_value": float(self.adx_value),
            "atr_normalized": float(self.atr_normalized),
            "rsi_value": float(self.rsi_value),
            "trend_direction": self.trend_direction,
            "confidence": float(self.confidence),
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "details": self.details,
        }


class RegimeClassifier:
    """
    Multi-Factor Market Regime Classifier.
    Evaluates ADX, ATR Volatility expansion, and momentum compression to classify dynamic market regimes.
    """

    def classify_regime(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> RegimeClassification:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        if df is None or len(df) < 25:
            return RegimeClassification(
                asset=asset,
                timeframe=timeframe,
                regime=MarketRegime.UNCERTAIN,
                adx_value=20.0,
                atr_normalized=1.0,
                rsi_value=50.0,
                trend_direction="NEUTRAL",
                confidence=0.5,
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        close = df['close'].iloc[-1]
        adx, p_di, m_di = compute_adx(df, period=14)
        latest_adx = float(adx.iloc[-1])
        latest_pdi = float(p_di.iloc[-1])
        latest_mdi = float(m_di.iloc[-1])

        atr_series = compute_atr(df, period=14)
        latest_atr = float(atr_series.iloc[-1])
        avg_atr = float(atr_series.tail(50).mean())
        atr_ratio = latest_atr / (avg_atr + 1e-6)

        rsi_series = compute_rsi(df, period=14)
        latest_rsi = float(rsi_series.iloc[-1])

        # Trend direction
        if latest_pdi > latest_mdi:
            trend_dir = "BULLISH"
        elif latest_mdi > latest_pdi:
            trend_dir = "BEARISH"
        else:
            trend_dir = "NEUTRAL"

        # Classification rules
        if atr_ratio > 1.8:
            regime = MarketRegime.HIGH_VOLATILITY
            confidence = 0.90
        elif atr_ratio < 0.6:
            regime = MarketRegime.LOW_VOLATILITY
            confidence = 0.85
        elif latest_adx >= 32.0:
            regime = MarketRegime.STRONG_TREND
            confidence = 0.92
        elif latest_adx >= 22.0:
            regime = MarketRegime.WEAK_TREND
            confidence = 0.80
        elif abs(latest_rsi - 50.0) < 10.0 and latest_adx < 20.0:
            regime = MarketRegime.RANGE
            confidence = 0.88
        elif latest_adx > 20.0 and atr_ratio > 1.3:
            regime = MarketRegime.BREAKOUT
            confidence = 0.82
        else:
            regime = MarketRegime.TRANSITION
            confidence = 0.70

        return RegimeClassification(
            asset=asset,
            timeframe=timeframe,
            regime=regime,
            adx_value=latest_adx,
            atr_normalized=atr_ratio,
            rsi_value=latest_rsi,
            trend_direction=trend_dir,
            confidence=confidence,
            timestamp_utc=now_utc,
            timestamp_ist=now_ist,
            details={"atr_ratio": atr_ratio, "plus_di": latest_pdi, "minus_di": latest_mdi}
        )
