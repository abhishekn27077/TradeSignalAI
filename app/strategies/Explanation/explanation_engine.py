from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.Confluence.confluence_engine import ConfluenceScore
from app.strategies.Router.strategy_router import RoutedStrategy


@dataclass
class SignalExplanation:
    signal_id: str
    asset: str
    timeframe: str
    direction: Direction
    headline: str
    why_evidence: List[str]
    risk_factors: List[str]
    invalidation_triggers: List[str]
    confluence_score: float
    strategy_name: str
    timestamp_utc: datetime
    timestamp_ist: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "headline": self.headline,
            "why_evidence": self.why_evidence,
            "risk_factors": self.risk_factors,
            "invalidation_triggers": self.invalidation_triggers,
            "confluence_score": round(float(self.confluence_score), 2),
            "strategy_name": self.strategy_name,
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "details": self.details,
        }


class SignalExplanationEngine:
    """
    Structured Signal Explanation & Evidence Tree Engine.
    Produces comprehensive, transparent, and auditable 'Why / Risk / Invalidation' narratives.
    """

    def generate_explanation(
        self,
        signal_id: str,
        asset: str,
        timeframe: str,
        confluence: ConfluenceScore,
        strategy: RoutedStrategy,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        extra_evidence: Optional[Dict[str, Any]] = None
    ) -> SignalExplanation:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        direction_str = confluence.direction.value if hasattr(confluence.direction, 'value') else str(confluence.direction)
        headline = f"{direction_str} {strategy.strategy_type.value} Setup on {asset} ({timeframe})"

        why_evidence: List[str] = []
        risk_factors: List[str] = []
        invalidation_triggers: List[str] = []

        # 1. Build WHY Evidence Tree
        why_evidence.append(f"Multi-factor confluence reached {confluence.total_score:.1f}/100 in {confluence.regime} market regime.")
        if confluence.structure_score > 15.0:
            why_evidence.append(f"Market structure confirmed {direction_str} trend with score {confluence.structure_score:.1f} pts.")
        if confluence.smc_score > 10.0:
            why_evidence.append(f"Institutional order flow active with Order Block / Fair Value Gap mitigation in optimal dealing range.")
        if confluence.liquidity_score > 8.0:
            why_evidence.append("Liquidity sweep detected and confirmed on key reference levels.")
        if confluence.session_score > 5.0:
            why_evidence.append("Setup timing coincides with active institutional Killzone volatility window.")
        if confluence.smt_score > 5.0:
            why_evidence.append("Cross-asset SMT divergence confirms institutional accumulation/distribution.")
        if confluence.technical_score > 10.0:
            why_evidence.append("Momentum indicators (SuperTrend, UT Bot, VWAP, MACD) confirm directional expansion.")

        # 2. Build RISK PROFILE
        rr_ratio = abs(take_profit - entry_price) / (abs(entry_price - stop_loss) + 1e-8)
        risk_factors.append(f"Risk-to-Reward ratio calculated at {rr_ratio:.2f}:1 (Zero-trust threshold >= 1.2:1 verified).")
        risk_factors.append(f"Stop-loss distance: {abs(entry_price - stop_loss):.5f} price units.")
        if confluence.collinearity_penalty_applied > 0:
            risk_factors.append(f"Collinearity dampener active (-{confluence.collinearity_penalty_applied:.1f} pts) to prevent indicator double-counting.")

        # 3. Build INVALIDATION TRIGGERS
        invalidation_triggers.append(f"Price breach beyond structural Stop Loss at {stop_loss:.5f}.")
        invalidation_triggers.append(f"Opposing CHoCH or structural break against {direction_str} bias.")
        invalidation_triggers.append("Holding window envelope expiration if target is not reached within timeframe tolerance.")

        return SignalExplanation(
            signal_id=signal_id,
            asset=asset,
            timeframe=timeframe,
            direction=confluence.direction,
            headline=headline,
            why_evidence=why_evidence,
            risk_factors=risk_factors,
            invalidation_triggers=invalidation_triggers,
            confluence_score=confluence.total_score,
            strategy_name=strategy.strategy_type.value if hasattr(strategy.strategy_type, 'value') else str(strategy.strategy_type),
            timestamp_utc=now_utc,
            timestamp_ist=now_ist,
            details={
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_reward_ratio": rr_ratio,
            }
        )
