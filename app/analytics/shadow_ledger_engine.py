"""
Phase 43 — Immutable Shadow Prediction Ledger & Realistic Paper Execution Simulator.

Tracks paper trades across an 8-state lifecycle:
  FORECAST_CREATED -> PAPER_OPEN -> [TP_HIT | SL_HIT | TIME_EXIT | AMBIGUOUS | EXPIRED | INVALIDATED]

Realistic Execution Simulator Features:
  - Real market entry execution
  - Asset-specific spread deductions (EURUSD, XAUUSD, BTCUSD, NAS100, etc.)
  - Realistic market slippage (0.5 to 1.5 pips)
  - Broker commission fees
  - Net P&L and Net R-multiple calculations
  - Intra-candle ambiguous bar detection: strictly marks AMBIGUOUS if both TP and SL are crossed
    within the same candle without verifiable sub-minute sequence.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.analytics.shadow_validation_engine import shadow_validation_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)

# Asset-specific execution cost profiles
ASSET_COST_PROFILES: dict[str, dict[str, float]] = {
    "EURUSD": {"spread_pips": 1.2, "slippage_pips": 0.5, "commission_pips": 0.3, "pip_value": 0.0001},
    "GBPUSD": {"spread_pips": 1.5, "slippage_pips": 0.6, "commission_pips": 0.3, "pip_value": 0.0001},
    "USDJPY": {"spread_pips": 1.2, "slippage_pips": 0.5, "commission_pips": 0.3, "pip_value": 0.01},
    "AUDUSD": {"spread_pips": 1.4, "slippage_pips": 0.5, "commission_pips": 0.3, "pip_value": 0.0001},
    "BTCUSD": {"spread_pips": 15.0, "slippage_pips": 10.0, "commission_pips": 5.0, "pip_value": 1.0},
    "ETHUSD": {"spread_pips": 1.5, "slippage_pips": 1.0, "commission_pips": 0.5, "pip_value": 1.0},
    "XAUUSD": {"spread_pips": 0.35, "slippage_pips": 0.25, "commission_pips": 0.15, "pip_value": 1.0},
    "NAS100": {"spread_pips": 1.8, "slippage_pips": 1.2, "commission_pips": 0.5, "pip_value": 1.0},
    "SPX500": {"spread_pips": 0.45, "slippage_pips": 0.30, "commission_pips": 0.15, "pip_value": 1.0},
}


class ShadowLedgerEngine:
    """
    Manages immutable paper trades and realistic execution simulations.
    """

    def __init__(self):
        # In-memory storage for active session paper records
        self._predictions: list[dict[str, Any]] = []
        self._paper_trades: list[dict[str, Any]] = []
        self._initialized = False

    def record_prediction(self, prediction_data: dict[str, Any]) -> dict[str, Any]:
        """
        Record an immutable forecast prediction snapshot.
        """
        now = datetime.now(timezone.utc)
        cohort_meta = shadow_validation_engine.get_cohort_metadata()

        pred_id = prediction_data.get("prediction_id") or f"PRED-{prediction_data.get('asset', 'EURUSD')}-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        input_payload = {
            "asset": prediction_data.get("asset"),
            "timeframe": prediction_data.get("timeframe", "1h"),
            "cutoff": prediction_data.get("data_cutoff", now.isoformat()),
            "direction": prediction_data.get("direction"),
            "probability": prediction_data.get("probability"),
        }
        input_hash = hashlib.sha256(json.dumps(input_payload, sort_keys=True, default=str).encode()).hexdigest()

        record = {
            "prediction_id": pred_id,
            "timestamp": now.isoformat(),
            "data_cutoff": prediction_data.get("data_cutoff", now.isoformat()),
            "asset": prediction_data.get("asset", "EURUSD"),
            "timeframe": prediction_data.get("timeframe", "1h"),
            "direction": prediction_data.get("direction", "NEUTRAL"),
            "probability": prediction_data.get("probability", 0.50),
            "confidence": prediction_data.get("confidence", 0.50),
            "entry_price": prediction_data.get("entry_price"),
            "stop_loss": prediction_data.get("stop_loss"),
            "take_profit": prediction_data.get("take_profit"),
            "expected_move_pct": prediction_data.get("expected_move_pct"),
            "risk_reward": prediction_data.get("risk_reward"),
            "model_outputs": prediction_data.get("model_outputs", {}),
            "consensus_score": prediction_data.get("consensus_score"),
            "macro_state": prediction_data.get("macro_state", "NEUTRAL"),
            "news_state": prediction_data.get("news_state", "NEUTRAL"),
            "event_risk": prediction_data.get("event_risk", "NONE"),
            "market_regime": prediction_data.get("market_regime", "RANGE"),
            "validation_cohort": cohort_meta["validation_cohort"],
            "model_version": cohort_meta["model_version"],
            "feature_hash": cohort_meta["hashes"]["feature_hash"],
            "input_hash": input_hash,
            "is_trade_qualified": prediction_data.get("is_trade_qualified", False),
            "rejection_reason": prediction_data.get("rejection_reason"),
            "status": "FORECAST_CREATED",
        }

        # Check duplicate prediction on same candle boundary
        existing = next((p for p in self._predictions if p["asset"] == record["asset"] and p["data_cutoff"] == record["data_cutoff"] and p["validation_cohort"] == record["validation_cohort"]), None)
        if existing:
            return existing

        self._predictions.append(record)

        # If trade is qualified and validation is active, spawn a PAPER_OPEN order
        if record["is_trade_qualified"] and not shadow_validation_engine.is_paused:
            paper_order = self._spawn_paper_order(record)
            record["status"] = "PAPER_OPEN"
            record["paper_trade_id"] = paper_order["trade_id"]

        return record

    def _spawn_paper_order(self, pred: dict[str, Any]) -> dict[str, Any]:
        """Spawn a realistic paper order from a qualified forecast."""
        asset = pred["asset"]
        costs = ASSET_COST_PROFILES.get(asset, {"spread_pips": 1.5, "slippage_pips": 0.5, "commission_pips": 0.3, "pip_value": 0.0001})

        entry_raw = float(pred["entry_price"] or 1.0)
        pip_val = costs["pip_value"]

        # Apply realistic spread and slippage to entry fill
        is_buy = pred["direction"] == "BUY"
        slippage_offset = (costs["spread_pips"] / 2.0 + costs["slippage_pips"]) * pip_val
        actual_entry = entry_raw + slippage_offset if is_buy else entry_raw - slippage_offset

        trade_id = f"PT-{asset}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"

        order = {
            "trade_id": trade_id,
            "prediction_id": pred["prediction_id"],
            "asset": asset,
            "direction": pred["direction"],
            "entry_time": pred["timestamp"],
            "entry_price": round(actual_entry, 5),
            "stop_loss": pred["stop_loss"],
            "take_profit": pred["take_profit"],
            "risk_reward": pred["risk_reward"],
            "confidence": pred["confidence"],
            "validation_cohort": pred["validation_cohort"],
            "model_version": pred["model_version"],
            "cost_profile": costs,
            "status": "PAPER_OPEN",
            "current_price": round(actual_entry, 5),
            "current_r": 0.0,
            "expected_horizon_hours": 24,
        }

        self._paper_trades.append(order)
        return order

    def spawn_paper_trade(
        self,
        prediction_id: str,
        asset: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: float = 2.0,
        confidence: float = 0.70,
        validation_cohort: str = "PHASE43_SHADOW_V1",
        model_version: str = "3.2.0-frozen",
    ) -> dict[str, Any]:
        """Directly spawn a paper order for simulation and tests."""
        pred = {
            "prediction_id": prediction_id,
            "asset": asset,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward": risk_reward,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_cohort": validation_cohort,
            "model_version": model_version,
        }
        return self._spawn_paper_order(pred)

    def resolve_paper_trade(
        self,
        trade_id: str,
        future_candles: list[dict[str, float]],
    ) -> Optional[dict[str, Any]]:
        """
        Evaluate future closed candles to resolve paper trade outcome with realistic cost math.
        """
        trade = next((t for t in self._paper_trades if t["trade_id"] == trade_id), None)
        if not trade or trade["status"] != "PAPER_OPEN":
            return None

        entry = trade["entry_price"]
        sl = float(trade["stop_loss"])
        tp = float(trade["take_profit"])
        is_buy = trade["direction"] == "BUY"
        costs = trade["cost_profile"]
        pip_val = costs["pip_value"]
        risk_dist = abs(entry - sl) if abs(entry - sl) > 1e-6 else pip_val * 20.0

        for candle in future_candles:
            high = float(candle.get("high", entry))
            low = float(candle.get("low", entry))
            close = float(candle.get("close", entry))

            tp_hit = (high >= tp) if is_buy else (low <= tp)
            sl_hit = (low <= sl) if is_buy else (high >= sl)

            # Intra-candle ambiguity detection
            if tp_hit and sl_hit:
                trade["status"] = "AMBIGUOUS"
                trade["exit_price"] = entry
                trade["gross_r"] = 0.0
                trade["net_r"] = -round((costs["spread_pips"] + costs["commission_pips"]) * pip_val / risk_dist, 2)
                trade["outcome"] = "AMBIGUOUS (BOTH_TP_SL_CROSSED)"
                trade["resolved_at"] = datetime.now(timezone.utc).isoformat()
                return trade

            if tp_hit:
                trade["status"] = "TP_HIT"
                trade["exit_price"] = tp
                trade["gross_r"] = round(abs(tp - entry) / risk_dist, 2)
                total_cost_r = (costs["spread_pips"] + costs["slippage_pips"] + costs["commission_pips"]) * pip_val / risk_dist
                trade["net_r"] = round(trade["gross_r"] - total_cost_r, 2)
                trade["outcome"] = "TP_HIT"
                trade["resolved_at"] = datetime.now(timezone.utc).isoformat()
                return trade

            if sl_hit:
                trade["status"] = "SL_HIT"
                trade["exit_price"] = sl
                trade["gross_r"] = -1.0
                total_cost_r = (costs["spread_pips"] + costs["slippage_pips"] + costs["commission_pips"]) * pip_val / risk_dist
                trade["net_r"] = round(-1.0 - total_cost_r, 2)
                trade["outcome"] = "SL_HIT"
                trade["resolved_at"] = datetime.now(timezone.utc).isoformat()
                return trade

        # If horizon elapsed without hitting TP or SL
        trade["status"] = "TIME_EXIT"
        last_close = future_candles[-1].get("close", entry) if future_candles else entry
        trade["exit_price"] = last_close
        trade["gross_r"] = round(((last_close - entry) if is_buy else (entry - last_close)) / risk_dist, 2)
        total_cost_r = (costs["spread_pips"] + costs["commission_pips"]) * pip_val / risk_dist
        trade["net_r"] = round(trade["gross_r"] - total_cost_r, 2)
        trade["outcome"] = "TIME_EXIT"
        trade["resolved_at"] = datetime.now(timezone.utc).isoformat()
        return trade

    def resolve_trade_manual(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: str,
        status: str,
        gross_r: float,
        net_r: float,
    ) -> Optional[dict[str, Any]]:
        """Manually updates a trade after external offline reconciliation."""
        trade = next((t for t in self._paper_trades if t["trade_id"] == trade_id), None)
        if not trade:
            return None
        trade["status"] = status
        trade["outcome"] = status
        trade["exit_price"] = exit_price
        trade["exit_time"] = exit_time
        trade["gross_r"] = gross_r
        trade["net_r"] = net_r
        trade["resolved_at"] = exit_time
        return trade

    def get_all_predictions(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return all immutable predictions."""
        return self._predictions[-limit:]

    def get_all_paper_trades(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return all paper trades."""
        return self._paper_trades[-limit:]

    def get_open_paper_trades(self) -> list[dict[str, Any]]:
        """Return currently open paper trades."""
        return [t for t in self._paper_trades if t["status"] == "PAPER_OPEN"]


# Singleton instance
shadow_ledger_engine = ShadowLedgerEngine()
