"""
Historical Data Downloader
=============================
Enterprise-grade downloader with incremental sync, gap detection/repair,
duplicate removal, retry logic, rate limiting, and progress tracking.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.logs.logger import get_logger
from app.market_intelligence.config import data_config, get_session_for_hour
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class HistoricalDownloader:
    """
    Manages downloading, incremental sync, gap repair, and deduplication
    of historical OHLCV data.
    """

    def __init__(self):
        self._adapter = None
        self._semaphore = asyncio.Semaphore(data_config.max_concurrent_downloads)
        self._active_jobs: dict[str, str] = {}  # "SYMBOL:TF" -> status

    def _get_adapter(self):
        """Lazy-load the data provider adapter."""
        if self._adapter is None:
            from app.market_intelligence.providers.yfinance_adapter import (
                yfinance_adapter,
            )
            self._adapter = yfinance_adapter
        return self._adapter

    async def download_symbol(
        self,
        symbol: str,
        timeframe: str,
        asset_class: str = "forex",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Download historical data for a single symbol/timeframe.
        Creates a sync job record and tracks progress.
        """
        job_key = f"{symbol}:{timeframe}"

        if job_key in self._active_jobs and self._active_jobs[job_key] == "running":
            return {"status": "already_running", "symbol": symbol, "timeframe": timeframe}

        self._active_jobs[job_key] = "running"
        adapter = self._get_adapter()
        result = {
            "symbol": symbol, "timeframe": timeframe, "status": "pending",
            "downloaded": 0, "duplicates_removed": 0, "errors": [],
        }

        # Create sync job record
        job_id = await self._create_sync_job(symbol, timeframe)

        try:
            async with self._semaphore:
                await self._publish_progress(symbol, timeframe, 0, "downloading")

                # Determine date range
                if start_date is None:
                    history_days = data_config.get_history_days(asset_class, timeframe)
                    start_date = datetime.now(timezone.utc) - timedelta(days=history_days)

                if end_date is None:
                    end_date = datetime.now(timezone.utc)

                # Check last stored candle for incremental mode
                last_ts = await self._get_last_timestamp(symbol, timeframe)
                if last_ts and last_ts > start_date:
                    start_date = last_ts + timedelta(minutes=1)
                    logger.info(f"Incremental mode: {symbol} {timeframe} from {start_date}")

                # Fetch from adapter with retry
                candles = await self._fetch_with_retry(
                    adapter, symbol, timeframe, start_date, end_date
                )

                if not candles:
                    result["status"] = "no_data"
                    self._active_jobs[job_key] = "completed"
                    await self._update_sync_job(job_id, "completed", 100, 0, 0)
                    await self._publish_progress(symbol, timeframe, 100, "completed")
                    return result

                await self._publish_progress(symbol, timeframe, 30, "storing")

                # Enrich with session and store
                for candle in candles:
                    ts = candle["timestamp"]
                    candle["session"] = get_session_for_hour(ts.hour)
                    candle["provider"] = adapter.name

                # Batch insert
                inserted = await self._batch_insert_candles(symbol, timeframe, candles)
                result["downloaded"] = inserted

                await self._publish_progress(symbol, timeframe, 70, "deduplicating")

                # Remove duplicates
                dups = await self.remove_duplicates(symbol, timeframe)
                result["duplicates_removed"] = dups

                await self._publish_progress(symbol, timeframe, 90, "finalizing")

                # Update symbol last_synced
                await self._update_symbol_sync(symbol)

                result["status"] = "completed"
                await self._update_sync_job(job_id, "completed", 100, len(candles), inserted)
                await self._publish_progress(symbol, timeframe, 100, "completed")

                logger.info(
                    f"Download complete: {symbol} {timeframe} — "
                    f"{inserted} candles stored, {dups} duplicates removed"
                )

        except Exception as e:
            error_msg = str(e)
            result["status"] = "failed"
            result["errors"].append(error_msg)
            logger.error(f"Download failed for {symbol} {timeframe}: {e}")
            await self._update_sync_job(job_id, "failed", 0, 0, 0, error_msg)
            await self._publish_progress(symbol, timeframe, 0, "failed", error_msg)

        finally:
            self._active_jobs[job_key] = result["status"]

        return result

    async def download_incremental(self, symbol: str, timeframe: str, asset_class: str = "forex"):
        """Download only candles after the last stored timestamp."""
        return await self.download_symbol(symbol, timeframe, asset_class)

    async def detect_gaps(self, symbol: str, timeframe: str) -> list[dict[str, Any]]:
        """Find missing candle windows in stored data."""
        from app.market_intelligence.config import TIMEFRAME_MINUTES

        interval_minutes = TIMEFRAME_MINUTES.get(timeframe, 60)
        candles = await self._get_timestamps(symbol, timeframe)

        if len(candles) < 2:
            return []

        gaps = []
        for i in range(1, len(candles)):
            expected_gap = timedelta(minutes=interval_minutes)
            actual_gap = candles[i] - candles[i - 1]

            # Allow some tolerance (2x expected gap for weekends/holidays on daily)
            max_gap = expected_gap * (3 if timeframe in ("D1", "W1") else 2)

            if actual_gap > max_gap:
                gaps.append({
                    "start": candles[i - 1],
                    "end": candles[i],
                    "missing_candles": int(actual_gap / expected_gap) - 1,
                })

        return gaps

    async def repair_gaps(self, symbol: str, timeframe: str, asset_class: str = "forex") -> int:
        """Download and insert missing candles for detected gaps."""
        gaps = await self.detect_gaps(symbol, timeframe)
        if not gaps:
            return 0

        adapter = self._get_adapter()
        total_repaired = 0

        for gap in gaps:
            candles = await self._fetch_with_retry(
                adapter, symbol, timeframe, gap["start"], gap["end"]
            )
            if candles:
                for c in candles:
                    c["session"] = get_session_for_hour(c["timestamp"].hour)
                    c["provider"] = adapter.name
                inserted = await self._batch_insert_candles(symbol, timeframe, candles)
                total_repaired += inserted

        if total_repaired > 0:
            logger.info(f"Gap repair: {symbol} {timeframe} — {total_repaired} candles filled")

        return total_repaired

    async def remove_duplicates(self, symbol: str, timeframe: str) -> int:
        """Remove duplicate candle records, keeping the latest."""
        from sqlalchemy import text

        from app.database.manager import db_manager

        session_factory = db_manager.get_session()
        if not session_factory:
            return 0

        async with session_factory() as session:
            try:
                # Delete duplicates keeping lowest ID per unique combo
                result = await session.execute(text("""
                    DELETE FROM historical_candles
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM historical_candles
                        WHERE symbol = :symbol AND timeframe = :timeframe
                        GROUP BY symbol, timeframe, timestamp, provider
                    ) AND symbol = :symbol AND timeframe = :timeframe
                """), {"symbol": symbol, "timeframe": timeframe})
                await session.commit()
                count = result.rowcount
                if count > 0:
                    logger.info(f"Removed {count} duplicate candles for {symbol} {timeframe}")
                return count
            except Exception as e:
                await session.rollback()
                logger.warning(f"Deduplicate error for {symbol} {timeframe}: {e}")
                return 0

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _fetch_with_retry(self, adapter, symbol, timeframe, start, end, retries=None):
        """Fetch with exponential backoff retry."""
        if retries is None:
            retries = data_config.retry_limit

        for attempt in range(retries):
            try:
                candles = await adapter.fetch_candles(symbol, timeframe, start, end)
                return candles
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(
                    f"Fetch attempt {attempt + 1}/{retries} failed for {symbol} {timeframe}: {e}. "
                    f"Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)

        logger.error(f"All {retries} fetch attempts failed for {symbol} {timeframe}")
        return []

    async def _batch_insert_candles(self, symbol: str, timeframe: str, candles: list[dict]) -> int:
        """Batch insert candles, skipping duplicates."""
        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return 0

        inserted = 0
        batch_size = 500

        async with session_factory() as session:
            try:
                for i in range(0, len(candles), batch_size):
                    batch = candles[i:i + batch_size]
                    for candle in batch:
                        # Check for existing (simple approach for SQLite compat)
                        from sqlalchemy import select
                        existing = await session.execute(
                            select(CandleModel.id).where(
                                CandleModel.symbol == symbol,
                                CandleModel.timeframe == timeframe,
                                CandleModel.timestamp == candle["timestamp"],
                                CandleModel.provider == candle.get("provider", "yfinance"),
                            )
                        )
                        if existing.scalar() is not None:
                            continue

                        session.add(CandleModel(
                            symbol=symbol,
                            timeframe=timeframe,
                            timestamp=candle["timestamp"],
                            open=candle["open"],
                            high=candle["high"],
                            low=candle["low"],
                            close=candle["close"],
                            volume=candle.get("volume", 0),
                            spread=candle.get("spread"),
                            session=candle.get("session"),
                            provider=candle.get("provider", "yfinance"),
                            timezone="UTC",
                        ))
                        inserted += 1

                    await session.commit()

                return inserted
            except Exception as e:
                await session.rollback()
                logger.error(f"Batch insert error for {symbol} {timeframe}: {e}")
                return inserted

    async def _get_last_timestamp(self, symbol: str, timeframe: str) -> datetime | None:
        """Get the most recent candle timestamp for incremental downloads."""
        from sqlalchemy import desc, select

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return None

        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(CandleModel.timestamp)
                    .where(CandleModel.symbol == symbol, CandleModel.timeframe == timeframe)
                    .order_by(desc(CandleModel.timestamp))
                    .limit(1)
                )
                row = result.scalar()
                return row
            except Exception:
                return None

    async def _get_timestamps(self, symbol: str, timeframe: str) -> list[datetime]:
        """Get all stored timestamps for gap detection."""
        from sqlalchemy import select

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return []

        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(CandleModel.timestamp)
                    .where(CandleModel.symbol == symbol, CandleModel.timeframe == timeframe)
                    .order_by(CandleModel.timestamp)
                )
                return [row[0] for row in result.fetchall()]
            except Exception:
                return []

    async def _create_sync_job(self, symbol: str, timeframe: str) -> int:
        """Create a data sync job record."""
        from app.database.manager import db_manager
        from app.database.models.market import DataSyncJobModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return 0

        async with session_factory() as session:
            try:
                job = DataSyncJobModel(
                    symbol=symbol, timeframe=timeframe,
                    provider=data_config.provider,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                )
                session.add(job)
                await session.commit()
                await session.refresh(job)
                return job.id
            except Exception as e:
                await session.rollback()
                logger.warning(f"Create sync job error: {e}")
                return 0

    async def _update_sync_job(self, job_id: int, status: str, progress: float,
                               total: int, downloaded: int, error: str = None):
        """Update sync job record."""
        from sqlalchemy import update

        from app.database.manager import db_manager
        from app.database.models.market import DataSyncJobModel

        session_factory = db_manager.get_session()
        if not session_factory or job_id == 0:
            return

        async with session_factory() as session:
            try:
                values = {
                    "status": status, "progress": progress,
                    "total_candles": total, "downloaded_candles": downloaded,
                }
                if status in ("completed", "failed"):
                    values["completed_at"] = datetime.now(timezone.utc)
                if error:
                    values["error_message"] = error

                await session.execute(
                    update(DataSyncJobModel).where(DataSyncJobModel.id == job_id).values(**values)
                )
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.warning(f"Update sync job error: {e}")

    async def _update_symbol_sync(self, symbol: str):
        """Update symbol's last_synced timestamp."""
        from sqlalchemy import update

        from app.database.manager import db_manager
        from app.database.models.market import SymbolModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return

        async with session_factory() as session:
            try:
                await session.execute(
                    update(SymbolModel)
                    .where(SymbolModel.symbol == symbol)
                    .values(last_synced=datetime.now(timezone.utc))
                )
                await session.commit()
            except Exception:
                await session.rollback()

    async def _publish_progress(self, symbol: str, timeframe: str,
                                progress: float, status: str, error: str = None):
        """Publish download progress via EventBus."""
        try:
            await event_bus.publish("DataDownloadProgress", payload={
                "symbol": symbol, "timeframe": timeframe,
                "progress": progress, "status": status, "error": error,
            })
        except Exception:
            pass

    def get_active_jobs(self) -> dict[str, str]:
        """Return currently active download jobs."""
        return dict(self._active_jobs)


# Singleton
historical_downloader = HistoricalDownloader()
