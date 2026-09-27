"""
Reconciliation Engine — Phase 74

Detects mismatches between Internal System Portfolio and External Broker/Paper state.
Replaces the old stub (internal_positions = []).

Required states:
    MATCHED           — position matches exactly
    MISMATCH          — position diverges (qty, side, or price)
    MISSING_INTERNAL  — position exists in broker but not in internal
    MISSING_EXTERNAL  — position exists internally but not in broker
    UNKNOWN           — broker unavailable or unreachable
    STALE_ORDER       — order in pending state for too long
    PARTIAL_FILL      — fill quantity doesn't match expected

Never silently treats missing broker data as MATCHED.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class ReconStatus(str, Enum):
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    MISSING_INTERNAL = "MISSING_INTERNAL"  # In broker but not internal
    MISSING_EXTERNAL = "MISSING_EXTERNAL"  # In internal but not broker
    UNKNOWN = "UNKNOWN"                     # Broker unavailable
    STALE_ORDER = "STALE_ORDER"            # Order pending too long
    PARTIAL_FILL = "PARTIAL_FILL"          # Fill qty mismatch


@dataclass
class ReconResult:
    symbol: str
    status: ReconStatus
    internal: dict[str, Any] | None = None
    external: dict[str, Any] | None = None
    issues: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ReconciliationEngine:
    """
    Detects mismatches between internal and broker/paper positions.
    
    Architecture:
    1. Fetch internal positions from position_manager (source of truth)
    2. Fetch broker/paper positions from paper executor
    3. Compare symbol-by-symbol
    4. Fail closed: if broker is unavailable, status = UNKNOWN (not MATCHED)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._last_recon_time: datetime | None = None
        self._last_broker_available: bool = True
        self._recon_history: list[ReconResult] = []
        self._max_history: int = 100
        self._lock = asyncio.Lock()

    def _subscribe(self):
        """Subscribe to broker/paper events."""
        try:
            from app.utils.event_bus import event_bus
            event_bus.subscribe("BrokerAccountSynced", self.on_broker_sync)
            event_bus.subscribe("PositionClosed", self.on_position_closed)
            event_bus.subscribe("OrderFilled", self.on_order_filled)
            event_bus.subscribe("PaperExecutorState", self.on_paper_state)
            logger.info("ReconciliationEngine subscribed to event bus")
        except Exception as e:
            logger.warning(f"Could not subscribe to event bus: {e}")

    async def on_broker_sync(self, event_data: dict[str, Any]):
        """Trigger reconciliation on broker sync event."""
        await self.run_reconciliation()

    async def on_position_closed(self, event_data: dict[str, Any]):
        """Trigger reconciliation on position closed event."""
        await self.run_reconciliation()

    async def on_order_filled(self, event_data: dict[str, Any]):
        """Trigger reconciliation on order fill event."""
        await self.run_reconciliation()

    async def on_paper_state(self, event_data: dict[str, Any]):
        """Trigger reconciliation on paper executor state change."""
        await self.run_reconciliation()

    # ── Position Fetchers ────────────────────────────────────────────────────

    def _get_internal_positions(self) -> list[dict[str, Any]]:
        """Fetch authoritative positions from internal position manager."""
        try:
            from app.execution.position_manager import position_manager
            return position_manager.get_all_positions_as_list()
        except Exception as e:
            logger.error(f"Failed to fetch internal positions: {e}")
            return []

    def _get_paper_positions(self) -> tuple[list[dict[str, Any]], bool]:
        """
        Fetch positions from paper executor.
        Returns (positions, broker_available).
        Broker unavailable = (empty_list, False), NOT (empty_list, True).
        """
        try:
            from app.execution.paper.executor import paper_executor
            raw = paper_executor.get_all_positions()
            positions = []
            for symbol, pos in raw.items():
                positions.append({
                    "symbol": symbol,
                    "quantity": pos.quantity,
                    "average_entry_price": pos.average_entry_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "status": "ACTIVE"
                })
            self._last_broker_available = True
            return positions, True
        except Exception as e:
            logger.error(f"Failed to fetch paper positions: {e}")
            self._last_broker_available = False
            return [], False

    # ── Core Diff Logic ──────────────────────────────────────────────────────

    def diff_positions(
        self,
        internal: list[dict[str, Any]],
        external: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Compare internal vs external positions and return mismatch list.
        
        Missing external = MISSING_EXTERNAL (not MATCHED).
        """
        mismatches = []
        ext_map = {p.get("symbol", "").upper(): p for p in external}
        int_map = {p.get("symbol", "").upper(): p for p in internal}

        # Check each internal position
        for symbol, int_pos in int_map.items():
            ext_pos = ext_map.get(symbol)
            if ext_pos is None:
                mismatches.append({
                    "symbol": symbol,
                    "issue": "MISSING_EXTERNAL",
                    "internal_quantity": int_pos.get("quantity"),
                    "external_quantity": None,
                    "description": "Position exists internally but not in broker"
                })
            elif not self._positions_match(int_pos, ext_pos):
                mismatches.append({
                    "symbol": symbol,
                    "issue": "QUANTITY_MISMATCH",
                    "internal_quantity": int_pos.get("quantity"),
                    "external_quantity": ext_pos.get("quantity"),
                    "internal_avg_price": int_pos.get("average_entry_price"),
                    "external_avg_price": ext_pos.get("average_entry_price"),
                    "description": f"Position qty mismatch: internal={int_pos.get('quantity')} vs external={ext_pos.get('quantity')}"
                })

        # Check each external position
        for symbol, ext_pos in ext_map.items():
            int_pos = int_map.get(symbol)
            if int_pos is None:
                mismatches.append({
                    "symbol": symbol,
                    "issue": "MISSING_INTERNAL",
                    "internal_quantity": None,
                    "external_quantity": ext_pos.get("quantity"),
                    "description": "Position exists in broker but not internally"
                })

        return mismatches

    def _positions_match(self, a: dict[str, Any], b: dict[str, Any], tolerance: float = 1e-6) -> bool:
        """Compare two positions for equality with floating-point tolerance."""
        qty_match = abs(a.get("quantity", 0) - b.get("quantity", 0)) < tolerance
        # Price check: allow small difference for slippage
        price_a = a.get("average_entry_price", 0)
        price_b = b.get("average_entry_price", 0)
        if price_a == 0 and price_b == 0:
            price_match = True
        elif price_a == 0 or price_b == 0:
            price_match = False
        else:
            price_match = abs(price_a - price_b) / max(abs(price_a), abs(price_b)) < 0.001  # 0.1% tolerance
        return qty_match and price_match

    # ── Main Reconciliation ──────────────────────────────────────────────────

    async def run_reconciliation(self) -> dict[str, Any]:
        """
        Run full reconciliation between internal and broker positions.
        Returns a summary dict with results for each symbol.
        """
        async with self._lock:
            internal = self._get_internal_positions()
            external, broker_available = self._get_paper_positions()

            self._last_recon_time = datetime.now(timezone.utc)
            
            if not broker_available:
                # FAIL CLOSED: broker unavailable = UNKNOWN, not MATCHED
                logger.warning("RECONCILIATION: Broker unavailable — status set to UNKNOWN")
                result = {
                    "status": "UNKNOWN",
                    "broker_available": False,
                    "internal_count": len(internal),
                    "external_count": 0,
                    "mismatches": [],
                    "timestamp": self._last_recon_time.isoformat()
                }
                await self._publish_recon_result(result)
                return result

            mismatches = self.diff_positions(internal, external)
            
            if mismatches:
                logger.error(f"RECONCILIATION MISMATCH detected: {mismatches}")
                await self._publish_recon_error(mismatches)
            else:
                logger.info(f"RECONCILIATION: All positions matched ({len(internal)} symbols)")

            result = {
                "status": "MATCHED" if not mismatches else "MISMATCH",
                "broker_available": True,
                "internal_count": len(internal),
                "external_count": len(external),
                "mismatch_count": len(mismatches),
                "mismatches": mismatches,
                "timestamp": self._last_recon_time.isoformat()
            }
            await self._publish_recon_result(result)
            return result

    # ── 3-Way Reconciliation (Internal vs Broker vs Ledger) ───────────────────

    def _get_ledger_positions(self) -> tuple[list[dict[str, Any]], bool]:
        """
        Fetch active positions from the Authoritative Canonical Prospective Ledger.
        Returns (positions, ledger_available).
        """
        try:
            from app.core.canonical_prospective_ledger import CanonicalProspectiveLedger, STATUS_ACTIVE
            ledger = CanonicalProspectiveLedger()
            signals = ledger.get_signals_by_filter(date_filter="ALL", status=STATUS_ACTIVE)
            positions = []
            for s in signals:
                positions.append({
                    "symbol": s.asset.upper(),
                    "signal_id": s.signal_id,
                    "direction": s.direction,
                    "entry_price": s.actual_entry_price or s.entry_price,
                    "stop_loss": s.stop_loss,
                    "take_profit": s.take_profit,
                })
            return positions, True
        except Exception as e:
            logger.error(f"Failed to fetch ledger positions: {e}")
            return [], False

    async def run_3way_reconciliation(self) -> dict[str, Any]:
        """
        Institutional 3-way reconciliation across:
        1. Internal Position Manager
        2. External / Paper Broker
        3. Authoritative Canonical Prospective Ledger

        Detects quantity mismatches, missing positions, orphan ledger signals,
        and ledger desynchronizations. Never silently ignores discrepancies.
        """
        async with self._lock:
            internal = self._get_internal_positions()
            external, broker_available = self._get_paper_positions()
            ledger_positions, ledger_available = self._get_ledger_positions()

            now_iso = datetime.now(timezone.utc).isoformat()

            if not broker_available or not ledger_available:
                status = "UNKNOWN"
                logger.warning(
                    f"3-WAY RECONCILIATION: Fail-closed. Broker available={broker_available}, "
                    f"Ledger available={ledger_available} -> Status UNKNOWN"
                )
                return {
                    "status": status,
                    "broker_available": broker_available,
                    "ledger_available": ledger_available,
                    "mismatches": [],
                    "timestamp": now_iso,
                }

            # 1. Standard 2-way diff (Internal vs External)
            mismatches = self.diff_positions(internal, external)

            # 2. Cross-check against Canonical Ledger
            int_symbols = {p["symbol"].upper() for p in internal}
            ext_symbols = {p["symbol"].upper() for p in external}
            active_live_symbols = int_symbols | ext_symbols
            ledger_symbols = {p["symbol"].upper() for p in ledger_positions}

            # Check for positions active live but not active in ledger
            for sym in active_live_symbols:
                if sym not in ledger_symbols:
                    mismatches.append({
                        "symbol": sym,
                        "issue": "LEDGER_DESYNC",
                        "description": f"Symbol {sym} is active live but missing from active canonical ledger",
                    })

            # Check for signals active in ledger but not active live
            for sym in ledger_symbols:
                if sym not in active_live_symbols:
                    mismatches.append({
                        "symbol": sym,
                        "issue": "ORPHAN_LEDGER_SIGNAL",
                        "description": f"Signal for {sym} is marked ACTIVE in ledger but no live position exists",
                    })

            # Emit typed ReconciliationMismatch events if divergence detected
            if mismatches:
                logger.error(f"3-WAY RECONCILIATION DETECTED {len(mismatches)} MISMATCHES: {mismatches}")
                try:
                    from app.core.events import ReconciliationMismatch
                    for m in mismatches:
                        evt = ReconciliationMismatch(
                            symbol=m["symbol"],
                            mismatch_type=m["issue"],
                            details=m,
                        )
                        from app.utils.event_bus import event_bus
                        await event_bus.publish("ReconciliationMismatch", evt.to_dict())
                except Exception as e:
                    logger.warning(f"Failed to publish ReconciliationMismatch event: {e}")

            result = {
                "status": "MATCHED" if not mismatches else "MISMATCH",
                "broker_available": True,
                "ledger_available": True,
                "internal_count": len(internal),
                "external_count": len(external),
                "ledger_count": len(ledger_positions),
                "mismatch_count": len(mismatches),
                "mismatches": mismatches,
                "timestamp": now_iso,
            }
            await self._publish_recon_result(result)
            return result

    # ── Per-Symbol Reconciliation ────────────────────────────────────────────

    async def reconcile_symbol(self, symbol: str) -> ReconResult:
        """Reconcile a single symbol. Returns detailed ReconResult."""
        internal = self._get_internal_positions()
        external, broker_available = self._get_paper_positions()

        int_map = {p["symbol"].upper(): p for p in internal}
        ext_map = {p["symbol"].upper(): p for p in external}

        int_pos = int_map.get(symbol.upper())
        ext_pos = ext_map.get(symbol.upper())

        if not broker_available:
            return ReconResult(
                symbol=symbol,
                status=ReconStatus.UNKNOWN,
                internal=int_pos,
                external=None,
                issues=["Broker unavailable"]
            )

        if int_pos is None and ext_pos is None:
            return ReconResult(symbol=symbol, status=ReconStatus.MATCHED, internal=None, external=None)
        elif int_pos is None:
            return ReconResult(
                symbol=symbol, status=ReconStatus.MISSING_INTERNAL,
                internal=None, external=ext_pos,
                issues=["Position exists in broker but not internally"]
            )
        elif ext_pos is None:
            return ReconResult(
                symbol=symbol, status=ReconStatus.MISSING_EXTERNAL,
                internal=int_pos, external=None,
                issues=["Position exists internally but not in broker"]
            )
        elif not self._positions_match(int_pos, ext_pos):
            issues = []
            if abs(int_pos["quantity"] - ext_pos["quantity"]) > 1e-6:
                issues.append(f"Quantity: internal={int_pos['quantity']} vs external={ext_pos['quantity']}")
            return ReconResult(
                symbol=symbol, status=ReconStatus.MISMATCH,
                internal=int_pos, external=ext_pos,
                issues=issues
            )
        else:
            return ReconResult(symbol=symbol, status=ReconStatus.MATCHED, internal=int_pos, external=ext_pos)

    # ── Event Publishing ────────────────────────────────────────────────────

    async def _publish_recon_result(self, result: dict[str, Any]):
        """Publish reconciliation result to event bus."""
        try:
            from app.utils.event_bus import event_bus
            await event_bus.publish("ReconciliationCompleted", result)
        except Exception:
            pass

    async def _publish_recon_error(self, mismatches: list[dict[str, Any]]):
        """Publish reconciliation error to event bus and logs."""
        logger.error(f"RECONCILIATION ERROR: {len(mismatches)} mismatches")
        for m in mismatches:
            logger.error(f"  {m['symbol']}: {m['issue']} — {m.get('description', '')}")
        try:
            from app.utils.event_bus import event_bus
            await event_bus.publish("ReconciliationError", {"mismatches": mismatches})
        except Exception:
            pass

    # ── Query Methods ───────────────────────────────────────────────────────

    def get_last_recon_time(self) -> datetime | None:
        return self._last_recon_time

    def get_last_status(self) -> str:
        if self._last_recon_time is None:
            return "NEVER_RUN"
        return "AVAILABLE" if self._last_broker_available else "UNKNOWN"


reconciliation_engine = ReconciliationEngine()
reconciliation_engine._subscribe()
