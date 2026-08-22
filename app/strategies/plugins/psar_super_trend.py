import uuid
from typing import Any

import numpy as np
import pandas as pd

from app.strategies.plugins.registry import register_strategy_metadata
from app.strategies.strategy_engine.core import BaseStrategy
from app.strategies.strategy_engine.metadata import (
    MarketRegime,
    RiskProfile,
    StrategyCategory,
    StrategyMetadata,
)
from app.strategies.strategy_engine.types import (
    RiskLevel,
    SignalDirection,
    SignalStrength,
    StrategySignal,
    Timeframe,
)


def compute_psar(high, low, close, acceleration=0.02, max_acceleration=0.2):
    length = len(high)
    psar = np.zeros(length)
    af = np.zeros(length)
    trend = np.zeros(length, dtype=int)
    ep = np.zeros(length)
    psar[0] = low[0]
    af[0] = acceleration
    trend[0] = 1
    ep[0] = high[0]
    for i in range(1, length):
        if trend[i - 1] == 1:
            psar[i] = psar[i - 1] + af[i - 1] * (ep[i - 1] - psar[i - 1])
            if low[i] < psar[i]:
                trend[i] = -1
                psar[i] = ep[i - 1]
                ep[i] = low[i]
                af[i] = acceleration
            else:
                trend[i] = 1
                if high[i] > ep[i - 1]:
                    ep[i] = high[i]
                    af[i] = min(af[i - 1] + acceleration, max_acceleration)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]
        else:
            psar[i] = psar[i - 1] - af[i - 1] * (psar[i - 1] - ep[i - 1])
            if high[i] > psar[i]:
                trend[i] = 1
                psar[i] = ep[i - 1]
                ep[i] = high[i]
                af[i] = acceleration
            else:
                trend[i] = -1
                if low[i] < ep[i - 1]:
                    ep[i] = low[i]
                    af[i] = min(af[i - 1] + acceleration, max_acceleration)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]
    psar = np.where(psar == 0, low, psar)
    return psar, trend


def compute_supertrend(high, low, close, period=10, multiplier=3.0):
    length = len(high)
    tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - close[:-1]))
    tr = np.maximum(tr, np.abs(low[1:] - close[:-1]))
    tr = np.concatenate([[tr[0]], tr])
    atr = pd.Series(tr).ewm(span=period, adjust=False).mean().values
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    supertrend = np.zeros(length)
    direction = np.zeros(length, dtype=int)
    for i in range(1, length):
        if close[i] > upper_band[i]:
            direction[i] = 1
        elif close[i] < lower_band[i]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
        if direction[i] == 1:
            supertrend[i] = lower_band[i]
        else:
            supertrend[i] = upper_band[i]
    return supertrend, direction


def compute_ema(series, period):
    return pd.Series(series).ewm(span=period, adjust=False).mean().values


def compute_adx(high, low, close, period=14):
    length = len(high)
    tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - close[:-1]))
    tr = np.maximum(tr, np.abs(low[1:] - close[:-1]))
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    tr = np.concatenate([[tr[0]], tr])
    plus_dm = np.concatenate([[0], plus_dm])
    minus_dm = np.concatenate([[0], minus_dm])
    tr_smooth = pd.Series(tr).ewm(span=period, adjust=False).mean().values
    plus_smooth = pd.Series(plus_dm).ewm(span=period, adjust=False).mean().values
    minus_smooth = pd.Series(minus_dm).ewm(span=period, adjust=False).mean().values
    plus_di = 100 * plus_smooth / np.where(tr_smooth > 0, tr_smooth, 1)
    minus_di = 100 * minus_smooth / np.where(tr_smooth > 0, tr_smooth, 1)
    dx = 100 * np.abs(plus_di - minus_di) / np.where((plus_di + minus_di) > 0, (plus_di + minus_di), 1)
    adx = pd.Series(dx).ewm(span=period, adjust=False).mean().values
    return adx, plus_di, minus_di


