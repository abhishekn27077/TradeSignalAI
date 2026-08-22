from datetime import datetime
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class TradeJournalManager:
    def __init__(self):
        self._trades: dict[str, Any] = {}
        self._next_id = 1
        self.is_running = False

    def start(self):
        from app.utils.event_bus import event_bus
        event_bus.subscribe("PositionClosed", self._on_position_closed)
        event_bus.subscribe("trade_executed", self._on_trade_executed)
        event_bus.subscribe("OrderFilled", self._on_order_filled) # Phase 11: Listen to Paper/Live Executions
        self.is_running = True
        logger.info("TradeJournalManager started")

    async def _on_order_filled(self, payload: dict[str, Any]):
        """Phase 11: Connect Paper Trading accurately to Journal updates"""
        trade = {
            "symbol": payload.get("symbol", ""),
            "direction": payload.get("direction", ""),
            "quantity": payload.get("quantity", 0),
            "price": payload.get("fill_price", 0),
            "pnl": 0.0,
            "status": "OPEN",
            "strategy": payload.get("strategy", "Execution"),
            "notes": f"Order {payload.get('order_id')} FILLED"
        }
        await self.record_trade(trade)

    async def _on_position_closed(self, payload: dict[str, Any]):
        trade = {
            "symbol": payload.get("symbol", ""),
            "direction": payload.get("side", ""),
            "quantity": payload.get("quantity", 0),
            "price": payload.get("exit_price", 0),
            "pnl": payload.get("pnl", 0),
            "status": "CLOSED",
            "strategy": payload.get("strategy_used", ""),
            "notes": payload.get("exit_reason", "")
        }
        await self.record_trade(trade)

    async def _on_trade_executed(self, payload: dict, **kwargs):
        payload_data = kwargs.get("payload", payload) if kwargs else payload
        result = payload_data.get("result", {})
        if result.get("status") in ["SUCCESS", "FILLED"]:
            trade = {
                "symbol": result.get("symbol", payload_data.get("symbol", "")),
                "direction": result.get("side", ""),
                "quantity": result.get("quantity", 0),
                "price": result.get("fill_price", 0),
                "pnl": 0.0,
                "status": "OPEN",
                "strategy": payload_data.get("strategy_used", "Manual"),
                "notes": "Trade Executed",
                "market_regime": payload_data.get("market_regime"),
                "trade_quality": payload_data.get("trade_quality"),
                "session": payload_data.get("session")
            }
            await self.record_trade(trade)

    async def record_trade(self, trade: dict[str, Any]) -> str:
        trade_id = str(self._next_id)
        self._next_id += 1
        record = {
            "id": trade_id,
            **trade,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        self._trades[trade_id] = record
        try:
            from app.database.manager import db_manager
            session = db_manager.get_session()
            if session:
                from app.database.models.journal import TradeJournal
                db_entry = TradeJournal(
                    id=trade_id,
                    symbol=trade.get("symbol", ""),
                    direction=trade.get("direction", ""),
                    quantity=trade.get("quantity", 0),
                    price=trade.get("price", 0),
                    pnl=trade.get("pnl", 0),
                    status=trade.get("status", "EXECUTED"),
                    strategy=trade.get("strategy", ""),
                    notes=trade.get("notes", ""),
                )
                session.add(db_entry)
                await session.commit()
        except Exception as e:
            logger.debug(f"DB journal write skipped: {e}")
            
        try:
            from app.utils.event_bus import event_bus
            await event_bus.publish("JournalUpdated", record)
        except Exception:
            pass
            
        return trade_id

    async def get_trades(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        try:
            from app.database.manager import db_manager
            session = db_manager.get_session()
            if session:
                from sqlalchemy import select

                from app.database.models.journal import TradeJournal
                result = await session.execute(
                    select(TradeJournal).order_by(TradeJournal.created_at.desc()).offset(offset).limit(limit)
                )
                rows = result.scalars().all()
                if rows:
                    return [
                        {
                            "id": r.id,
                            "symbol": r.symbol,
                            "direction": r.direction,
                            "quantity": r.quantity,
                            "price": r.price,
                            "pnl": r.pnl,
                            "status": r.status,
                            "strategy": r.strategy,
                            "notes": r.notes,
                            "created_at": r.created_at.isoformat() if r.created_at else None,
                        }
                        for r in rows
                    ]
        except Exception as e:
            logger.debug(f"DB journal fetch failed: {e}")

        trades = sorted(self._trades.values(), key=lambda x: x.get("recorded_at", ""), reverse=True)
        return trades[offset : offset + limit]

    async def get_trade(self, trade_id: str) -> dict[str, Any] | None:
        try:
            from app.database.manager import db_manager
            session = db_manager.get_session()
            if session:
                from sqlalchemy import select

                from app.database.models.journal import TradeJournal
                result = await session.execute(select(TradeJournal).where(TradeJournal.id == trade_id))
                r = result.scalar_one_or_none()
                if r:
                    return {
                        "id": r.id,
                        "symbol": r.symbol,
                        "direction": r.direction,
                        "quantity": r.quantity,
                        "price": r.price,
                        "pnl": r.pnl,
                        "status": r.status,
                        "strategy": r.strategy,
                        "notes": r.notes,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
        except Exception:
            pass
        return self._trades.get(trade_id)

    async def get_statistics(self) -> dict[str, Any]:
        trades = list(self._trades.values())
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
            }
            
        # Convert dictionary trades to a basic object structure that AnalyticsEngine expects
        class MockTradeRecord:
            def __init__(self, t: dict):
                self.pnl = t.get("pnl", 0)
                self.strategy = t.get("strategy", "Unknown")
                self.market_regime = t.get("market_regime", "Unknown")
                self.session = t.get("session", "Unknown")
                self.trade_quality = t.get("trade_quality", "Unknown")
                self.entry_time = None
                self.exit_time = None

        records = [MockTradeRecord(t) for t in trades]
        
        try:
            from app.analytics.engine import analytics_engine
            stats = analytics_engine.calculate_statistics(records)
            
            # Extract basic fields required by the frontend alongside advanced metrics
            wins = [t for t in trades if t.get("pnl", 0) > 0]
            loses = [t for t in trades if t.get("pnl", 0) < 0]
            total_pnl = sum(t.get("pnl", 0) for t in trades)
            
            return {
                "total_trades": len(trades),
                "winning_trades": len(wins),
                "losing_trades": len(loses),
                "win_rate": stats.get("win_rate", 0),
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(trades) if len(trades) > 0 else 0,
                **stats
            }
        except Exception as e:
            logger.error(f"Error calculating advanced stats: {e}")
            total = len(trades)
            winning = [t for t in trades if t.get("pnl", 0) > 0]
            losing = [t for t in trades if t.get("pnl", 0) < 0]
            total_pnl = sum(t.get("pnl", 0) for t in trades)
            return {
                "total_trades": total,
                "winning_trades": len(winning),
                "losing_trades": len(losing),
                "win_rate": len(winning) / total * 100 if total > 0 else 0,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / total if total > 0 else 0,
            }


journal_manager = TradeJournalManager()