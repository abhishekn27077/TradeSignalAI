"""
app/core/signal_identity.py  — Phase 33
========================================
SignalIdentityGuard: deterministic duplicate prevention.
Computes a SHA-256 identity hash for any candidate signal based on its
immutable characteristics. If the same setup has already been persisted,
the guard blocks a second emission.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

# Increment this version string when strategy logic changes.
STRATEGY_VERSION = "v3.33.0"


class SignalIdentityGuard:
    """
    Prevents duplicate signals for identical market setups.

    Identity is determined by:
        asset + timeframe + candle_timestamp (ISO) + direction + strategy_version

    This is deterministic: the same inputs always produce the same hash.
    """

    @staticmethod
    def compute_hash(
        asset: str,
        timeframe: str,
        candle_timestamp: datetime | str,
        direction: str,
        strategy_version: str = STRATEGY_VERSION,
    ) -> str:
        """Returns a 64-character SHA-256 hex digest."""
        if isinstance(candle_timestamp, datetime):
            ts_str = candle_timestamp.isoformat()
        else:
            ts_str = str(candle_timestamp)

        payload = {
            "asset": asset.upper().strip(),
            "timeframe": timeframe.upper().strip(),
            "candle_timestamp": ts_str,
            "direction": direction.upper().strip(),
            "strategy_version": strategy_version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    async def is_duplicate(
        db_session: Any,
        identity_hash: str,
    ) -> bool:
        """
        Checks the database for an existing signal with the same identity hash.

        Parameters
        ----------
        db_session : SQLAlchemy async session
        identity_hash : str
            The 64-character hash from compute_hash()

        Returns
        -------
        bool
            True if a duplicate exists (signal should be suppressed).
        """
        try:
            from sqlalchemy import select
            from app.database.models.signal import SignalLifecycleModel

            stmt = select(SignalLifecycleModel.id).where(
                SignalLifecycleModel.duplicate_protection_hash == identity_hash
            ).limit(1)
            result = await db_session.execute(stmt)
            row = result.first()
            if row:
                logger.warning(f"DUPLICATE_SIGNAL blocked — hash {identity_hash[:16]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"SignalIdentityGuard.is_duplicate error (failing closed): {e}")
            # Fail closed — suppress/quarantine the signal on error to prevent duplicate execution
            return True

    @staticmethod
    def build_identity(signal_dict: dict[str, Any]) -> str:
        """Convenience: extract fields from a signal dict and compute hash."""
        return SignalIdentityGuard.compute_hash(
            asset=signal_dict.get("asset", signal_dict.get("symbol", "")),
            timeframe=signal_dict.get("timeframe", "H4"),
            candle_timestamp=signal_dict.get("candle_timestamp", signal_dict.get("created_at", "")),
            direction=signal_dict.get("direction", ""),
        )
