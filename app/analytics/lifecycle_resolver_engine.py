"""
app/analytics/lifecycle_resolver_engine.py
=========================================
Automatic Lifecycle Resolver Engine for TradeSignalAI-v3 (Phase 65).

Monitors LIVE / UNRESOLVED signals, performs post-T0 chronological candle evaluation,
resolves outcomes (WON, LOST, TIME_EXIT, AMBIGUOUS), applies realistic friction
(Spread, Slippage, Broker Fees), and persists realized Net R to the ledger.
"""

from __future__ import annotations
import logging
import sqlite3
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.core.signal_factory import SignalFactory
from app.core.signal_event_logger import signal_event_logger
from app.analytics.causal_outcome_learning_engine import causal_outcome_learning_engine

logger = logging.getLogger("lifecycle_resolver_engine")


class LifecycleResolverEngine:
    """
    Automated background and on-demand lifecycle resolver for canonical signals.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        for candidate in [self.db_path, "trading_fallback.db", "app/database/trading_fallback.db"]:
            if os.path.exists(candidate):
                try:
                    return sqlite3.connect(candidate)
                except Exception:
                    pass
        return None

    def get_unresolved_signals(self) -> List[Dict[str, Any]]:
        """Queries all LIVE or ACTIVE signals from the canonical ledger."""
        conn = self._get_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT signal_id, asset, timeframe, direction, generated_at,
                       information_cutoff_time, expiry_time, entry_price, stop_loss,
                       take_profit, risk_reward, status, outcome
                FROM canonical_signal_ledger
                WHERE status IN ('LIVE', 'ACTIVE', 'QUALIFIED') AND (outcome IS NULL OR outcome = '')
                """
            )
            rows = cur.fetchall()
            signals = []
            for r in rows:
                signals.append({
                    "signal_id": r[0],
                    "asset": r[1],
                    "timeframe": r[2],
                    "direction": r[3],
                    "generated_at": r[4],
                    "information_cutoff_time": r[5],
                    "expiry_time": r[6],
                    "entry_price": float(r[7]),
                    "stop_loss": float(r[8]),
                    "take_profit": float(r[9]),
                    "risk_reward": float(r[10]),
                    "status": r[11],
                    "outcome": r[12],
                })
            return signals
        except Exception as e:
            logger.debug(f"Failed to query unresolved signals: {e}")
            return []
        finally:
            conn.close()

    def run_resolution_cycle(
        self,
        signal_factory_instance: Optional[SignalFactory] = None,
        custom_candles_by_asset: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a complete resolution cycle:
        1. Identifies unresolved signals.
        2. Evaluates candles strictly after information_cutoff_time.
        3. Updates database ledger atomically.
        4. Emits structured telemetry events.
        """
        unresolved = self.get_unresolved_signals()
        resolved_count = 0
        resolved_details = []

        for sig in unresolved:
            asset = sig["asset"]
            post_candles = []
            if custom_candles_by_asset and asset in custom_candles_by_asset:
                post_candles = custom_candles_by_asset[asset]

            # Use causal outcome learning engine to resolve
            resolution = causal_outcome_learning_engine.resolve_signal_outcome(
                signal=sig,
                post_t0_candles=post_candles,
            )

            if resolution.is_resolved:
                outcome_str = resolution.outcome
                net_r_val = resolution.realized_net_r
                exit_p = resolution.exit_price
                exit_t = resolution.exit_time or datetime.now(timezone.utc).isoformat()

                if signal_factory_instance:
                    signal_factory_instance.update_signal_outcome(
                        signal_id=sig["signal_id"],
                        outcome=outcome_str,
                        exit_price=exit_p,
                        exit_time=exit_t,
                        net_r=net_r_val,
                    )
                else:
                    self._update_db_outcome(sig["signal_id"], outcome_str, exit_p, exit_t, net_r_val)

                # Emit lifecycle telemetry
                event_type = f"SIGNAL_{outcome_str}" if outcome_str in ["WON", "LOST", "TIME_EXIT", "AMBIGUOUS"] else "SIGNAL_RESOLVED"
                signal_event_logger.emit_event(
                    event_type=event_type,
                    signal_id=sig["signal_id"],
                    asset=asset,
                    timeframe=sig["timeframe"],
                    payload={
                        "outcome": outcome_str,
                        "exit_price": exit_p,
                        "realized_net_r": net_r_val,
                        "frictions": resolution.frictions,
                    },
                )

                resolved_count += 1
                resolved_details.append({
                    "signal_id": sig["signal_id"],
                    "asset": asset,
                    "outcome": outcome_str,
                    "realized_net_r": net_r_val,
                })

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "unresolved_checked": len(unresolved),
            "resolved_count": resolved_count,
            "total_resolved": resolved_count,
            "resolved_signals": resolved_details,
            "resolved_details": resolved_details,
        }

    def auto_resolve_all_open_signals(self) -> Dict[str, Any]:
        """Automatically resolves all open and due signals."""
        return self.run_resolution_cycle()

    def _update_db_outcome(self, signal_id: str, outcome: str, exit_price: float, exit_time: str, net_r: float):
        """Updates outcome in SQLite directly."""
        conn = self._get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE canonical_signal_ledger
                    SET outcome = ?, net_r = ?, status = 'RESOLVED'
                    WHERE signal_id = ?
                    """,
                    (outcome, net_r, signal_id),
                )
                conn.commit()
            except Exception as e:
                logger.debug(f"Direct outcome update error: {e}")
            finally:
                conn.close()


lifecycle_resolver_engine = LifecycleResolverEngine()
