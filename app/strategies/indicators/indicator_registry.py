"""
app/strategies/indicators/indicator_registry.py
================================================
Indicator Registry & Collinearity Attenuation Engine for TradeSignalAI-v3 (Phase 70).

Provides:
1. Full Registry of Community & Classical Technical/SMC Indicators:
   - SuperTrend (KivancOzbilgic ATR trailing stop)
   - Squeeze Momentum (LazyBear BB vs KC Squeeze + Momentum)
   - Custom MACD (ChrisMoody Fast/Slow signal crosses)
   - UT Bot Alerts (QuantNomad ATR trailing key value)
   - ICT Killzones & Session Pivots
   - LuxAlgo SMC Equivalent (Order Blocks, BOS, CHoCH, Fair Value Gaps)
   - Williams Vix Fix (Volatility bottoms)
2. Evidence Family Classification & Collinearity Attenuation:
   - Prevents correlated indicator groups from falsely inflating consensus confidence.
   - Calculates correlation-adjusted effective weights: W_eff = W_base / sqrt(N_family).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import math
import numpy as np
import pandas as pd


class IndicatorFamily(str, Enum):
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    VOLUME = "VOLUME"
    STRUCTURE = "STRUCTURE"
    SESSION = "SESSION"


@dataclass
class IndicatorDefinition:
    id: str
    name: str
    family: IndicatorFamily
    author_reference: str
    license_type: str
    is_non_repainting: bool
    base_weight: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "family": self.family.value,
            "author_reference": self.author_reference,
            "license_type": self.license_type,
            "is_non_repainting": self.is_non_repainting,
            "base_weight": self.base_weight,
            "description": self.description,
        }


class IndicatorRegistry:
    """
    Authoritative registry of technical, SMC, and session indicators with collinearity attenuation.
    """

    def __init__(self):
        self._indicators: Dict[str, IndicatorDefinition] = {}
        self._register_default_indicators()

    def _register_default_indicators(self):
        # 1. Trend Family
        self.register(IndicatorDefinition(
            id="supertrend",
            name="SuperTrend (KivancOzbilgic)",
            family=IndicatorFamily.TREND,
            author_reference="KivancOzbilgic / TradingView Community",
            license_type="Open Source (MIT / PineScript Public)",
            is_non_repainting=True,
            base_weight=0.15,
            description="ATR-based trailing stop indicating dominant trend continuation and flips."
        ))
        self.register(IndicatorDefinition(
            id="ema_trend_stack",
            name="EMA Multi-Ribbon (20/50/200)",
            family=IndicatorFamily.TREND,
            author_reference="Classic Quantitative Trend Following",
            license_type="Public Domain",
            is_non_repainting=True,
            base_weight=0.10,
            description="Exponential moving average alignment for structural trend confirmation."
        ))

        # 2. Momentum Family
        self.register(IndicatorDefinition(
            id="squeeze_momentum",
            name="Squeeze Momentum Indicator (LazyBear)",
            family=IndicatorFamily.MOMENTUM,
            author_reference="LazyBear / John Carter TTM Squeeze",
            license_type="Open Source (PineScript Public)",
            is_non_repainting=True,
            base_weight=0.15,
            description="Bollinger Bands within Keltner Channels to identify volatility compression and breakout momentum."
        ))
        self.register(IndicatorDefinition(
            id="macd_custom",
            name="Custom MACD Divergence (ChrisMoody)",
            family=IndicatorFamily.MOMENTUM,
            author_reference="ChrisMoody / TradingView Community",
            license_type="Open Source (PineScript Public)",
            is_non_repainting=True,
            base_weight=0.10,
            description="12/26/9 MACD histogram and zero-line cross momentum filtering."
        ))
        self.register(IndicatorDefinition(
            id="ut_bot_alerts",
            name="UT Bot Alerts (QuantNomad)",
            family=IndicatorFamily.MOMENTUM,
            author_reference="QuantNomad / TradingView Community",
            license_type="Open Source (PineScript Public)",
            is_non_repainting=True,
            base_weight=0.10,
            description="Trailing key-value ATR stops generating trend-momentum trigger alerts."
        ))

        # 3. Volatility Family
        self.register(IndicatorDefinition(
            id="atr_volatility_bands",
            name="Average True Range (ATR) Envelope",
            family=IndicatorFamily.VOLATILITY,
            author_reference="J. Welles Wilder",
            license_type="Public Domain",
            is_non_repainting=True,
            base_weight=0.10,
            description="Measures market volatility and normalizes stop loss / take profit distance."
        ))
        self.register(IndicatorDefinition(
            id="williams_vix_fix",
            name="Williams Vix Fix (LazyBear)",
            family=IndicatorFamily.VOLATILITY,
            author_reference="Larry Williams / LazyBear",
            license_type="Open Source (PineScript Public)",
            is_non_repainting=True,
            base_weight=0.08,
            description="Synthetic implied volatility index for detecting panic lows and market exhaustion."
        ))

        # 4. Volume Family
        self.register(IndicatorDefinition(
            id="volume_confirmation",
            name="Institutional Volume Delta & OBV",
            family=IndicatorFamily.VOLUME,
            author_reference="Joseph Granville / Classic Volume Spread",
            license_type="Public Domain",
            is_non_repainting=True,
            base_weight=0.10,
            description="Validates price movements against volume expansion and exhaustion."
        ))

        # 5. Structure Family (SMC / Smart Money)
        self.register(IndicatorDefinition(
            id="smc_order_blocks",
            name="Smart Money Order Blocks (LuxAlgo Equiv)",
            family=IndicatorFamily.STRUCTURE,
            author_reference="ICT / LuxAlgo SMC Mathematical Equivalent",
            license_type="Clean-Room Python Implementation",
            is_non_repainting=True,
            base_weight=0.20,
            description="Institutional supply/demand zones preceding structural impulses with mitigation tracking."
        ))
        self.register(IndicatorDefinition(
            id="smc_bos_choch",
            name="Break of Structure & Change of Character (LuxAlgo Equiv)",
            family=IndicatorFamily.STRUCTURE,
            author_reference="ICT / LuxAlgo SMC Mathematical Equivalent",
            license_type="Clean-Room Python Implementation",
            is_non_repainting=True,
            base_weight=0.20,
            description="Trend continuation (BOS) and structural reversal (CHoCH) detection on confirmed candle closes."
        ))

        # 6. Session Family
        self.register(IndicatorDefinition(
            id="ict_killzones",
            name="ICT Killzones & Session Pivots",
            family=IndicatorFamily.SESSION,
            author_reference="Michael J. Huddleston (ICT)",
            license_type="Clean-Room Time Model",
            is_non_repainting=True,
            base_weight=0.10,
            description="Time-of-day liquidity windows: Asian, London Open, NY Open, London Close."
        ))

    def register(self, ind: IndicatorDefinition):
        self._indicators[ind.id] = ind

    def get_indicator(self, ind_id: str) -> Optional[IndicatorDefinition]:
        return self._indicators.get(ind_id)

    def list_all(self) -> List[IndicatorDefinition]:
        return list(self._indicators.values())

    def compute_collinearity_attenuated_weights(
        self,
        active_indicators: List[str],
        normalize: bool = True
    ) -> Dict[str, float]:
        """
        Calculates correlation-attenuated weights for an ensemble of indicators.
        If multiple indicators belong to the same family (e.g., 3 Momentum indicators),
        their weights are scaled by 1 / sqrt(count_in_family) to prevent collinearity inflation.
        """
        family_counts: Dict[IndicatorFamily, int] = {}
        for ind_id in active_indicators:
            ind = self._indicators.get(ind_id)
            if ind:
                family_counts[ind.family] = family_counts.get(ind.family, 0) + 1

        attenuated_weights: Dict[str, float] = {}
        total_weight = 0.0

        for ind_id in active_indicators:
            ind = self._indicators.get(ind_id)
            if not ind:
                continue
            count = family_counts.get(ind.family, 1)
            # Attenuation factor: 1.0 / sqrt(count)
            attenuation = 1.0 / math.sqrt(count)
            eff_weight = round(ind.base_weight * attenuation, 4)
            attenuated_weights[ind_id] = eff_weight
            total_weight += eff_weight

        # Normalize weights if requested so they sum to 1.0
        if normalize and total_weight > 0:
            for k in attenuated_weights:
                attenuated_weights[k] = round(attenuated_weights[k] / total_weight, 4)

        return attenuated_weights


# Global Singleton Instance
indicator_registry = IndicatorRegistry()
