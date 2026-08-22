from typing import Any

import pandas as pd

from app.logs.logger import get_logger

logger = get_logger(__name__)

class SMCLiquidityEngine:
    """
    Advanced Liquidity Engine for SMC.
    Detects EQH/EQL, BSL/SSL, Sweeps, Stop Hunts, and assigns confidence/rankings.
    """
    def __init__(self, tolerance_pips=5.0, sweep_threshold_pips=2.0):
        self.tolerance = tolerance_pips
        self.sweep_threshold = sweep_threshold_pips
        
    def detect_equal_highs_lows(self, df: pd.DataFrame, window=20) -> tuple:
        eqh, eql = [], []
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(len(df)):
            for j in range(i+1, min(i+window, len(df))):
                if abs(highs[i] - highs[j]) <= self.tolerance:
                    eqh.append({"price": highs[i], "idx1": i, "idx2": j, "type": "EQH"})
                if abs(lows[i] - lows[j]) <= self.tolerance:
                    eql.append({"price": lows[i], "idx1": i, "idx2": j, "type": "EQL"})
                    
        return eqh, eql

    def detect_sweeps(self, df: pd.DataFrame, zones: list[dict]) -> list[dict]:
        """Check if any zones were recently swept and rejected"""
        sweeps = []
        recent_bars = df.tail(5) # Look at last 5 bars for sweeps
        
        for zone in zones:
            for idx, row in recent_bars.iterrows():
                # Bullish Sweep (Stop Hunt of EQL/SSL)
                if zone["type"] in ["EQL", "SSL"]:
                    if row['low'] < zone["price"] and row['close'] > zone["price"]:
                        sweeps.append({
                            "zone_price": zone["price"],
                            "sweep_type": "BULLISH_SWEEP",
                            "confidence": 0.85 if row['close'] > (row['high'] + row['low'])/2 else 0.60
                        })
                # Bearish Sweep (Stop Hunt of EQH/BSL)
                elif zone["type"] in ["EQH", "BSL"]:
                    if row['high'] > zone["price"] and row['close'] < zone["price"]:
                        sweeps.append({
                            "zone_price": zone["price"],
                            "sweep_type": "BEARISH_SWEEP",
                            "confidence": 0.85 if row['close'] < (row['high'] + row['low'])/2 else 0.60
                        })
        return sweeps

    def rank_liquidity_zones(self, zones: list[dict]) -> list[dict]:
        for zone in zones:
            # Assign confidence based on type
            zone["confidence"] = 0.90 if zone["type"] in ["BSL", "SSL"] else 0.70
        return zones

    def analyze(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < 20:
            return {"zones": [], "sweeps": []}
            
        eqh, eql = self.detect_equal_highs_lows(df)
        
        # Simple BSL / SSL derived from daily highs/lows for now
        bsl = [{"price": df['high'].rolling(50).max().iloc[-1], "type": "BSL"}]
        ssl = [{"price": df['low'].rolling(50).min().iloc[-1], "type": "SSL"}]
        
        all_zones = self.rank_liquidity_zones(eqh + eql + bsl + ssl)
        sweeps = self.detect_sweeps(df, all_zones)
        
        return {
            "zones": all_zones,
            "sweeps": sweeps,
            "has_bullish_sweep": any(s["sweep_type"] == "BULLISH_SWEEP" for s in sweeps),
            "has_bearish_sweep": any(s["sweep_type"] == "BEARISH_SWEEP" for s in sweeps)
        }

liquidity_engine = SMCLiquidityEngine()