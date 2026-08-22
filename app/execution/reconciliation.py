import logging
from typing import Any

from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class ReconciliationEngine:
    """Detects mismatches between Internal System Portfolio and External Broker."""
    
    def __init__(self):
        event_bus.subscribe("BrokerAccountSynced", self.on_broker_sync)
        
    async def on_broker_sync(self, event_data: dict[str, Any]):
        """Runs the reconciliation check every time we pull from the broker."""
        broker_name = event_data.get("broker_name")
        broker_positions = event_data.get("positions", [])
        
        # In a real implementation, we would pull our internal positions from portfolio_manager
        # and do a diff. For MVP, we'll implement the Diff logic generically.
        internal_positions = [] # Placeholder
        
        mismatches = self.diff_positions(internal_positions, broker_positions)
        
        if mismatches:
            logger.error(f"RECONCILIATION MISMATCH detected on {broker_name}: {mismatches}")
            await event_bus.publish("ReconciliationError", {
                "broker": broker_name,
                "mismatches": mismatches
            })
            
    def diff_positions(self, internal: list[dict[str, Any]], external: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Returns a list of mismatches. Simple implementation for MVP."""
        mismatches = []
        
        ext_map = {p.get("symbol"): p for p in external}
        int_map = {p.get("symbol"): p for p in internal}
        
        for symbol, ext_pos in ext_map.items():
            if symbol not in int_map:
                mismatches.append({"symbol": symbol, "issue": "Exists in broker but not internal"})
            elif int_map[symbol].get("quantity") != ext_pos.get("quantity"):
                mismatches.append({
                    "symbol": symbol, 
                    "issue": "Quantity mismatch",
                    "internal": int_map[symbol].get("quantity"),
                    "external": ext_pos.get("quantity")
                })
                
        for symbol in int_map:
            if symbol not in ext_map:
                mismatches.append({"symbol": symbol, "issue": "Exists internal but not in broker"})
                
        return mismatches

reconciliation_engine = ReconciliationEngine()
