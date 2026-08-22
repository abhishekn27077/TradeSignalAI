"""
Phase 50 — Pre-Entry Revalidation & Anti-Whipsaw Engine.

Compares previous forecast state against newly evaluated real market state.
Produces evidence-backed comparison outcomes (STRENGTHENED, WEAKENED, UNCHANGED, CHANGED, INVALIDATED)
and enforces anti-whipsaw hysteresis rules to avoid rapid flapping on insignificant candle noise.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.market_clock import market_clock
from app.logs.logger import get_logger

logger = get_logger(__name__)


class RevalidationEngine:
    """
    Evaluates existing actionable opportunities against current real-time market data
    and generates versioned lineage records.
    """

    # Hysteresis threshold: requires significant consensus and confidence to reverse direction
    HYSTERESIS_MIN_CONSENSUS = 0.70
    HYSTERESIS_MIN_CONFIDENCE = 0.65
    CONFIDENCE_DELTA_THRESHOLD = 0.03

    @classmethod
    def compare_and_revalidate(
        cls,
        previous_signal: Dict[str, Any],
        current_forecast: Dict[str, Any],
        current_market: Optional[Dict[str, Any]] = None,
        now_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Compares an existing forecast/opportunity against current market analysis.

        Returns:
            Dict with revalidation result, updated fields, change reasons, and versioning info.
        """
        now = now_utc or market_clock.get_current_utc()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        prev_dir = (previous_signal.get("direction") or "NEUTRAL").upper()
        curr_dir = (current_forecast.get("direction") or "NEUTRAL").upper()

        prev_conf = float(previous_signal.get("confidence") or 0.5)
        curr_conf = float(current_forecast.get("confidence") or 0.5)
        conf_delta = curr_conf - prev_conf

        prev_consensus = float(previous_signal.get("consensus_score") or previous_signal.get("consensus_pct") or 0.5)
        curr_consensus = float(current_forecast.get("consensus_score") or current_forecast.get("consensus_pct") or 0.5)

        prev_regime = previous_signal.get("market_regime") or "RANGE"
        curr_regime = current_forecast.get("market_regime") or "RANGE"

        event_risk = current_forecast.get("event_risk", "NONE")
        is_stale = current_forecast.get("data_freshness_status") == "DATA_STALE"

        change_reasons: List[str] = []
        is_direction_changed = prev_dir != curr_dir
        is_invalidated = False
        revalidation_status = "SIGNAL_UNCHANGED"
        primary_action = "WAIT"
        actionable_status = "VALIDATED"
        no_trade_reason: Optional[str] = None

        # ── 1. Check Data Freshness ──────────────────────────────────────────
        if is_stale:
            revalidation_status = "DATA_STALE"
            actionable_status = "DATA_STALE"
            primary_action = "NO TRADE"
            no_trade_reason = "DATA_STALE"
            change_reasons.append("Market provider data is stale; trade execution blocked")

        # ── 2. Check Event Risk Gating ───────────────────────────────────────
        elif event_risk in ["HIGH", "EXTREME"]:
            revalidation_status = "EVENT_BLOCKED"
            actionable_status = "NO_TRADE"
            primary_action = "NO TRADE"
            no_trade_reason = "HIGH_EVENT_RISK"
            change_reasons.append(f"High economic event risk detected ({event_risk})")

        # ── 3. Check Price Boundary Invalidation ────────────────────────────
        elif current_market and previous_signal.get("stop_loss"):
            curr_price = float(current_market.get("price", previous_signal.get("entry_price", 0.0)))
            sl = float(previous_signal["stop_loss"])
            entry = float(previous_signal.get("entry_price") or curr_price)

            if prev_dir == "BUY" and curr_price <= sl:
                is_invalidated = True
                revalidation_status = "SIGNAL_INVALIDATED"
                actionable_status = "INVALIDATED"
                primary_action = "CANCELLED"
                no_trade_reason = "PRICE_HIT_STOP_LOSS"
                change_reasons.append(f"Price ({curr_price:.5f}) breached initial stop loss level ({sl:.5f})")
            elif prev_dir == "SELL" and curr_price >= sl:
                is_invalidated = True
                revalidation_status = "SIGNAL_INVALIDATED"
                actionable_status = "INVALIDATED"
                primary_action = "CANCELLED"
                no_trade_reason = "PRICE_HIT_STOP_LOSS"
                change_reasons.append(f"Price ({curr_price:.5f}) breached initial stop loss level ({sl:.5f})")

        # ── 4. Direction Reversal & Anti-Whipsaw Filter ──────────────────────
        if not is_invalidated and not is_stale and event_risk not in ["HIGH", "EXTREME"]:
            if is_direction_changed:
                # Enforce anti-whipsaw rule: Reversals require strong consensus and confidence
                if curr_consensus >= cls.HYSTERESIS_MIN_CONSENSUS and curr_conf >= cls.HYSTERESIS_MIN_CONFIDENCE and curr_dir in ["BUY", "SELL"]:
                    revalidation_status = "SIGNAL_CHANGED"
                    actionable_status = "VALIDATED"
                    primary_action = "WAIT"
                    change_reasons.append(
                        f"Direction reversed from {prev_dir} to {curr_dir} with strong consensus ({curr_consensus:.0%}) and confidence ({curr_conf:.0%})"
                    )
                    if prev_regime != curr_regime:
                        change_reasons.append(f"Market regime shifted from {prev_regime} to {curr_regime}")
                else:
                    # Not enough evidence to justify reversal -> mark previous invalidated and fail-closed to NO_TRADE
                    revalidation_status = "SIGNAL_INVALIDATED"
                    actionable_status = "NO_TRADE"
                    primary_action = "NO TRADE"
                    no_trade_reason = "MODEL_DISAGREEMENT"
                    change_reasons.append(
                        f"Previous {prev_dir} invalidated by market shift, but new {curr_dir} lacks required consensus ({curr_consensus:.0%} < {cls.HYSTERESIS_MIN_CONSENSUS:.0%})"
                    )
            else:
                # Same direction: evaluate strengthening / weakening
                if conf_delta >= cls.CONFIDENCE_DELTA_THRESHOLD:
                    revalidation_status = "SIGNAL_STRENGTHENED"
                    actionable_status = "VALIDATED"
                    change_reasons.append(f"Confidence increased by +{conf_delta*100:.1f}% ({prev_conf:.0%} -> {curr_conf:.0%})")
                elif conf_delta <= -cls.CONFIDENCE_DELTA_THRESHOLD:
                    revalidation_status = "SIGNAL_WEAKENED"
                    actionable_status = "VALIDATED"
                    change_reasons.append(f"Confidence softened by {conf_delta*100:.1f}% ({prev_conf:.0%} -> {curr_conf:.0%})")
                else:
                    revalidation_status = "SIGNAL_UNCHANGED"
                    actionable_status = "VALIDATED"
                    change_reasons.append("Market thesis remains consistent with incoming candles")

                # Consensus shifts
                if abs(curr_consensus - prev_consensus) >= 0.05:
                    change_reasons.append(f"Model consensus updated from {prev_consensus:.0%} to {curr_consensus:.0%}")

        # ── 5. Generate Versioning Identifiers ───────────────────────────────
        prev_sig_id = previous_signal.get("signal_id", "SIG-UNKNOWN")
        prev_version = int(previous_signal.get("version", 1))
        new_version = prev_version + 1
        parent_id = previous_signal.get("parent_signal_id") or prev_sig_id

        # Unique versioned signal ID
        asset = previous_signal.get("asset", "ASSET")
        new_signal_id = f"{parent_id}-v{new_version}" if not prev_sig_id.endswith(f"-v{prev_version}") else f"{parent_id.split('-v')[0]}-v{new_version}"

        return {
            "revalidation_status": revalidation_status,
            "actionable_status": actionable_status,
            "primary_action": primary_action,
            "no_trade_reason": no_trade_reason,
            "change_reasons": change_reasons,
            "change_reason_text": "; ".join(change_reasons) if change_reasons else "Revalidation confirmed previous parameters",
            "is_direction_changed": is_direction_changed,
            "confidence_delta": round(conf_delta, 4),
            "revalidated_at_utc": now,
            "revalidated_at_ist": market_clock.format_ist(now),
            # Versioning lineage
            "signal_id": new_signal_id,
            "version": new_version,
            "parent_signal_id": parent_id,
            "supersedes_signal_id": prev_sig_id,
            "revalidation_count": int(previous_signal.get("revalidation_count", 0)) + 1,
            # Current values
            "direction": curr_dir if not is_invalidated and not is_stale and revalidation_status != "SIGNAL_INVALIDATED" else prev_dir,
            "confidence": curr_conf,
            "consensus_score": curr_consensus,
            "market_regime": curr_regime,
        }


revalidation_engine = RevalidationEngine()
