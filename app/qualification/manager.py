import asyncio
import os
import time
from datetime import datetime
from typing import Any

import psutil

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class QualificationManager:
    def __init__(self):
        self.active_mode = None  # None, "synthetic", "historical", "live"
        self.is_running = False
        
        # Metrics
        self.metrics = {
            "trades_completed": 0,
            "signals_generated": 0,
            "orders_filled": 0,
            "orders_rejected": 0,
            "journal_entries": 0,
            "memory_records": 0,
            "cpu_percent": 0.0,
            "ram_mb": 0.0,
            "db_size_mb": 0.0,
            "ws_latency_ms": 0.0,
            "api_latency_ms": 0.0
        }
        
        self.start_time: datetime | None = None
        self._monitoring_task: asyncio.Task | None = None
        
        # Register EventBus subscribers
        event_bus.subscribe("SignalGenerated", self._on_signal)
        event_bus.subscribe("OrderFilled", self._on_order_filled)
        event_bus.subscribe("OrderRejected", self._on_order_rejected)
        event_bus.subscribe("PositionClosed", self._on_trade_completed)
        event_bus.subscribe("JournalEntryCreated", self._on_journal)
        event_bus.subscribe("MemoryCreated", self._on_memory)

    async def _on_signal(self, payload: dict[str, Any]):
        if self.is_running:
            self.metrics["signals_generated"] += 1

    async def _on_order_filled(self, payload: dict[str, Any]):
        if self.is_running:
            self.metrics["orders_filled"] += 1

    async def _on_order_rejected(self, payload: dict[str, Any]):
        if self.is_running:
            self.metrics["orders_rejected"] += 1

    async def _on_trade_completed(self, payload: dict[str, Any]):
        if self.is_running:
            self.metrics["trades_completed"] += 1

    async def _on_journal(self, payload: dict[str, Any]):
        if self.is_running:
            self.metrics["journal_entries"] += 1

    async def _on_memory(self, payload: dict[str, Any]):
        if self.is_running:
            self.metrics["memory_records"] += 1

    def _get_db_size(self) -> float:
        db_path = "trading_fallback.db"
        if os.path.exists(db_path):
            return os.path.getsize(db_path) / (1024 * 1024)
        return 0.0

    async def _monitor_loop(self):
        while self.is_running:
            try:
                self.metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
                process = psutil.Process(os.getpid())
                self.metrics["ram_mb"] = process.memory_info().rss / (1024 * 1024)
                self.metrics["db_size_mb"] = self._get_db_size()
            except Exception as e:
                logger.warning(f"Error reading metrics: {e}")
            await asyncio.sleep(2)

    async def _synthetic_pump(self):
        # Pump fake ticks at high speed to trigger the engine
        while self.is_running and self.active_mode == "synthetic":
            tick = {
                "symbol": "BTCUSD",
                "bid": 60000 + (time.time() % 100),
                "ask": 60000 + (time.time() % 100) + 1,
                "last": 60000 + (time.time() % 100),
                "volume": 5,
                "timestamp": datetime.utcnow().isoformat()
            }
            await event_bus.publish("MarketDataTick", tick)
            await asyncio.sleep(0.1)

    async def start_mode(self, mode: str, config: dict[str, Any] = None):
        if self.is_running:
            await self.stop()
            
        self.active_mode = mode
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        # Reset counters
        for k in ["trades_completed", "signals_generated", "orders_filled", "orders_rejected", "journal_entries", "memory_records"]:
            self.metrics[k] = 0
            
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Qualification Mode {mode} started")
        
        # Dispatch specific mode logic here
        if mode == "synthetic":
            from app.market_data.providers.manager import market_provider_manager
            from app.market_data.providers.simulated import SimulatedDataProvider
            
            sim = market_provider_manager.get_provider("simulated")
            if not sim:
                sim = SimulatedDataProvider()
                market_provider_manager.register("simulated", sim)
            
            if hasattr(sim, "set_regime"):
                regime = config.get("regime", "trending") if config else "trending"
                sim.set_regime(regime)
                
            asyncio.create_task(self._synthetic_pump())
            
        elif mode == "historical":
            from app.market_data.providers.manager import market_provider_manager
            market_provider_manager.fallback_to_simulated()  # Actually we might need a replay mode here
        elif mode == "live":
            pass

    async def stop(self):
        self.is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Qualification Mode stopped")
        
    def get_status(self) -> dict[str, Any]:
        return {
            "is_running": self.is_running,
            "active_mode": self.active_mode,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time and self.is_running else 0,
            "metrics": self.metrics
        }

qualification_manager = QualificationManager()
