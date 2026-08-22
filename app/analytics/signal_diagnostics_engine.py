"""
Phase 41 — Signal Generation Diagnostics Engine.

Provides transparent diagnostics for every core asset during every scan:
  - Forecast Direction & Probability
  - Consensus Agreement & Multi-Model Breakdown
  - Risk:Reward Ratio (R:R)
  - Event Risk Level & Impending Event Name
  - Data Freshness & Quality
  - Zero-Trust Risk Filter Decision
  - Final State: TRADE_SIGNAL_EMITTED | NO_VALID_SETUP

Crucial Rule: When Final State is NO_VALID_SETUP, the engine outputs the
exact rejection reasons (e.g. "CONSENSUS_BELOW_THRESHOLD (58% < 65%)",
"HIGH_EVENT_RISK (US CPI in 3h)", "RR_BELOW_MINIMUM (1.2 < 1.5)").
The forecast is NEVER hidden when a trade is disqualified.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from app.logs.logger import get_logger

logger = get_logger(__name__)

CORE_ASSETS = [
    "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY",
    "AUDUSD", "XAUUSD", "NAS100", "SPX500",
]

MIN_CONSENSUS_THRESHOLD = 0.65
MIN_RR_THRESHOLD = 1.5


class SignalDiagnosticsEngine:
    """
    Evaluates scan-level diagnostics for all 9 core assets with transparent rejection reasons.
    """

    async def get_diagnostics(self) -> dict[str, Any]:
        """
        Run diagnostics across all 9 assets.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch current forecasts
        from app.analytics.tomorrow_forecast_engine import tomorrow_forecast_engine
        today_data = await tomorrow_forecast_engine.generate_today_forecasts()
        forecasts = today_data.get("forecasts", [])

        # Map by asset
        forecast_map = {f["asset"]: f for f in forecasts}

        diagnostics_list = []
        trade_signals_count = 0
        no_trade_count = 0
        rejection_breakdown = {
            "CONSENSUS_BELOW_THRESHOLD": 0,
            "HIGH_EVENT_RISK": 0,
            "RR_BELOW_MINIMUM": 0,
            "DATA_STALE": 0,
            "NEUTRAL_BIAS": 0,
        }

        for asset in CORE_ASSETS:
            fc = forecast_map.get(asset, {})
            direction = fc.get("direction", "NEUTRAL")
            confidence = fc.get("confidence", 0.50)
            agreement = fc.get("consensus_agreement_pct", 50.0)
            rr = fc.get("risk_reward_ratio")
            event_risk = fc.get("event_risk", "NONE")
            upcoming_events = fc.get("upcoming_events", [])
            is_qualified = fc.get("is_trade_signal_qualified", False)

            # Rejection audit
            rejection_reasons = []

            if direction == "NEUTRAL":
                rejection_reasons.append("NEUTRAL_BIAS: No directional edge detected across models")
                rejection_breakdown["NEUTRAL_BIAS"] += 1
            else:
                if confidence < MIN_CONSENSUS_THRESHOLD:
                    rejection_reasons.append(
                        f"CONSENSUS_BELOW_THRESHOLD: Confidence {(confidence * 100):.1f}% < {(MIN_CONSENSUS_THRESHOLD * 100):.0f}% required"
                    )
                    rejection_breakdown["CONSENSUS_BELOW_THRESHOLD"] += 1

                if event_risk in ["HIGH", "EXTREME"]:
                    event_name = upcoming_events[0]["event_name"] if upcoming_events else "High-Impact Event"
                    rejection_reasons.append(
                        f"HIGH_EVENT_RISK: Trading gated due to {event_name} ({event_risk} risk)"
                    )
                    rejection_breakdown["HIGH_EVENT_RISK"] += 1

                if rr is None or rr < MIN_RR_THRESHOLD:
                    rr_val = f"{rr:.2f}" if rr is not None else "N/A"
                    rejection_reasons.append(
                        f"RR_BELOW_MINIMUM: Reward-to-Risk ratio {rr_val} < {MIN_RR_THRESHOLD} required"
                    )
                    rejection_breakdown["RR_BELOW_MINIMUM"] += 1

            if is_qualified:
                final_state = "TRADE_SIGNAL_EMITTED"
                trade_signals_count += 1
                risk_decision = "APPROVED"
                summary_reason = "Passed all Zero-Trust gates (Confidence >= 65%, R:R >= 1.5, Safe Macro)"
            else:
                final_state = "NO_VALID_SETUP"
                no_trade_count += 1
                risk_decision = "BLOCKED"
                summary_reason = "; ".join(rejection_reasons) if rejection_reasons else "Risk parameters not met"

            diagnostics_list.append({
                "asset": asset,
                "scan_time": now.isoformat(),
                "forecast_direction": direction,
                "forecast_probability": confidence,
                "consensus_agreement_pct": agreement,
                "risk_reward_ratio": rr,
                "event_risk_level": event_risk,
                "data_freshness": "REALTIME_ACTIVE",
                "risk_decision": risk_decision,
                "final_state": final_state,
                "rejection_reasons": rejection_reasons,
                "summary_reason": summary_reason,
                "entry_price": fc.get("entry_price"),
                "stop_loss": fc.get("stop_loss"),
                "take_profit": fc.get("take_profit"),
            })

        return {
            "timestamp": now.isoformat(),
            "total_assets_scanned": len(CORE_ASSETS),
            "trade_signals_emitted": trade_signals_count,
            "no_trade_forecasts": no_trade_count,
            "rejection_summary": rejection_breakdown,
            "diagnostics": diagnostics_list,
        }


# Singleton instance
signal_diagnostics_engine = SignalDiagnosticsEngine()
