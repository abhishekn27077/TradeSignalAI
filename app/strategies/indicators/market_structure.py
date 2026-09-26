"""
market_structure.py
───────────────────
Market Structure + Liquidity Zone Engine.

Detects:
- Higher High (HH), Higher Low (HL), Lower High (LH), Lower Low (LL)
- Break Of Structure (BOS)
- Change Of Character (CHOCH)
- Liquidity Zones: PDH, PDL, Weekly High, Weekly Low, Major swing highs/lows
- Liquidity Sweeps: BSL, SSL, PDH/PDL/WH/WL sweeps (via liquidity_sweep module)
"""
from dataclasses import dataclass, field

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)
from app.strategies.indicators.otc.liquidity_sweep import (
    LiquiditySweepResult,
    detect_liquidity_sweeps,
)


@dataclass
class MarketStructureResult:
    trend: str = "SIDEWAYS"           # "BULLISH", "BEARISH", "SIDEWAYS"
    recent_bos: str | None = None  # "CALL", "PUT", None
    recent_choch: str | None = None # "CALL", "PUT", None
    distance_to_pdh: float = 999.0
    distance_to_pdl: float = 999.0
    near_opposing_liquidity: bool = False
    liquidity_zones: dict = field(default_factory=dict)
    # ── Liquidity Sweep fields ─────────────────────────────────────────────
    sweep_result: LiquiditySweepResult | None = None  # full sweep analysis
    sweep_direction: str | None = None   # "CALL" | "PUT" | None
    sweep_confidence: float = 0.0           # 0–100
    has_strong_sweep: bool = False          # True if any strong sweep detected
    
class MarketStructureEngine:
    def __init__(self, pivot_left=5, pivot_right=5, proximity_threshold_pips=5.0):
        self.pivot_left = pivot_left
        self.pivot_right = pivot_right
        self.proximity_threshold_pips = proximity_threshold_pips

    def analyse(self, df: pd.DataFrame) -> MarketStructureResult:
        if df is None or len(df) < self.pivot_left + self.pivot_right + 1:
            return MarketStructureResult()
            
        last = df.iloc[-1]
        close = last["close"]
        
        # 1. Identify Liquidity Zones (PDH, PDL, Weekly H/L)
        pdh, pdl, wh, wl = None, None, None, None
        
        if isinstance(df.index, pd.DatetimeIndex):
            # Extract previous day
            daily_highs = df.groupby(df.index.date)['high'].max()
            daily_lows = df.groupby(df.index.date)['low'].min()
            
            dates = daily_highs.index.sort_values()
            if len(dates) >= 2:
                prev_date = dates[-2]
                pdh = daily_highs.loc[prev_date]
                pdl = daily_lows.loc[prev_date]
                
            # Weakly High / Low (ISO week)
            try:
                weekly_highs = df.groupby(df.index.isocalendar().week)['high'].max()
                weekly_lows = df.groupby(df.index.isocalendar().week)['low'].min()
                weeks = weekly_highs.index.sort_values()
                if len(weeks) >= 2:
                    prev_week = weeks[-2]
                    wh = weekly_highs.loc[prev_week]
                    wl = weekly_lows.loc[prev_week]
            except Exception:
                pass
                
        # 2. Market Structure (Pivots) - Strictly Causal Confirmation
        # A pivot at (t - pivot_right) is confirmed at current bar t using only data up to t (no future data)
        window = self.pivot_left + self.pivot_right + 1
        rolling_max = df['high'].rolling(window=window, center=False).max()
        rolling_min = df['low'].rolling(window=window, center=False).min()
        cand_high = df['high'].shift(self.pivot_right)
        cand_low = df['low'].shift(self.pivot_right)
        
        pivot_highs = df[cand_high == rolling_max]['high'].dropna()
        pivot_lows = df[cand_low == rolling_min]['low'].dropna()
        
        trend = "SIDEWAYS"
        bos = None
        choch = None
        
        if not pivot_highs.empty and not pivot_lows.empty:
            last_ph = pivot_highs.iloc[-1]
            prev_ph = pivot_highs.iloc[-2] if len(pivot_highs) > 1 else None
            last_pl = pivot_lows.iloc[-1]
            prev_pl = pivot_lows.iloc[-2] if len(pivot_lows) > 1 else None
            
            hh = (prev_ph is not None and last_ph > prev_ph)
            lh = (prev_ph is not None and last_ph < prev_ph)
            hl = (prev_pl is not None and last_pl > prev_pl)
            ll = (prev_pl is not None and last_pl < prev_pl)
            
            if hh and hl:
                trend = "BULLISH"
            elif lh and ll:
                trend = "BEARISH"
                
            # Evaluate breaks
            # Look at recent candles (after the last confirmed pivot)
            # Find the index of the last confirmed pivot
            last_ph_idx = pivot_highs.index[-1]
            last_pl_idx = pivot_lows.index[-1]
            
            recent_candles = df.loc[max(last_ph_idx, last_pl_idx):]
            if not recent_candles.empty:
                max_recent_close = recent_candles['close'].max()
                min_recent_close = recent_candles['close'].min()
                
                if max_recent_close > last_ph:
                    if trend == "BULLISH":
                        bos = "CALL"
                    elif trend == "BEARISH":
                        choch = "CALL"
                elif min_recent_close < last_pl:
                    if trend == "BEARISH":
                        bos = "PUT"
                    elif trend == "BULLISH":
                        choch = "PUT"
                    
        # 3. Liquidity proximity
        pip_multiplier = 10000.0
        distance_to_pdh = (pdh - close) * pip_multiplier if pdh else 999.0
        distance_to_pdl = (close - pdl) * pip_multiplier if pdl else 999.0
        
        near_opposing = False
        if bos == "CALL" or choch == "CALL" or trend == "BULLISH":
            if pdh and abs(distance_to_pdh) < self.proximity_threshold_pips:
                near_opposing = True
        elif bos == "PUT" or choch == "PUT" or trend == "BEARISH":
            if pdl and abs(distance_to_pdl) < self.proximity_threshold_pips:
                near_opposing = True
                
        zones = {"PDH": pdh, "PDL": pdl, "WH": wh, "WL": wl}

        # ── Liquidity Sweep Detection ──────────────────────────────────────
        sweep_result = detect_liquidity_sweeps(df, zones)

        return MarketStructureResult(
            trend=trend,
            recent_bos=bos,
            recent_choch=choch,
            distance_to_pdh=abs(distance_to_pdh),
            distance_to_pdl=abs(distance_to_pdl),
            near_opposing_liquidity=near_opposing,
            liquidity_zones=zones,
            sweep_result=sweep_result,
            sweep_direction=sweep_result.dominant_direction if sweep_result.detected else None,
            sweep_confidence=sweep_result.sweep_confidence,
            has_strong_sweep=sweep_result.has_strong_sweep,
        )

market_structure_engine = MarketStructureEngine()

