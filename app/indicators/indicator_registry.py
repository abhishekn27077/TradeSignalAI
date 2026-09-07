"""
app/indicators/indicator_registry.py
====================================
Indicator Registry & Evidence Cluster Architecture for TradeSignalAI-v3.

Ensures:
1. Strict classification of all indicators/community strategies:
   - SUPPORTED (Validated non-repainting, causal, can vote in production consensus)
   - EXPERIMENTAL (Under evaluation, votes in shadow consensus only)
   - UNVERIFIED (Needs historical backtest validation)
   - REPAINTING (Repaints on bar close or uses future bars -> REJECTED from consensus)
   - LOOKAHEAD_RISK (Uses request.security or unconfirmed candles -> BLOCKED)
   - INSUFFICIENT_DATA (Requires missing inputs)
   - REJECTED (Failed causal audit)

2. Correlation-Aware Evidence Clustering:
   Prevents correlated indicators from inflating consensus votes.
   Clusters:
   - TREND_CLUSTER
   - MOMENTUM_CLUSTER
   - STRUCTURE_CLUSTER
   - LIQUIDITY_CLUSTER
   - VOLATILITY_CLUSTER
   - VOLUME_CLUSTER
   - FORECAST_MODEL_CLUSTER
   - HISTORICAL_ANALOG_CLUSTER
   - EVENT_CLUSTER
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class IndicatorStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    EXPERIMENTAL = "EXPERIMENTAL"
    UNVERIFIED = "UNVERIFIED"
    REPAINTING = "REPAINTING"
    LOOKAHEAD_RISK = "LOOKAHEAD_RISK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    REJECTED = "REJECTED"


class EvidenceClusterType(str, Enum):
    TREND_CLUSTER = "TREND_CLUSTER"
    MOMENTUM_CLUSTER = "MOMENTUM_CLUSTER"
    STRUCTURE_CLUSTER = "STRUCTURE_CLUSTER"
    LIQUIDITY_CLUSTER = "LIQUIDITY_CLUSTER"
    VOLATILITY_CLUSTER = "VOLATILITY_CLUSTER"
    VOLUME_CLUSTER = "VOLUME_CLUSTER"
    FORECAST_MODEL_CLUSTER = "FORECAST_MODEL_CLUSTER"
    HISTORICAL_ANALOG_CLUSTER = "HISTORICAL_ANALOG_CLUSTER"
    EVENT_CLUSTER = "EVENT_CLUSTER"


@dataclass
class IndicatorDefinition:
    indicator_id: str
    name: str
    source: str  # "NATIVE", "COMMUNITY", "TRADINGVIEW_PINESCRIPT", "MACHINE_LEARNING"
    version: str
    cluster: EvidenceClusterType
    status: IndicatorStatus
    timeframes: List[str]
    non_repainting: bool
    confirmation_delay_bars: int
    lookahead_risk: str  # "NONE", "HIGH", "UNVERIFIED"
    repaint_risk: str     # "NONE", "INTRABAR_ONLY", "SEVERE"
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "name": self.name,
            "source": self.source,
            "version": self.version,
            "cluster": self.cluster.value,
            "status": self.status.value,
            "timeframes": self.timeframes,
            "non_repainting": self.non_repainting,
            "confirmation_delay_bars": self.confirmation_delay_bars,
            "lookahead_risk": self.lookahead_risk,
            "repaint_risk": self.repaint_risk,
            "description": self.description,
            "parameters": self.parameters,
        }


class IndicatorRegistry:
    """
    Central repository of validated indicators, evidence clusters, and repainting audits.
    """

    def __init__(self):
        self._indicators: Dict[str, IndicatorDefinition] = {}
        self._register_default_indicators()

    def _register_default_indicators(self):
        # ── 1. TREND CLUSTER ──────────────────────────────────────────────────
        self.register(IndicatorDefinition(
            indicator_id="ema_trend_ribbon",
            name="EMA Multi-Period Ribbon (20/50/200)",
            source="NATIVE",
            version="2.0.0",
            cluster=EvidenceClusterType.TREND_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["5m", "15m", "30m", "1H", "2H", "4H", "12H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Exponential moving average alignment across fast (20), medium (50), and baseline (200) periods.",
            parameters={"periods": [20, 50, 200]}
        ))

        self.register(IndicatorDefinition(
            indicator_id="supertrend",
            name="SuperTrend ATR Trailing Band",
            source="NATIVE",
            version="1.5.0",
            cluster=EvidenceClusterType.TREND_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "30m", "1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="ATR-based adaptive volatility trend band.",
            parameters={"period": 10, "multiplier": 3.0}
        ))

        self.register(IndicatorDefinition(
            indicator_id="adaptive_regression_breakout",
            name="Adaptive Regression Breakout Map",
            source="COMMUNITY",
            version="1.2.0",
            cluster=EvidenceClusterType.TREND_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=1,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Linear regression channel with dynamic polynomial deviation bands.",
            parameters={"length": 50, "dev": 2.0}
        ))

        # ── 2. MOMENTUM CLUSTER ───────────────────────────────────────────────
        self.register(IndicatorDefinition(
            indicator_id="rsi_wilder",
            name="RSI (Wilder Smoothed 14)",
            source="NATIVE",
            version="2.0.0",
            cluster=EvidenceClusterType.MOMENTUM_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["5m", "15m", "30m", "1H", "2H", "4H", "12H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Wilder-smoothed Relative Strength Index tracking momentum acceleration and exhaustion.",
            parameters={"period": 14, "overbought": 70.0, "oversold": 30.0}
        ))

        self.register(IndicatorDefinition(
            indicator_id="macd_standard",
            name="MACD (12/26/9 Standard)",
            source="NATIVE",
            version="1.0.0",
            cluster=EvidenceClusterType.MOMENTUM_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "30m", "1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Moving average convergence divergence momentum oscillator.",
            parameters={"fast": 12, "slow": 26, "signal": 9}
        ))

        self.register(IndicatorDefinition(
            indicator_id="reversal_trap_bands",
            name="Reversal Trap Probability Bands",
            source="COMMUNITY",
            version="1.1.0",
            cluster=EvidenceClusterType.MOMENTUM_CLUSTER,
            status=IndicatorStatus.EXPERIMENTAL,
            timeframes=["15m", "1H", "4H"],
            non_repainting=True,
            confirmation_delay_bars=1,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Detects momentum exhaustion and false breakout traps using volume-weighted standard deviation.",
            parameters={"band_width": 2.5}
        ))

        # ── 3. STRUCTURE CLUSTER ──────────────────────────────────────────────
        self.register(IndicatorDefinition(
            indicator_id="smc_bos_choch",
            name="Smart Money Structure (BOS & CHoCH)",
            source="NATIVE",
            version="3.0.0",
            cluster=EvidenceClusterType.STRUCTURE_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=1,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Break of Structure (BOS) and Change of Character (CHoCH) swing high/low mapping.",
            parameters={"swing_length": 5}
        ))

        self.register(IndicatorDefinition(
            indicator_id="amd_po3_engine",
            name="AMD Power of 3 Engine (Accumulation/Manipulation/Distribution)",
            source="COMMUNITY",
            version="2.0.0",
            cluster=EvidenceClusterType.STRUCTURE_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "1H", "4H"],
            non_repainting=True,
            confirmation_delay_bars=1,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Intraday & multi-day session Power of 3 cycle detection with expansion phase confirmation.",
            parameters={"session_bars": 24}
        ))

        self.register(IndicatorDefinition(
            indicator_id="elliott_impulse_engine",
            name="Elliott Impulse Engine",
            source="COMMUNITY",
            version="1.0.0",
            cluster=EvidenceClusterType.STRUCTURE_CLUSTER,
            status=IndicatorStatus.EXPERIMENTAL,
            timeframes=["1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=2,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Algorithmic 5-wave impulse and 3-wave corrective pattern identifier.",
            parameters={"depth": 10}
        ))

        # ── 4. LIQUIDITY CLUSTER ──────────────────────────────────────────────
        self.register(IndicatorDefinition(
            indicator_id="liquidity_sweep_hunter",
            name="Liquidity Sweep Hunter (Equal Highs/Lows)",
            source="COMMUNITY",
            version="2.1.0",
            cluster=EvidenceClusterType.LIQUIDITY_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "1H", "4H"],
            non_repainting=True,
            confirmation_delay_bars=1,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Identifies buy-side and sell-side liquidity sweeps and rapid reclaim pin-bars.",
            parameters={"tolerance_pips": 3.0}
        ))

        self.register(IndicatorDefinition(
            indicator_id="institutional_smc_poc_matrix",
            name="Structural Liquidity & POC Matrix",
            source="COMMUNITY",
            version="1.4.0",
            cluster=EvidenceClusterType.LIQUIDITY_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Volume Profile Point of Control (POC), Value Area High (VAH), and Value Area Low (VAL).",
            parameters={"profile_period": "session"}
        ))

        # ── 5. VOLATILITY CLUSTER ─────────────────────────────────────────────
        self.register(IndicatorDefinition(
            indicator_id="atr_volatility_regime",
            name="ATR Volatility Regime & Normalizer",
            source="NATIVE",
            version="2.0.0",
            cluster=EvidenceClusterType.VOLATILITY_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["5m", "15m", "30m", "1H", "2H", "4H", "12H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="ATR-based volatility expansion/contraction scoring and dynamic SL/TP calculation.",
            parameters={"period": 14}
        ))

        self.register(IndicatorDefinition(
            indicator_id="bollinger_bandwidth",
            name="Bollinger Band Squeeze & Expansion",
            source="NATIVE",
            version="1.0.0",
            cluster=EvidenceClusterType.VOLATILITY_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "1H", "4H"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Standard deviation channel bandwidth measuring volatility compression prior to breakouts.",
            parameters={"length": 20, "mult": 2.0}
        ))

        # ── 6. VOLUME / ORDER FLOW CLUSTER ────────────────────────────────────
        self.register(IndicatorDefinition(
            indicator_id="smart_swing_vwap",
            name="Smart Swing Anchored VWAP",
            source="COMMUNITY",
            version="2.0.0",
            cluster=EvidenceClusterType.VOLUME_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["15m", "1H", "4H", "1D"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Volume Weighted Average Price anchored to major swing highs/lows and session opens.",
            parameters={"anchor": "swing"}
        ))

        self.register(IndicatorDefinition(
            indicator_id="volume_footprint_delta",
            name="Volume Footprint & Delta Proxy",
            source="COMMUNITY",
            version="1.0.0",
            cluster=EvidenceClusterType.VOLUME_CLUSTER,
            status=IndicatorStatus.SUPPORTED,
            timeframes=["5m", "15m", "1H"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Intrabar buying vs selling volume imbalance estimation.",
            parameters={"threshold": 1.5}
        ))

        # ── 7. UNVERIFIED / REPAINTING COMMUNITY STRATEGIES (AUDITED & ISOLATED)
        self.register(IndicatorDefinition(
            indicator_id="universal_signal_backtester_v3",
            name="Universal Signal Backtester",
            source="TRADINGVIEW_PINESCRIPT",
            version="3.4.0",
            cluster=EvidenceClusterType.TREND_CLUSTER,
            status=IndicatorStatus.UNVERIFIED,
            timeframes=["1H", "4H"],
            non_repainting=False,
            confirmation_delay_bars=0,
            lookahead_risk="UNVERIFIED",
            repaint_risk="INTRABAR_ONLY",
            description="Community backtesting suite with unverified intrabar execution assumptions.",
            parameters={}
        ))

        self.register(IndicatorDefinition(
            indicator_id="xg_boost_lite_pinescript",
            name="XG Boost Lite (PineScript Port)",
            source="TRADINGVIEW_PINESCRIPT",
            version="1.0.0",
            cluster=EvidenceClusterType.FORECAST_MODEL_CLUSTER,
            status=IndicatorStatus.UNVERIFIED,
            timeframes=["1H", "4H"],
            non_repainting=True,
            confirmation_delay_bars=0,
            lookahead_risk="NONE",
            repaint_risk="NONE",
            description="Lightweight Decision Tree implementation ported to PineScript.",
            parameters={}
        ))

    def register(self, indicator: IndicatorDefinition):
        self._indicators[indicator.indicator_id] = indicator

    def get(self, indicator_id: str) -> Optional[IndicatorDefinition]:
        return self._indicators.get(indicator_id)

    def get_all(self) -> List[IndicatorDefinition]:
        return list(self._indicators.values())

    def get_supported_by_cluster(self, cluster: EvidenceClusterType) -> List[IndicatorDefinition]:
        return [
            ind for ind in self._indicators.values()
            if ind.cluster == cluster and ind.status == IndicatorStatus.SUPPORTED
        ]

    def audit_repainting_behavior(self, indicator_id: str) -> Dict[str, Any]:
        """Audits indicator for causal correctness and repainting safety."""
        ind = self.get(indicator_id)
        if not ind:
            return {"indicator_id": indicator_id, "found": False, "safe_for_production": False}

        is_safe = (
            ind.status == IndicatorStatus.SUPPORTED
            and ind.non_repainting
            and ind.lookahead_risk == "NONE"
            and ind.repaint_risk == "NONE"
        )
        return {
            "indicator_id": ind.indicator_id,
            "name": ind.name,
            "cluster": ind.cluster.value,
            "status": ind.status.value,
            "non_repainting": ind.non_repainting,
            "lookahead_risk": ind.lookahead_risk,
            "repaint_risk": ind.repaint_risk,
            "confirmation_delay_bars": ind.confirmation_delay_bars,
            "safe_for_production": is_safe,
        }


# Global Singleton
indicator_registry = IndicatorRegistry()
