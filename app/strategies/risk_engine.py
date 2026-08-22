"""
app/strategies/risk_engine.py  — Phase 33
==========================================
Phase 33 Risk Engine v2: complete validation gate with full trace output.
Validates entry > 0, SL > 0, TP > 0, R:R >= threshold.
Returns explicit TAKE_NOW / WAIT / NO_TRADE decisions.
"""
import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Zero-trust outcome labels
DECISION_TAKE_NOW  = "TAKE_NOW"
DECISION_WAIT      = "WAIT"
DECISION_NO_TRADE  = "NO_TRADE"

REASON_INVALID_SETUP      = "INVALID_RISK_SETUP"
REASON_POOR_RR            = "POOR_RISK_REWARD"
REASON_RSI_OVERBOUGHT     = "RSI_OVERBOUGHT"
REASON_RSI_OVERSOLD       = "RSI_OVERSOLD"
REASON_NEUTRAL_SIGNAL     = "NEUTRAL_OR_WAIT_SIGNAL"


class RiskEngine:
    """
    Phase 33: Strict Risk & Sizing Engine v2.

    Takes the master signal and generates precise ENTRY, SL, TP, and R:R.
    Returns a complete trace suitable for evidence logging.
    """

    def __init__(self, min_risk_reward: float = 1.5):
        self.min_rr = min_risk_reward

    def calculate_setup(self, df: pd.DataFrame, consensus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates Stop Loss and Take Profit based on ATR. Returns consensus
        dict updated with 'setup' and 'risk_trace' if it meets all constraints.

        Phase 33 guarantees:
          - entry > 0 check
          - SL > 0 check
          - TP > 0 check
          - R:R >= min_rr check
          - explicit TAKE_NOW / WAIT / NO_TRADE decision
          - full risk_trace for evidence ledger
        """
        if consensus.get("master_signal") in ["NEUTRAL", "NO_TRADE", "WAIT"]:
            consensus["risk_trace"] = {
                "decision": DECISION_NO_TRADE,
                "reason": REASON_NEUTRAL_SIGNAL,
                "min_rr_required": self.min_rr,
            }
            return consensus

        if df.empty:
            consensus["master_signal"] = DECISION_NO_TRADE
            consensus["risk_trace"] = {
                "decision": DECISION_NO_TRADE,
                "reason": REASON_INVALID_SETUP,
                "detail": "EMPTY_DATAFRAME",
                "min_rr_required": self.min_rr,
            }
            return consensus

        latest = df.iloc[-1]
        close_price = float(latest.get('close', 0.0))
        atr = float(latest.get('ATR_14', close_price * 0.01))  # fallback 1%
        rsi = float(latest.get('RSI_14', 50.0))
        signal = consensus.get("master_signal")

        # Calculate entry, SL, TP
        if signal == "BULLISH":
            entry = close_price
            stop_loss = entry - (atr * 1.5)
            take_profit = entry + (atr * 3.0)
        elif signal == "BEARISH":
            entry = close_price
            stop_loss = entry + (atr * 1.5)
            take_profit = entry - (atr * 3.0)
        else:
            consensus["master_signal"] = DECISION_NO_TRADE
            consensus["risk_trace"] = {
                "decision": DECISION_NO_TRADE,
                "reason": REASON_NEUTRAL_SIGNAL,
                "signal_received": signal,
            }
            return consensus

        # ── Phase 33: Mandatory validity checks ─────────────────────────────
        if entry <= 0:
            return self._reject(consensus, "ENTRY_ZERO_OR_NEGATIVE", entry, stop_loss, take_profit, atr, rsi)
        if stop_loss <= 0:
            return self._reject(consensus, "SL_ZERO_OR_NEGATIVE", entry, stop_loss, take_profit, atr, rsi)
        if take_profit <= 0:
            return self._reject(consensus, "TP_ZERO_OR_NEGATIVE", entry, stop_loss, take_profit, atr, rsi)

        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        risk_reward = reward / risk if risk != 0 else 0.0
        expected_move_pct = (reward / entry * 100) if entry != 0 else 0.0
        risk_percent = (risk / entry * 100) if entry != 0 else 0.0

        if risk_reward < self.min_rr:
            logger.warning(f"Trade rejected by RiskEngine: R:R {risk_reward:.2f} < {self.min_rr}")
            consensus["master_signal"] = DECISION_NO_TRADE
            consensus.setdefault("intelligence", {})["no_trade_reasons"] = (
                consensus["intelligence"].get("no_trade_reasons", []) + [REASON_POOR_RR]
            )
            consensus["risk_trace"] = {
                "decision": DECISION_NO_TRADE,
                "reason": REASON_POOR_RR,
                "calculated_rr": round(risk_reward, 4),
                "min_rr_required": self.min_rr,
                "current_price": close_price,
                "entry": round(entry, 5),
                "stop_loss": round(stop_loss, 5),
                "take_profit": round(take_profit, 5),
                "atr_at_entry": round(atr, 5),
                "rsi": round(rsi, 2),
            }
            return consensus

        # ── Setup is valid ───────────────────────────────────────────────────
        consensus["setup"] = {
            "current_price": round(close_price, 5),
            "entry_price": round(entry, 5),
            "entry_zone": [round(entry * 0.999, 5), round(entry * 1.001, 5)],
            "stop_loss": round(stop_loss, 5),
            "take_profit": round(take_profit, 5),
            "risk_reward_ratio": round(risk_reward, 2),
            "risk_percent": round(risk_percent, 4),
            "expected_move_pct": round(expected_move_pct, 4),
            "atr_at_entry": round(atr, 5),
        }

        # ── TAKE_NOW vs WAIT decision ────────────────────────────────────────
        if signal == "BULLISH" and rsi > 70.0:
            decision = DECISION_WAIT
            wait_reason = REASON_RSI_OVERBOUGHT
        elif signal == "BEARISH" and rsi < 30.0:
            decision = DECISION_WAIT
            wait_reason = REASON_RSI_OVERSOLD
        else:
            decision = DECISION_TAKE_NOW
            wait_reason = None

        consensus["master_signal"] = decision
        consensus["setup"]["decision"] = decision
        if wait_reason:
            consensus["setup"]["wait_reason"] = wait_reason

        # Full risk trace for evidence ledger
        consensus["risk_trace"] = {
            "decision": decision,
            "wait_reason": wait_reason,
            "current_price": round(close_price, 5),
            "entry": round(entry, 5),
            "entry_zone": consensus["setup"]["entry_zone"],
            "stop_loss": round(stop_loss, 5),
            "take_profit": round(take_profit, 5),
            "risk_reward_ratio": round(risk_reward, 2),
            "risk_percent": round(risk_percent, 4),
            "expected_move_pct": round(expected_move_pct, 4),
            "atr_at_entry": round(atr, 5),
            "rsi": round(rsi, 2),
            "min_rr_required": self.min_rr,
            "validity": {
                "entry_valid": entry > 0,
                "sl_valid": stop_loss > 0,
                "tp_valid": take_profit > 0,
                "rr_valid": risk_reward >= self.min_rr,
            },
        }

        return consensus

    def _reject(
        self,
        consensus: Dict[str, Any],
        reason: str,
        entry: float,
        sl: float,
        tp: float,
        atr: float,
        rsi: float,
    ) -> Dict[str, Any]:
        consensus["master_signal"] = DECISION_NO_TRADE
        consensus.setdefault("intelligence", {}).setdefault("no_trade_reasons", []).append(
            REASON_INVALID_SETUP
        )
        consensus["risk_trace"] = {
            "decision": DECISION_NO_TRADE,
            "reason": REASON_INVALID_SETUP,
            "detail": reason,
            "entry": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "atr_at_entry": atr,
            "rsi": rsi,
            "validity": {
                "entry_valid": entry > 0,
                "sl_valid": sl > 0,
                "tp_valid": tp > 0,
                "rr_valid": False,
            },
        }
        logger.warning(f"RiskEngine REJECTED: {reason}")
        return consensus


risk_engine = RiskEngine()
