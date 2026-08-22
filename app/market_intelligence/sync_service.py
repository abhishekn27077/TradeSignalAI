"""
Data Sync Service
===================
Background async task that periodically checks for incremental updates,
downloads new candles, runs quality checks, and generates features.
Integrated into the FastAPI lifespan.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from app.logs.logger import get_logger
from app.market_intelligence.config import data_config
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class DataSyncService:
    """
    Background service that orchestrates periodic data synchronization:
    1. Incremental candle downloads for all configured symbols
    2. Quality validation
    3. Feature generation
    """

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_sync: datetime | None = None
        self._next_sync: datetime | None = None
        self._sync_interval = data_config.sync_interval_minutes * 60  # seconds

    async def start(self):
        """Start the background sync loop."""
        if self._running:
            logger.warning("DataSyncService already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info(
            f"DataSyncService started — sync every {data_config.sync_interval_minutes} minutes"
        )

    async def stop(self):
        """Gracefully stop the sync loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DataSyncService stopped")

    def get_status(self) -> dict:
        """Return current sync service status."""
        return {
            "running": self._running,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "next_sync": self._next_sync.isoformat() if self._next_sync else None,
            "interval_minutes": data_config.sync_interval_minutes,
        }

    @property
    def active_symbols(self) -> list[str]:
        """List of active symbols for other engines."""
        return [s["symbol"] for s in data_config.get_all_symbols_flat()]

    async def sync_all(self):
        """Manually trigger a full sync cycle."""
        await self._run_sync_cycle()

    async def _sync_loop(self):
        """Main background loop."""
        # Initial delay to let the app boot
        await asyncio.sleep(10)

        while self._running:
            try:
                self._next_sync = datetime.now(timezone.utc) + timedelta(
                    seconds=self._sync_interval
                )
                await self._run_sync_cycle()
                self._last_sync = datetime.now(timezone.utc)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync cycle error: {e}")

            # Wait for next cycle
            try:
                await asyncio.sleep(self._sync_interval)
            except asyncio.CancelledError:
                break

    async def _run_sync_cycle(self):
        """Execute one full sync cycle across all configured symbols."""
        logger.info("Starting data sync cycle...")

        try:
            await event_bus.publish("DataSyncProgress", payload={
                "status": "started",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

        from app.market_intelligence.downloader import historical_downloader
        from app.market_intelligence.features import feature_store
        from app.market_intelligence.quality import data_quality_engine

        all_symbols = data_config.get_all_symbols_flat()
        total = 0
        completed = 0
        errors = 0

        for sym_info in all_symbols:
            symbol = sym_info["symbol"]
            asset_class = sym_info["asset_class"]
            timeframes = data_config.timeframes.get(asset_class, ["D1"])

            for tf in timeframes:
                if not self._running:
                    return

                total += 1
                try:
                    # 1. Incremental download
                    result = await historical_downloader.download_incremental(
                        symbol, tf, asset_class
                    )

                    if result.get("status") in ("completed", "no_data"):
                        # 2. Quality check
                        await data_quality_engine.validate(symbol, tf)

                        # 3. Feature generation (only if we downloaded new data)
                        if result.get("downloaded", 0) > 0:
                            await feature_store.generate_features(symbol, tf)

                        completed += 1
                    else:
                        errors += 1
                        logger.warning(
                            f"Sync failed for {symbol} {tf}: {result.get('errors', [])}"
                        )

                except Exception as e:
                    errors += 1
                    logger.error(f"Sync error for {symbol} {tf}: {e}")

                # Rate limiting between downloads
                await asyncio.sleep(1)

        summary = {
            "status": "completed",
            "total_tasks": total,
            "completed": completed,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            await event_bus.publish("DataSyncComplete", payload=summary)
        except Exception:
            pass

        logger.info(
            f"Sync cycle complete: {completed}/{total} successful, {errors} errors"
        )

    async def ensure_symbols_registered(self):
        """
        Ensure all configured symbols exist in the database.
        Creates SymbolModel records for any missing symbols.
        """
        from sqlalchemy import select

        from app.database.manager import db_manager
        from app.database.models.market import SymbolModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return

        all_symbols = data_config.get_all_symbols_flat()

        async with session_factory() as session:
            try:
                for sym_info in all_symbols:
                    existing = await session.execute(
                        select(SymbolModel).where(SymbolModel.symbol == sym_info["symbol"])
                    )
                    if existing.scalar() is None:
                        session.add(SymbolModel(
                            symbol=sym_info["symbol"],
                            asset_class=sym_info["asset_class"],
                            base_currency=sym_info.get("base", ""),
                            quote_currency=sym_info.get("quote", ""),
                            exchange="default",
                            pip_size=float(sym_info.get("pip_size", 0.0001)),
                            data_provider=data_config.provider,
                            is_active=True,
                        ))
                await session.commit()
                logger.info(f"Symbol registry: {len(all_symbols)} symbols ensured")
            except Exception as e:
                await session.rollback()
                logger.warning(f"Ensure symbols error: {e}")


# Singleton
data_sync_service = DataSyncService()
