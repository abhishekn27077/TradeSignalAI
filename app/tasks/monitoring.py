import asyncio

import psutil

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class SystemMonitor:
    def __init__(self):
        self._running = False
        self._task = None
        
        # Operational Metrics
        self.signal_count = 0
        self.ws_reconnects = 0
        self.broker_reconnects = 0
        self.latencies = []
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
    def _on_signal_generated(self, payload: dict, **kwargs):
        self.signal_count += 1
        
    def get_operational_metrics(self) -> dict:
        process = psutil.Process()
        current_mem = process.memory_info().rss / 1024 / 1024
        mem_growth = current_mem - self.start_memory
        
        # Active strategies count
        active_strategies_count = 0
        try:
            from app.strategies.manager import strategy_manager
            active_strategies_count = len(strategy_manager._active_strategies)
        except Exception:
            pass
            
        # Win rate and Trades count
        win_rate = 0.0
        trades_count = 0
        try:
            from app.journal.manager import journal_manager
            trades = journal_manager._trades
            trades_count = len(trades)
            winning = sum(1 for t in trades.values() if t.get("pnl", 0) > 0)
            if trades_count > 0:
                win_rate = (winning / trades_count) * 100
        except Exception:
            pass
            
        return {
            "signals_per_hour": self.signal_count * 1800, # extrapolated
            "trades_per_day": trades_count,
            "win_rate": round(win_rate, 2),
            "average_latency_ms": round(sum(self.latencies) / len(self.latencies), 2) if self.latencies else None,
            "active_strategies": active_strategies_count,
            "event_queue_size": len(event_bus._subscribers),
            "websocket_reconnects": self.ws_reconnects,
            "broker_reconnects": self.broker_reconnects,
            "ai_response_time_ms": None,
            "memory_growth_mb": round(mem_growth, 2)
        }

    async def _monitor_loop(self):
        # Register signal listener
        try:
            event_bus.subscribe("SignalGenerated", self._on_signal_generated)
        except Exception:
            pass
            
        while self._running:
            try:
                # 1. System Health
                from app.api.v1.health import health_status
                health_data = await health_status()
                await event_bus.publish("SystemHealthUpdate", payload=health_data)

                # 2. Portfolio Update
                try:
                    from app.execution.router import smart_router
                    from app.journal.manager import journal_manager
                    
                    bal = {"balance": 0, "equity": 0, "margin": 0, "free_margin": 0}
                    if hasattr(smart_router, "get_balance"):
                        bal = await smart_router.get_balance()
                        
                    stats = {}
                    if hasattr(journal_manager, "get_statistics"):
                        stats = await journal_manager.get_statistics()
                        
                    portfolio_payload = {
                        "balance": bal.get("balance", 0),
                        "equity": bal.get("equity", 0),
                        "margin": bal.get("margin", 0),
                        "free_margin": bal.get("free_margin", 0),
                        "net_profit": stats.get("total_pnl", 0),
                        "win_rate": stats.get("win_rate", 0),
                        "total_trades": stats.get("total_trades", 0)
                    }
                    await event_bus.publish("PortfolioUpdated", payload=portfolio_payload)
                except Exception as e:
                    logger.warning(f"Portfolio monitor error: {e}")

                # 3. Risk Update
                try:
                    from app.risk.limits import risk_limits
                    limits = risk_limits.get_all_limits() if hasattr(risk_limits, "get_all_limits") else {}
                    await event_bus.publish("RiskUpdated", payload=limits)
                except Exception as e:
                    logger.warning(f"Risk monitor error: {e}")
                    
                # 4. Agent Status
                try:
                    from app.agents.manager import agent_registry
                    agents = []
                    for agent_id, agent in agent_registry._agents.items():
                        agents.append({
                            "id": agent.agent_id,
                            "name": agent.agent_id.replace("_001", "").title() + " Analyst",
                            "role": getattr(agent.role, "value", str(agent.role)),
                            "status": "waiting",
                            "confidence": 0,
                            "decision": "WAIT",
                            "performanceScore": 95
                        })
                    await event_bus.publish("AgentStatusUpdated", payload={"agents": agents})
                except Exception as e:
                    logger.warning(f"Agent monitor error: {e}")

            except Exception as e:
                logger.error(f"System monitor loop error: {e}")
            
            # Broadcast updates every 2 seconds
            await asyncio.sleep(2.0)

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("System Monitor started")

    async def stop(self):
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("System Monitor stopped")

system_monitor = SystemMonitor()