def compute_atr(high, low, close, period=14):
    length = len(high)
    tr = np.maximum(high[1:] - low[1:], np.abs(high[1:] - close[:-1]))
    tr = np.maximum(tr, np.abs(low[1:] - close[:-1]))
    tr = np.concatenate([[tr[0]], tr])
    return pd.Series(tr).ewm(span=period, adjust=False).mean().values


class PSARSuperTrendH4Strategy(BaseStrategy):
    metadata = StrategyMetadata(
        name="PSARSuperTrendH4Strategy",
        description="Professional H4 strategy combining Parabolic SAR reversal with SuperTrend, EMA200 trend filter, ADX momentum, and ATR volatility confirmation. Entry only on new H4 candle open. Only the first PSAR reversal dot counts.",
        version="2.0.0",
        category=StrategyCategory.HYBRID,
        supported_assets=["forex", "crypto", "indices"],
        supported_timeframes=["4H"],
        supported_regimes=[MarketRegime.TRENDING, MarketRegime.STRONG_TRENDING, MarketRegime.BREAKOUT],
        entry_rules=[
            "First Parabolic SAR reversal below price (BUY) or above price (SELL)",
            "SuperTrend must confirm direction",
            "EMA200 must align with trade direction",
            "ADX above configurable threshold (default 25)",
            "ATR confirms acceptable volatility",
            "Only the FIRST reversal PSAR dot counts - no consecutive signals",
        ],
        exit_rules=[
            "PSAR reversal opposite direction",
            "SuperTrend flip",
            "Maximum holding time reached",
            "Stop loss hit",
            "Take profit hit",
        ],
        required_indicators=["PSAR", "SuperTrend", "EMA200", "ADX", "ATR"],
        risk_profile=RiskProfile.MEDIUM,
        priority=8,
        weight=1.0,
        max_concurrent_trades=2,
        daily_trade_limit=4,
    )

    def __init__(self, name: str = "PSARSuperTrendH4Strategy", params: dict[str, Any] = None):
        super().__init__(name, params)
        self._last_psar_trend = None
        self._signaled_this_bar = False
        self._current_bar_index = -1
        self._last_signal_bar = -1
        self.adx_threshold = (params or {}).get("adx_threshold", 25)
        self.atr_multiplier = (params or {}).get("atr_multiplier", 1.0)
        self.psar_acceleration = (params or {}).get("psar_acceleration", 0.02)
        self.psar_max_acceleration = (params or {}).get("psar_max_acceleration", 0.2)
        self.supertrend_period = (params or {}).get("supertrend_period", 10)
        self.supertrend_multiplier = (params or {}).get("supertrend_multiplier", 3.0)

    def initialize(self):
        super().initialize()
        self._last_psar_trend = None
        self._signaled_this_bar = False
        self._current_bar_index = -1
        self._last_signal_bar = -1

    def reset(self):
        super().reset()
        self._last_psar_trend = None
        self._signaled_this_bar = False
        self._current_bar_index = -1
        self._last_signal_bar = -1

    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignal | None:
        if len(data) < 100:
            return None

        high = data['high'].values.astype(float)
        low = data['low'].values.astype(float)
        close = data['close'].values.astype(float)
        volume = data['volume'].values.astype(float) if 'volume' in data.columns else np.ones(len(data))

        psar, psar_trend = compute_psar(high, low, close, self.psar_acceleration, self.psar_max_acceleration)
        _, st_direction = compute_supertrend(high, low, close, self.supertrend_period, self.supertrend_multiplier)
        ema200 = compute_ema(close, 200)
        adx, plus_di, minus_di = compute_adx(high, low, close)
        atr = compute_atr(high, low, close)

        i = -1
        last = data.iloc[i]
        prev = data.iloc[-2] if len(data) >= 2 else data.iloc[-1]

        if self._last_psar_trend is None:
            self._last_psar_trend = psar_trend[i]

        current_price = close[i]
        ema200_val = ema200[i] if not np.isnan(ema200[i]) else current_price
        adx_val = adx[i] if not np.isnan(adx[i]) else 0
        atr_val = atr[i] if not np.isnan(atr[i]) else 0

        atr_mean = np.nanmean(atr[-50:]) if len(atr) >= 50 else atr_val
        atr_ok = atr_val >= atr_mean * 0.5 and atr_val <= atr_mean * 3.0 if atr_mean > 0 else True
        adx_ok = adx_val >= self.adx_threshold

        if not adx_ok or not atr_ok:
            return None

        current_trend = psar_trend[i]
        prev_trend = psar_trend[-2] if len(psar_trend) >= 2 else current_trend

        psar_reversal = (prev_trend == -1 and current_trend == 1) or (prev_trend == 1 and current_trend == -1)
        first_reversal = True
        if self._last_signal_bar == len(data) - 1:
            first_reversal = False

        if not psar_reversal:
            self._last_psar_trend = current_trend
            return None

        if not first_reversal:
            self._last_psar_trend = current_trend
            return None

        if current_trend == 1:
            st_bullish = st_direction[i] == 1
            ema_bullish = current_price > ema200_val
            if st_bullish and ema_bullish:
                confidence = 0.75
                if adx_val >= 30:
                    confidence = min(0.95, confidence + 0.10)
                if abs(current_price - ema200_val) / ema200_val < 0.03:
                    confidence = min(0.95, confidence + 0.05)
                self._last_signal_bar = len(data) - 1
                return StrategySignal(
                    signal_id=str(uuid.uuid4()),
                    strategy_name=self.name,
                    asset=symbol,
                    timeframe=Timeframe.H4,
                    direction=SignalDirection.BUY,
                    confidence=confidence,
                    strength=SignalStrength.STRONG if confidence >= 0.80 else SignalStrength.MODERATE,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=(
                        f"BUY: PSAR reversal bullish + SuperTrend bullish + EMA200 bullish. "
                        f"ADX={adx_val:.1f}, ATR={atr_val:.5f}. "
                        f"First reversal PSAR dot confirmed."
                    ),
                    supporting_indicators=["PSAR", "SuperTrend", "EMA200", "ADX", "ATR"],
                    stop_loss_suggestion=current_price - (atr_val * 2.0),
                    take_profit_suggestion=current_price + (atr_val * 3.0),
                )
        elif current_trend == -1:
            st_bearish = st_direction[i] == -1
            ema_bearish = current_price < ema200_val
            if st_bearish and ema_bearish:
                confidence = 0.75
                if adx_val >= 30:
                    confidence = min(0.95, confidence + 0.10)
                if abs(current_price - ema200_val) / ema200_val < 0.03:
                    confidence = min(0.95, confidence + 0.05)
                self._last_signal_bar = len(data) - 1
                return StrategySignal(
                    signal_id=str(uuid.uuid4()),
                    strategy_name=self.name,
                    asset=symbol,
                    timeframe=Timeframe.H4,
                    direction=SignalDirection.SELL,
                    confidence=confidence,
                    strength=SignalStrength.STRONG if confidence >= 0.80 else SignalStrength.MODERATE,
                    risk_level=RiskLevel.MEDIUM,
                    reasoning=(
                        f"SELL: PSAR reversal bearish + SuperTrend bearish + EMA200 bearish. "
                        f"ADX={adx_val:.1f}, ATR={atr_val:.5f}. "
                        f"First reversal PSAR dot confirmed."
                    ),
                    supporting_indicators=["PSAR", "SuperTrend", "EMA200", "ADX", "ATR"],
                    stop_loss_suggestion=current_price + (atr_val * 2.0),
                    take_profit_suggestion=current_price - (atr_val * 3.0),
                )

        return None


register_strategy_metadata("PSARSuperTrendH4Strategy", PSARSuperTrendH4Strategy.metadata)
