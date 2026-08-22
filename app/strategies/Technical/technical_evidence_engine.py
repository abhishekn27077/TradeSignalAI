import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.Technical.indicators import (
    compute_atr, compute_rsi, compute_adx, compute_macd, compute_vwap
)
from app.strategies.Technical.supertrend import compute_supertrend
from app.strategies.Technical.ut_bot import compute_ut_bot


@dataclass
class IndicatorEvidence:
    indicator: str
    value: float
    state: str
    direction: Direction
    strength: float
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "value": float(self.value),
            "state": self.state,
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "strength": float(self.strength),
            "confidence": float(self.confidence),
            "details": self.details,
        }


class TechnicalEvidenceEngine:
    """
    Evaluates multi-indicator technical evidence and produces structured evidence objects.
    Evidence does not trigger standalone trades; it feeds the Confluence & Router engines.
    """

    def evaluate_evidence(self, df: pd.DataFrame, asset: str = "UNKNOWN", timeframe: str = "1H") -> Dict[str, IndicatorEvidence]:
        if df is None or len(df) < 20:
            return {}

        evidence: Dict[str, IndicatorEvidence] = {}
        close = df['close'].iloc[-1]

        # 1. ATR (Volatility baseline)
        atr_series = compute_atr(df, period=14)
        latest_atr = float(atr_series.iloc[-1])
        atr_pct = (latest_atr / close) * 100.0 if close > 0 else 0.0
        evidence["ATR"] = IndicatorEvidence(
            indicator="ATR",
            value=latest_atr,
            state="NORMAL_VOLATILITY" if atr_pct < 2.0 else "HIGH_VOLATILITY",
            direction=Direction.NEUTRAL,
            strength=min(1.0, atr_pct / 2.0),
            confidence=0.90,
            details={"atr_pct": atr_pct}
        )

        # 2. ADX / DMI (Trend Strength)
        adx, p_di, m_di = compute_adx(df, period=14)
        latest_adx = float(adx.iloc[-1])
        latest_pdi = float(p_di.iloc[-1])
        latest_mdi = float(m_di.iloc[-1])

        if latest_adx > 25.0:
            adx_dir = Direction.BULLISH if latest_pdi > latest_mdi else Direction.BEARISH
            adx_state = "STRONG_TREND"
        else:
            adx_dir = Direction.NEUTRAL
            adx_state = "WEAK_RANGE"

        evidence["ADX"] = IndicatorEvidence(
            indicator="ADX",
            value=latest_adx,
            state=adx_state,
            direction=adx_dir,
            strength=min(1.0, latest_adx / 50.0),
            confidence=0.85,
            details={"plus_di": latest_pdi, "minus_di": latest_mdi}
        )

        # 3. RSI (Momentum / Exhaustion)
        rsi_series = compute_rsi(df, period=14)
        latest_rsi = float(rsi_series.iloc[-1])

        if latest_rsi >= 70.0:
            rsi_dir = Direction.BEARISH  # Overbought exhaustion / mean-reversion bias
            rsi_state = "OVERBOUGHT"
        elif latest_rsi <= 30.0:
            rsi_dir = Direction.BULLISH  # Oversold exhaustion / bounce bias
            rsi_state = "OVERSOLD"
        elif latest_rsi >= 55.0:
            rsi_dir = Direction.BULLISH
            rsi_state = "BULLISH_MOMENTUM"
        elif latest_rsi <= 45.0:
            rsi_dir = Direction.BEARISH
            rsi_state = "BEARISH_MOMENTUM"
        else:
            rsi_dir = Direction.NEUTRAL
            rsi_state = "NEUTRAL"

        evidence["RSI"] = IndicatorEvidence(
            indicator="RSI",
            value=latest_rsi,
            state=rsi_state,
            direction=rsi_dir,
            strength=abs(latest_rsi - 50.0) / 50.0,
            confidence=0.80,
            details={"rsi_14": latest_rsi}
        )

        # 4. MACD (Momentum Crossover)
        macd_line, sig_line, hist = compute_macd(df)
        latest_hist = float(hist.iloc[-1])
        latest_macd = float(macd_line.iloc[-1])

        macd_dir = Direction.BULLISH if latest_hist > 0 else Direction.BEARISH
        macd_state = "MOMENTUM_EXPANDING" if abs(latest_hist) > abs(float(hist.iloc[-2])) else "MOMENTUM_CONTRACTING"

        evidence["MACD"] = IndicatorEvidence(
            indicator="MACD",
            value=latest_macd,
            state=macd_state,
            direction=macd_dir,
            strength=min(1.0, abs(latest_hist) / (latest_atr + 1e-6)),
            confidence=0.80,
            details={"histogram": latest_hist, "signal_line": float(sig_line.iloc[-1])}
        )

        # 5. SMA 200 (Macro Regime Filter)
        if len(df) >= 200:
            sma_200 = float(df['close'].rolling(window=200).mean().iloc[-1])
            sma_dir = Direction.BULLISH if close > sma_200 else Direction.BEARISH
            dist_pct = ((close - sma_200) / sma_200) * 100.0
            evidence["SMA200"] = IndicatorEvidence(
                indicator="SMA200",
                value=sma_200,
                state="ABOVE_SMA200" if close > sma_200 else "BELOW_SMA200",
                direction=sma_dir,
                strength=min(1.0, abs(dist_pct) / 5.0),
                confidence=0.90,
                details={"dist_pct": dist_pct}
            )

        # 6. SuperTrend
        st_val, st_dir = compute_supertrend(df, period=10, multiplier=3.0)
        latest_st_dir = int(st_dir.iloc[-1])
        evidence["SUPERTREND"] = IndicatorEvidence(
            indicator="SUPERTREND",
            value=float(st_val.iloc[-1]),
            state="BULLISH_TREND" if latest_st_dir == 1 else "BEARISH_TREND",
            direction=Direction.BULLISH if latest_st_dir == 1 else Direction.BEARISH,
            strength=0.85,
            confidence=0.85,
            details={"band_price": float(st_val.iloc[-1])}
        )

        # 7. UT Bot Alerts
        ut_stop, ut_pos = compute_ut_bot(df, key_value=1.0, atr_period=10)
        latest_ut_pos = int(ut_pos.iloc[-1])
        evidence["UT_BOT"] = IndicatorEvidence(
            indicator="UT_BOT",
            value=float(ut_stop.iloc[-1]),
            state="LONG_BIAS" if latest_ut_pos == 1 else "SHORT_BIAS",
            direction=Direction.BULLISH if latest_ut_pos == 1 else Direction.BEARISH,
            strength=0.80,
            confidence=0.80,
            details={"trailing_stop": float(ut_stop.iloc[-1])}
        )

        # 8. VWAP
        vwap_series = compute_vwap(df)
        latest_vwap = float(vwap_series.iloc[-1])
        evidence["VWAP"] = IndicatorEvidence(
            indicator="VWAP",
            value=latest_vwap,
            state="ABOVE_VWAP" if close > latest_vwap else "BELOW_VWAP",
            direction=Direction.BULLISH if close > latest_vwap else Direction.BEARISH,
            strength=min(1.0, abs(close - latest_vwap) / (latest_atr + 1e-6)),
            confidence=0.85,
            details={"vwap_price": latest_vwap}
        )

        return evidence
