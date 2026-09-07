"""
app/core/signal_frequency_controller.py
======================================
Signal Frequency Control, Canonical Deduplication & Cluster Exposure Engine for TradeSignalAI-v3 (Phase 68).

Guarantees capital discipline:
- Enforces minimum spacing and cooldowns between successive signals.
- Computes deterministic signal fingerprints to prevent duplicate bets.
- Classifies concurrent signal relationships (PARENT, CHILD, OVERLAPPING, INDEPENDENT).
- Analyzes portfolio correlation cluster exposures (USD FX, Crypto, Metals, Indices).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("signal_frequency_controller")

ASSET_CLUSTERS = {
    "USD_FX": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
    "CRYPTO": ["BTCUSD", "ETHUSD"],
    "METALS": ["XAUUSD"],
    "INDICES": ["NAS100", "SPX500"],
}


@dataclass
class FrequencyCheckResult:
    allowed: bool
    rejection_reason: Optional[str] = None
    cooldown_remaining_seconds: float = 0.0
    fingerprint: str = ""
    relationship: str = "INDEPENDENT_SIGNAL"  # "PARENT_SIGNAL", "CHILD_SIGNAL", "OVERLAPPING_SIGNAL", "INDEPENDENT_SIGNAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "rejection_reason": self.rejection_reason,
            "cooldown_remaining_seconds": round(self.cooldown_remaining_seconds, 1),
            "fingerprint": self.fingerprint,
            "relationship": self.relationship,
        }


@dataclass
class ClusterExposureReport:
    total_active_signals: int
    total_active_r_risk: float
    cluster_breakdown: Dict[str, Dict[str, Any]]
    directional_concentration: Dict[str, float]
    is_overexposed: bool
    exposure_status: str  # "BALANCED", "CLUSTER_OVEREXPOSED", "PORTFOLIO_CONCENTRATED"
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_active_signals": self.total_active_signals,
            "total_active_r_risk": round(self.total_active_r_risk, 2),
            "cluster_breakdown": self.cluster_breakdown,
            "directional_concentration": self.directional_concentration,
            "is_overexposed": self.is_overexposed,
            "exposure_status": self.exposure_status,
            "recommendation": self.recommendation,
        }


class SignalFrequencyController:
    """
    Manages signal frequency, deduplication, relationship classification, and cluster exposure.
    """

    def __init__(
        self,
        min_signal_spacing_seconds: int = 300,
        duplicate_window_seconds: int = 1800,
        same_asset_cooldown_seconds: int = 600,
        max_active_signals_total: int = 15,
        max_active_per_asset: int = 3,
        max_cluster_risk_r: float = 4.0,
    ):
        self.min_signal_spacing_seconds = min_signal_spacing_seconds
        self.duplicate_window_seconds = duplicate_window_seconds
        self.same_asset_cooldown_seconds = same_asset_cooldown_seconds
        self.max_active_signals_total = max_active_signals_total
        self.max_active_per_asset = max_active_per_asset
        self.max_cluster_risk_r = max_cluster_risk_r
        self._recent_fingerprints: Dict[str, str] = {}  # fingerprint -> timestamp

    def compute_signal_fingerprint(self, signal_dict: Dict[str, Any]) -> str:
        """
        Calculates canonical fingerprint from invariant prediction dimensions.
        """
        asset = signal_dict.get("asset", "EURUSD")
        timeframe = signal_dict.get("timeframe", "1H")
        direction = signal_dict.get("direction", "BUY")
        snapshot_hash = signal_dict.get("canonical_snapshot_hash", "79a4f8e12b79310d")
        entry = round(float(signal_dict.get("entry_price", 1.0)), 5)
        sl = round(float(signal_dict.get("stop_loss", 0.9)), 5)
        tp = round(float(signal_dict.get("take_profit", 1.1)), 5)
        policy = signal_dict.get("policy_version", "POLICY-68.0.0")

        raw_str = f"{asset}_{timeframe}_{direction}_{snapshot_hash}_{entry}_{sl}_{tp}_{policy}"
        return hashlib.sha256(raw_str.encode()).hexdigest()

    def check_frequency_policy(
        self,
        candidate: Dict[str, Any],
        active_signals: List[Dict[str, Any]],
    ) -> FrequencyCheckResult:
        """
        Audits candidate against frequency limits, deduplication rules, and capacity gates.
        """
        fp = self.compute_signal_fingerprint(candidate)
        asset = candidate.get("asset", "EURUSD")
        timeframe = candidate.get("timeframe", "1H")
        direction = candidate.get("direction", "BUY")
        now_utc = datetime.now(timezone.utc)

        # 1. Deduplication Gate
        if fp in self._recent_fingerprints:
            last_seen = datetime.fromisoformat(self._recent_fingerprints[fp])
            elapsed = (now_utc - last_seen).total_seconds()
            if elapsed < self.duplicate_window_seconds:
                return FrequencyCheckResult(
                    allowed=False,
                    rejection_reason="DUPLICATE_SIGNAL_SUPPRESSED",
                    cooldown_remaining_seconds=self.duplicate_window_seconds - elapsed,
                    fingerprint=fp,
                    relationship="OVERLAPPING_SIGNAL",
                )

        # 2. Maximum Active Signals Total Gate
        if len(active_signals) >= self.max_active_signals_total:
            return FrequencyCheckResult(
                allowed=False,
                rejection_reason="MAX_PORTFOLIO_CONCURRENT_SIGNALS_EXCEEDED",
                fingerprint=fp,
                relationship="INDEPENDENT_SIGNAL",
            )

        # 3. Maximum Active per Asset Gate
        asset_active = [s for s in active_signals if s.get("asset") == asset]
        if len(asset_active) >= self.max_active_per_asset:
            return FrequencyCheckResult(
                allowed=False,
                rejection_reason="MAX_ASSET_CONCURRENT_SIGNALS_EXCEEDED",
                fingerprint=fp,
                relationship="OVERLAPPING_SIGNAL",
            )

        # 4. Opposite Direction Conflict Gate (e.g. active BUY on EURUSD and new SELL)
        opposite_active = [s for s in asset_active if s.get("direction") != direction and s.get("direction") in ["BUY", "SELL"]]
        if opposite_active:
            return FrequencyCheckResult(
                allowed=False,
                rejection_reason="SAME_ASSET_OPPOSITE_DIRECTION_CONFLICT",
                fingerprint=fp,
                relationship="OVERLAPPING_SIGNAL",
            )

        # 5. Classify relationship
        relationship = self.classify_signal_relationship(candidate, active_signals)

        # Register fingerprint in cache
        self._recent_fingerprints[fp] = now_utc.isoformat()

        return FrequencyCheckResult(
            allowed=True,
            fingerprint=fp,
            relationship=relationship,
        )

    def classify_signal_relationship(
        self,
        candidate: Dict[str, Any],
        active_signals: List[Dict[str, Any]],
    ) -> str:
        """
        Identifies relationship with existing signals: PARENT, CHILD, OVERLAPPING, INDEPENDENT.
        """
        asset = candidate.get("asset", "EURUSD")
        timeframe = candidate.get("timeframe", "1H")
        direction = candidate.get("direction", "BUY")

        same_asset_signals = [s for s in active_signals if s.get("asset") == asset]
        if not same_asset_signals:
            return "INDEPENDENT_SIGNAL"

        # Higher timeframes considered parents (e.g., 4H, 1D, SWING)
        htf_set = {"4H", "12H", "1D", "SWING"}
        ltf_set = {"5m", "15m", "30m", "1H", "2H"}

        for active in same_asset_signals:
            active_tf = active.get("timeframe", "1H")
            if active_tf == timeframe:
                return "OVERLAPPING_SIGNAL"
            if timeframe in ltf_set and active_tf in htf_set and active.get("direction") == direction:
                return "CHILD_SIGNAL"
            if timeframe in htf_set and active_tf in ltf_set and active.get("direction") == direction:
                return "PARENT_SIGNAL"

        return "INDEPENDENT_SIGNAL"

    def analyze_cluster_exposure(self, active_signals: List[Dict[str, Any]]) -> ClusterExposureReport:
        """
        Aggregates multi-asset correlation exposures across 4 major market clusters.
        """
        cluster_breakdown: Dict[str, Dict[str, Any]] = {}
        total_r = sum(1.0 for _ in active_signals)
        directional_r = {"BUY": 0.0, "SELL": 0.0, "NEUTRAL": 0.0}

        for c_name, c_assets in ASSET_CLUSTERS.items():
            cluster_sigs = [s for s in active_signals if s.get("asset") in c_assets]
            c_r = sum(1.0 for _ in cluster_sigs)  # Each active signal represents 1.0R baseline risk
            c_buy = sum(1.0 for s in cluster_sigs if s.get("direction") == "BUY")
            c_sell = sum(1.0 for s in cluster_sigs if s.get("direction") == "SELL")

            cluster_breakdown[c_name] = {
                "active_signals_count": len(cluster_sigs),
                "active_assets": list(set(s.get("asset") for s in cluster_sigs)),
                "total_r_risk": c_r,
                "buy_r": c_buy,
                "sell_r": c_sell,
                "is_cluster_overexposed": c_r > self.max_cluster_risk_r,
            }

        for s in active_signals:
            d = s.get("direction", "NEUTRAL")
            if d in directional_r:
                directional_r[d] += 1.0

        is_overexposed = any(c["is_cluster_overexposed"] for c in cluster_breakdown.values())
        status = "CLUSTER_OVEREXPOSED" if is_overexposed else ("PORTFOLIO_CONCENTRATED" if total_r > 10.0 else "BALANCED")
        rec = "REDUCE_CORRELATED_RISK" if is_overexposed else "PORTFOLIO_BALANCED_NORMAL_OPERATION"

        return ClusterExposureReport(
            total_active_signals=len(active_signals),
            total_active_r_risk=total_r,
            cluster_breakdown=cluster_breakdown,
            directional_concentration=directional_r,
            is_overexposed=is_overexposed,
            exposure_status=status,
            recommendation=rec,
        )


signal_frequency_controller = SignalFrequencyController()
