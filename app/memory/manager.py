from typing import Any

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class MemoryManager:
    def __init__(self):
        self._memory: dict[str, list[dict[str, Any]]] = {}
        self._initialized = False

    def start(self):
        self._initialized = True
        
        try:
            event_bus.subscribe("TradeReviewed", self._handle_trade_reviewed)
            event_bus.subscribe("PositionClosed", self._handle_position_closed)
        except Exception as e:
            logger.debug(f"Memory event subscription deferred: {e}")

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        try:
            from app.memory.vector.provider import InMemoryVectorProvider
            from app.memory.vector.search import HybridSearchEngine
            provider = InMemoryVectorProvider()
            engine = HybridSearchEngine(provider)
            return engine.search_similar(query, limit)
        except Exception as e:
            logger.debug(f"Memory search fallback: {e}")
            
        results = []
        for cat in self._memory.values():
            results.extend(cat)
        return results[:limit]
        
    async def find_similar_setups(self, symbol: str, timeframe: str, condition_desc: str) -> dict[str, Any]:
        """
        Phase 12: Memory Intelligence.
        Find historical trades matching the setup, and return statistics.
        """
        query = f"{symbol} {timeframe} {condition_desc}"
        similar = await self.search(query, limit=100)
        
        # Filter strictly by trade_review
        trades = [m for m in similar if m.get("type") in ["trade_review", "trade_reflection"] and m.get("symbol") == symbol]
        
        if not trades:
            return {"count": 0, "win_rate": 0.0, "best_strategy": "N/A"}
            
        wins = [t for t in trades if t.get("metadata", {}).get("pnl", 0) > 0]
        win_rate = len(wins) / len(trades)
        
        # Find best strategy
        strat_pnl = {}
        for t in trades:
            strat = t.get("metadata", {}).get("strategy", "Unknown")
            pnl = t.get("metadata", {}).get("pnl", 0)
            strat_pnl[strat] = strat_pnl.get(strat, 0) + pnl
            
        best_strat = max(strat_pnl.items(), key=lambda x: x[1])[0] if strat_pnl else "N/A"
        
        return {
            "count": len(trades),
            "win_rate": win_rate,
            "best_strategy": best_strat
        }

    async def store(self, key: str, value: dict[str, Any]):
        if key not in self._memory:
            self._memory[key] = []
        self._memory[key].append(value)
        try:
            from app.utils.event_bus import event_bus
            await event_bus.publish("MemoryUpdated", {"key": key, "entry": value})
        except Exception:
            pass

    async def get_statistics(self) -> dict[str, Any]:
        total = sum(len(v) for v in self._memory.values())
        return {
            "total_entries": total,
            "categories": list(self._memory.keys()),
            "category_counts": {k: len(v) for k, v in self._memory.items()},
        }

    async def _handle_trade_reviewed(self, payload: dict[str, Any]):
        """Generate memory entry from a completed trade review."""
        try:
            symbol = payload.get("symbol", "UNKNOWN")
            direction = payload.get("direction", "")
            pnl = payload.get("pnl", 0)
            strategy = payload.get("strategy", "")
            
            outcome = "profitable" if pnl > 0 else "losing"
            reflection = f"{outcome.capitalize()} {direction} trade on {symbol} using {strategy}. PnL: {pnl:.2f}"
            
            entry = {
                "text": reflection,
                "symbol": symbol,
                "type": "trade_reflection",
                "timestamp": int(__import__('time').time() * 1000),
                "metadata": {
                    "pnl": pnl,
                    "direction": direction,
                    "strategy": strategy,
                    "outcome": outcome,
                    "lesson": f"{'Continue using' if pnl > 0 else 'Review'} {strategy} on {symbol} in similar conditions."
                }
            }
            await self.store("trade_reflections", entry)
            logger.debug(f"Memory stored trade reflection for {symbol}")
        except Exception as e:
            logger.debug(f"Trade review memory failed: {e}")

    async def _handle_position_closed(self, payload: dict[str, Any]):
        """Generate memory entry from a closed position."""
        try:
            symbol = payload.get("symbol", "UNKNOWN")
            direction = payload.get("side", "")
            pnl = payload.get("pnl", 0.0)
            strategy = payload.get("strategy_used", "")
            
            outcome = "profitable" if pnl > 0 else "losing"
            reflection = f"{outcome.capitalize()} {direction} trade on {symbol} using {strategy}. PnL: {pnl:.2f}"
            
            entry = {
                "text": reflection,
                "symbol": symbol,
                "type": "trade_review",
                "timestamp": int(__import__('time').time() * 1000),
                "metadata": {
                    "pnl": pnl,
                    "direction": direction,
                    "strategy": strategy,
                    "outcome": outcome,
                    "lesson": f"{'Continue using' if pnl > 0 else 'Review'} {strategy} on {symbol} in similar conditions."
                }
            }
            await self.store("past_trades", entry)
            logger.debug(f"Memory stored position closed for {symbol}")
        except Exception as e:
            logger.debug(f"Position closed memory failed: {e}")


memory_manager = MemoryManager()