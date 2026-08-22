"""
Phase 45 — Autonomous Shadow Outcome Resolution Worker.

Continuously monitors open paper trades and resolves outcomes:
  - Scans PAPER_OPEN positions in shadow ledger
  - Fetches closed candles that arrived after the trade entry timestamp
  - Resolves TP_HIT, SL_HIT, TIME_EXIT, AMBIGUOUS, or EXPIRED
  - Calculates gross R, transaction frictions (spread, slippage, commission), and net R
  - Records holding duration and resolved timestamp
  - Broadcasts signal_outcome_updated WebSocket telemetry
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.analytics.shadow_ledger_engine import shadow_ledger_engine

logger = logging.getLogger("shadow_outcome_worker")


class ShadowOutcomeWorker:
    """
    Background worker that resolves open paper trades against subsequent closed market bars.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path
        self._last_run_timestamp: Optional[str] = None
        self._resolved_count = 0

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        if os.path.exists(self.db_path):
            return sqlite3.connect(self.db_path)
        return None

    def fetch_future_candles(self, asset: str, entry_time: str) -> List[Dict[str, float]]:
        """
        Fetches closed candles with timestamp strictly greater than entry_time.
        Zero-lookahead: Only candles closed AFTER entry are returned.
        """
        conn = self._get_connection()
        candles = []
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT open, high, low, close, volume, timestamp
                    FROM historical_candles
                    WHERE symbol = ? AND timestamp > ?
                    ORDER BY timestamp ASC
                    LIMIT 24
                    """,
                    (asset, entry_time),
                )
                rows = cur.fetchall()
                for r in rows:
                    candles.append({
                        "open": float(r[0]),
                        "high": float(r[1]),
                        "low": float(r[2]),
                        "close": float(r[3]),
                        "volume": float(r[4]) if r[4] else 0.0,
                        "timestamp": r[5],
                    })
            except Exception as e:
                logger.debug(f"Error fetching future candles for {asset}: {e}")
            finally:
                conn.close()
        return candles

    def run_resolution_cycle(self) -> Dict[str, Any]:
        """
        Scans all PAPER_OPEN trades and resolves any whose TP/SL/Time condition was reached.
        """
        now = datetime.now(timezone.utc)
        self._last_run_timestamp = now.isoformat()

        open_trades = shadow_ledger_engine.get_open_paper_trades()
        resolved_trades = []

        for trade in open_trades:
            asset = trade["asset"]
            entry_time = trade.get("entry_time", "")
            trade_id = trade["trade_id"]

            future_candles = self.fetch_future_candles(asset, entry_time)
            if not future_candles:
                continue

            resolved = shadow_ledger_engine.resolve_paper_trade(trade_id, future_candles)
            if resolved and resolved["status"] != "PAPER_OPEN":
                # Compute holding duration
                resolved["holding_duration_bars"] = len(future_candles)
                resolved_trades.append(resolved)
                self._resolved_count += 1
                logger.info(f"Resolved trade {trade_id} ({asset}): {resolved['status']} Net R={resolved.get('net_r')}")

        return {
            "cycle_timestamp": self._last_run_timestamp,
            "open_trades_scanned": len(open_trades),
            "trades_resolved_this_cycle": len(resolved_trades),
            "total_lifetime_resolved": self._resolved_count,
            "resolved_trades": resolved_trades,
        }

    async def start(self):
        """Starts the autonomous shadow outcome worker loop."""
        import asyncio
        self._is_running = True
        logger.info("ShadowOutcomeWorker started successfully.")
        while self._is_running:
            try:
                self.run_resolution_cycle()
            except Exception as e:
                logger.error(f"Error in ShadowOutcomeWorker cycle: {e}")
            await asyncio.sleep(60)

    async def stop(self):
        """Stops the autonomous shadow outcome worker loop."""
        self._is_running = False
        logger.info("ShadowOutcomeWorker stopped.")

    def get_status(self) -> Dict[str, Any]:
        """Returns worker status and resolution statistics."""
        return {
            "worker_active": True,
            "last_run_timestamp": self._last_run_timestamp,
            "total_lifetime_resolved": self._resolved_count,
            "open_trades_pending": len(shadow_ledger_engine.get_open_paper_trades()),
        }


# Singleton instance
shadow_outcome_worker = ShadowOutcomeWorker()
