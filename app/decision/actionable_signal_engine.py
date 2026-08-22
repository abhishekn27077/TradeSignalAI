"""
Phase 50 — Actionable Signal Engine & Lifecycle State Machine.

Transforms analytical forecasts into human-actionable trading opportunities,
manages temporal entry and holding envelopes, enforces Zero-Trust safety gates,
and orchestrates the state machine transitions.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.market_clock import market_clock
from app.decision.revalidation_engine import revalidation_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)


class ActionableSignalEngine:
    """
    Manages the creation, status progression, and revalidation of actionable trade opportunities.
    """

    def __init__(self):
        self._actionable_opportunities: Dict[str, Dict[str, Any]] = {}
        self._evolution_history: Dict[str, List[Dict[str, Any]]] = {}

    def create_actionable_opportunity(
        self,
        forecast_data: Dict[str, Any],
        target_utc: Optional[datetime] = None,
        now_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Builds a full actionable trade opportunity from forecast data and computes
        all dynamic entry and holding windows.
        """
        now = now_utc or market_clock.get_current_utc()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        asset = forecast_data.get("asset", "EURUSD")
        timeframe = forecast_data.get("timeframe", "1H")
        direction = (forecast_data.get("direction") or "NEUTRAL").upper()
        confidence = float(forecast_data.get("confidence") or 0.5)
        consensus_score = float(forecast_data.get("consensus_score") or forecast_data.get("consensus_pct") or 0.5)

        # ── 1. Target Time & Dynamic Windows ─────────────────────────────────
        if target_utc is None:
            # Derive target dynamically from timeframe if not provided
            lead_hours = 4.0 if "4H" in timeframe.upper() or "H4" in timeframe.upper() else (24.0 if "1D" in timeframe.upper() else 1.0)
            from datetime import timedelta
            target_utc = now + timedelta(hours=lead_hours)

        if target_utc.tzinfo is None:
            target_utc = target_utc.replace(tzinfo=timezone.utc)

        volatility = float(forecast_data.get("volatility_pct") or 1.0)
        atr = float(forecast_data.get("atr") or 0.0)

        entry_window = market_clock.compute_entry_window(
            target_utc=target_utc,
            timeframe=timeframe,
            atr=atr,
            volatility_pct=volatility,
        )
        holding_window = market_clock.compute_holding_window(
            timeframe=timeframe,
            atr=atr,
            strategy_type=forecast_data.get("strategy_type", "INTRADAY"),
        )

        # ── 2. Pricing & Risk/Reward ─────────────────────────────────────────
        entry_price = forecast_data.get("entry_price")
        stop_loss = forecast_data.get("stop_loss")
        take_profit = forecast_data.get("take_profit")
        risk_reward = forecast_data.get("risk_reward")

        # ── 3. Evaluate Zero-Trust Qualification & State Machine ─────────────
        event_risk = forecast_data.get("event_risk", "NONE")
        is_stale = forecast_data.get("data_freshness_status") == "DATA_STALE"
        is_qualified = forecast_data.get("is_trade_qualified", False)
        rejection_reason = forecast_data.get("rejection_reason") or forecast_data.get("trade_disqualification_reason")

        status, primary_action, no_trade_reason = self._evaluate_initial_state(
            now=now,
            entry_window=entry_window,
            direction=direction,
            confidence=confidence,
            consensus_score=consensus_score,
            event_risk=event_risk,
            is_stale=is_stale,
            is_qualified=is_qualified,
            rejection_reason=rejection_reason,
            risk_reward=risk_reward,
        )

        signal_id = forecast_data.get("prediction_id") or f"ACT-{asset}-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        opportunity: Dict[str, Any] = {
            "signal_id": signal_id,
            "version": 1,
            "parent_signal_id": signal_id,
            "supersedes_signal_id": None,
            "revalidation_count": 0,
            "asset": asset,
            "timeframe": timeframe,
            "direction": direction,
            "strategy_name": forecast_data.get("strategy_name", "ConsensusEngine"),
            # Timestamps (UTC & IST)
            "forecast_generated_at_utc": now.isoformat(),
            "forecast_generated_at_ist": market_clock.format_ist(now),
            "last_revalidated_at_utc": now.isoformat(),
            "last_revalidated_at_ist": market_clock.format_ist(now),
            "target_time_utc": entry_window["target_time_utc"].isoformat(),
            "target_time_ist": entry_window["target_time_ist"],
            "entry_window_start_utc": entry_window["entry_window_start_utc"].isoformat(),
            "entry_window_start_ist": entry_window["entry_window_start_ist"],
            "preferred_entry_time_utc": entry_window["preferred_entry_time_utc"].isoformat(),
            "preferred_entry_time_ist": entry_window["preferred_entry_time_ist"],
            "entry_window_end_utc": entry_window["entry_window_end_utc"].isoformat(),
            "entry_window_end_ist": entry_window["entry_window_end_ist"],
            "signal_expiry_time_utc": entry_window["signal_expiry_time_utc"].isoformat(),
            "signal_expiry_time_ist": entry_window["signal_expiry_time_ist"],
            # Holding envelopes
            "expected_hold_min_hours": holding_window["expected_hold_min_hours"],
            "expected_hold_max_hours": holding_window["expected_hold_max_hours"],
            "maximum_hold_hours": holding_window["maximum_hold_hours"],
            "expected_holding_formatted": holding_window["holding_description"],
            # Intelligence & Pricing
            "confidence": round(confidence, 4),
            "consensus_score": round(consensus_score, 4),
            "consensus_members": forecast_data.get("consensus_members", 8),
            "market_regime": forecast_data.get("market_regime", "RANGE"),
            "volatility_state": forecast_data.get("volatility_state", "NORMAL"),
            "event_risk": event_risk,
            "news_risk": forecast_data.get("news_risk", "NEUTRAL"),
            "current_price": forecast_data.get("current_price") or entry_price,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward": risk_reward,
            # State machine
            "status": status,
            "primary_action": primary_action,
            "invalidation_reason": None,
            "change_reason": "Initial forecast generated",
            "no_trade_reason": no_trade_reason,
            # Freshness
            "data_age_seconds": float(forecast_data.get("data_age_seconds", 0.0)),
            "data_freshness_status": "DATA_STALE" if is_stale else "FRESH",
            # Versions & Models
            "model_version": forecast_data.get("model_version", "3.2.0-frozen"),
            "strategy_version": forecast_data.get("strategy_version", "1.0.0"),
        }

        # Store in memory cache
        self._actionable_opportunities[signal_id] = opportunity
        self._record_evolution(signal_id, opportunity)

        return opportunity

    def _evaluate_initial_state(
        self,
        now: datetime,
        entry_window: Dict[str, Any],
        direction: str,
        confidence: float,
        consensus_score: float,
        event_risk: str,
        is_stale: bool,
        is_qualified: bool,
        rejection_reason: Optional[str],
        risk_reward: Optional[float],
    ) -> tuple[str, str, Optional[str]]:
        """Evaluates state machine and human action."""
        # 1. Freshness check
        if is_stale:
            return "DATA_STALE", "NO TRADE", "DATA_STALE"

        # 2. Event risk gate
        if event_risk in ["HIGH", "EXTREME"]:
            return "NO_TRADE", "NO TRADE", "HIGH_EVENT_RISK"

        # 3. Consensus threshold gate (>= 0.65)
        if consensus_score < 0.65 or direction not in ["BUY", "SELL"]:
            return "NO_TRADE", "NO TRADE", rejection_reason or "LOW_CONSENSUS"

        # 4. Confidence gate
        if confidence < 0.60:
            return "NO_TRADE", "NO TRADE", "LOW_CONFIDENCE"

        # 5. Risk-Reward gate
        if risk_reward is not None and risk_reward < 1.2:
            return "NO_TRADE", "NO TRADE", "LOW_RR"

        # 6. Temporal Entry Window check
        w_start = entry_window["entry_window_start_utc"]
        w_end = entry_window["entry_window_end_utc"]

        if now > w_end:
            return "EXPIRED", "EXPIRED", "ENTRY_WINDOW_EXPIRED"
        elif now >= w_start:
            return "ENTER_NOW", "ENTER NOW", None
        else:
            return "WATCH", "WAIT", None

    def revalidate_opportunity(
        self,
        signal_id: str,
        current_forecast: Dict[str, Any],
        current_market: Optional[Dict[str, Any]] = None,
        now_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Executes pre-entry revalidation on an existing opportunity, updates its state,
        applies anti-whipsaw rules, and records the evolution.
        """
        previous = self._actionable_opportunities.get(signal_id)
        if not previous:
            # Fallback: create fresh opportunity if not found
            return self.create_actionable_opportunity(current_forecast, now_utc=now_utc)

        now = now_utc or market_clock.get_current_utc()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # Run revalidation engine
        reval_res = revalidation_engine.compare_and_revalidate(
            previous_signal=previous,
            current_forecast=current_forecast,
            current_market=current_market,
            now_utc=now,
        )

        # Update or create new version
        new_opportunity = dict(previous)
        new_opportunity["signal_id"] = reval_res["signal_id"]
        new_opportunity["version"] = reval_res["version"]
        new_opportunity["parent_signal_id"] = reval_res["parent_signal_id"]
        new_opportunity["supersedes_signal_id"] = reval_res["supersedes_signal_id"]
        new_opportunity["revalidation_count"] = reval_res["revalidation_count"]
        new_opportunity["last_revalidated_at_utc"] = now.isoformat()
        new_opportunity["last_revalidated_at_ist"] = market_clock.format_ist(now)
        new_opportunity["change_reason"] = reval_res["change_reason_text"]

        # If invalidated
        if reval_res["revalidation_status"] in ["SIGNAL_INVALIDATED", "EVENT_BLOCKED", "DATA_STALE"]:
            new_opportunity["status"] = reval_res["actionable_status"]
            new_opportunity["primary_action"] = reval_res["primary_action"]
            new_opportunity["no_trade_reason"] = reval_res["no_trade_reason"]
            new_opportunity["invalidation_reason"] = reval_res["change_reason_text"]
        else:
            new_opportunity["direction"] = reval_res["direction"]
            new_opportunity["confidence"] = reval_res["confidence"]
            new_opportunity["consensus_score"] = reval_res["consensus_score"]
            new_opportunity["market_regime"] = reval_res["market_regime"]

            # Re-evaluate timing state
            w_start = datetime.fromisoformat(new_opportunity["entry_window_start_utc"])
            w_end = datetime.fromisoformat(new_opportunity["entry_window_end_utc"])
            if w_start.tzinfo is None:
                w_start = w_start.replace(tzinfo=timezone.utc)
            if w_end.tzinfo is None:
                w_end = w_end.replace(tzinfo=timezone.utc)

            if now > w_end:
                new_opportunity["status"] = "EXPIRED"
                new_opportunity["primary_action"] = "EXPIRED"
            elif now >= w_start:
                new_opportunity["status"] = "ENTER_NOW"
                new_opportunity["primary_action"] = "ENTER NOW"
            else:
                new_opportunity["status"] = "VALIDATED"
                new_opportunity["primary_action"] = "WAIT"

        # Update in memory
        self._actionable_opportunities[new_opportunity["signal_id"]] = new_opportunity
        # Mark previous superseded in map
        if previous["signal_id"] in self._actionable_opportunities:
            self._actionable_opportunities[previous["signal_id"]]["status"] = "SUPERSEDED"

        self._record_evolution(new_opportunity["parent_signal_id"], new_opportunity)
        return new_opportunity

    def get_actionable_opportunities(
        self, include_expired: bool = False, now_utc: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Returns all current actionable opportunities."""
        now = now_utc if now_utc is not None else market_clock.get_current_utc()
        opps = []
        for opp in self._actionable_opportunities.values():
            if opp.get("status") == "SUPERSEDED":
                continue
            exp_str = opp.get("signal_expiry_time_utc")
            if exp_str:
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                if not include_expired and now > exp_dt:
                    continue
            opps.append(opp)
        return opps

    def get_next_actionable_setup(self, now_utc: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Returns the single most actionable upcoming setup sorted by priority:
        1. ENTER_NOW
        2. VALIDATED / WATCH (soonest entry window)
        """
        opps = self.get_actionable_opportunities(include_expired=False, now_utc=now_utc)
        active_now = [o for o in opps if o.get("primary_action") == "ENTER NOW"]
        if active_now:
            return sorted(active_now, key=lambda x: x.get("confidence", 0.0), reverse=True)[0]

        waiting = [o for o in opps if o.get("primary_action") == "WAIT"]
        if waiting:
            return sorted(waiting, key=lambda x: x.get("entry_window_start_utc", "")) [0]

        return opps[0] if opps else None

    def get_signal_evolution(self, signal_id_or_parent: str) -> List[Dict[str, Any]]:
        """Returns the timeline history of changes for a given signal lineage."""
        return self._evolution_history.get(signal_id_or_parent, [])

    def _record_evolution(self, parent_id: str, record: Dict[str, Any]):
        if parent_id not in self._evolution_history:
            self._evolution_history[parent_id] = []
        # Store a snapshot copy
        self._evolution_history[parent_id].append({
            "version": record.get("version", 1),
            "timestamp_utc": record.get("last_revalidated_at_utc"),
            "timestamp_ist": record.get("last_revalidated_at_ist"),
            "direction": record.get("direction"),
            "confidence": record.get("confidence"),
            "status": record.get("status"),
            "primary_action": record.get("primary_action"),
            "change_reason": record.get("change_reason"),
            "signal_id": record.get("signal_id"),
        })


actionable_signal_engine = ActionableSignalEngine()
