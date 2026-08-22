"""
Data Quality Engine
=====================
Automatic validation, scoring, and repair of historical candle data.
Detects missing candles, duplicates, invalid timestamps, negative prices,
out-of-order records, and corrupt data.
"""

from typing import Any

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class DataQualityEngine:
    """
    Validates and repairs stored candle data.
    Generates quality scores (0-100) per symbol/timeframe.
    """

    async def validate(self, symbol: str, timeframe: str) -> dict[str, Any]:
        """
        Run all quality checks on a symbol/timeframe dataset.
        Returns a quality report dict.
        """
        candles = await self._load_candles(symbol, timeframe)

        report = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_candles": len(candles),
            "missing_count": 0,
            "duplicate_count": 0,
            "invalid_count": 0,
            "negative_price_count": 0,
            "out_of_order_count": 0,
            "quality_score": 100.0,
            "issues": [],
        }

        if not candles:
            report["quality_score"] = 0.0
            report["issues"].append("No candles found")
            return report

        # Check duplicates
        seen = set()
        dups = 0
        for c in candles:
            key = (c["timestamp"], c["provider"])
            if key in seen:
                dups += 1
            seen.add(key)
        report["duplicate_count"] = dups
        if dups > 0:
            report["issues"].append(f"{dups} duplicate candles detected")

        # Check negative prices
        neg = 0
        for c in candles:
            if c["open"] <= 0 or c["high"] <= 0 or c["low"] <= 0 or c["close"] <= 0:
                neg += 1
        report["negative_price_count"] = neg
        if neg > 0:
            report["issues"].append(f"{neg} candles with negative/zero prices")

        # Check out-of-order timestamps
        ooo = 0
        for i in range(1, len(candles)):
            if candles[i]["timestamp"] <= candles[i - 1]["timestamp"]:
                ooo += 1
        report["out_of_order_count"] = ooo
        if ooo > 0:
            report["issues"].append(f"{ooo} out-of-order timestamps")

        # Check invalid data (high < low, etc.)
        invalid = 0
        for c in candles:
            if c["high"] < c["low"] or c["high"] < c["open"] or c["high"] < c["close"] or c["low"] > c["open"] or c["low"] > c["close"]:
                invalid += 1
        report["invalid_count"] = invalid
        if invalid > 0:
            report["issues"].append(f"{invalid} candles with invalid OHLC relationships")

        # Check for gaps (missing candles)
        from datetime import timedelta

        from app.market_intelligence.config import TIMEFRAME_MINUTES

        interval = TIMEFRAME_MINUTES.get(timeframe, 60)
        missing = 0
        for i in range(1, len(candles)):
            expected_gap = timedelta(minutes=interval)
            actual_gap = candles[i]["timestamp"] - candles[i - 1]["timestamp"]

            # Allow larger gaps for daily/weekly (weekends)
            max_gap = expected_gap * (4 if timeframe in ("D1", "W1") else 2)
            if actual_gap > max_gap:
                gap_count = int(actual_gap / expected_gap) - 1
                missing += gap_count

        report["missing_count"] = missing
        if missing > 0:
            report["issues"].append(f"~{missing} missing candles (gaps detected)")

        # Calculate quality score
        total = len(candles)
        penalty = 0
        penalty += (dups / max(total, 1)) * 20
        penalty += (neg / max(total, 1)) * 25
        penalty += (ooo / max(total, 1)) * 15
        penalty += (invalid / max(total, 1)) * 20
        penalty += min((missing / max(total, 1)) * 20, 20)

        report["quality_score"] = round(max(0, 100 - penalty), 2)

        # Persist report
        await self._save_report(report)

        # Publish event
        try:
            await event_bus.publish("DataQualityUpdate", payload=report)
        except Exception:
            pass

        return report

    async def auto_repair(self, symbol: str, timeframe: str) -> dict[str, Any]:
        """
        Attempt automatic repair of detected issues:
        - Remove duplicates
        - Remove negative-price candles
        - Sort out-of-order records (by re-querying sorted)
        """
        repairs = {"duplicates_removed": 0, "invalid_removed": 0, "reordered": False}

        from app.market_intelligence.downloader import historical_downloader

        # Remove duplicates
        dups = await historical_downloader.remove_duplicates(symbol, timeframe)
        repairs["duplicates_removed"] = dups

        # Remove negative-price candles
        removed = await self._remove_invalid_candles(symbol, timeframe)
        repairs["invalid_removed"] = removed

        if dups > 0 or removed > 0:
            logger.info(
                f"Auto-repair {symbol} {timeframe}: "
                f"{dups} dups removed, {removed} invalid removed"
            )

        return repairs

    async def get_all_reports(self) -> list[dict[str, Any]]:
        """Get the latest quality report for each symbol/timeframe combo."""
        from sqlalchemy import desc, select

        from app.database.manager import db_manager
        from app.database.models.market import DataQualityReportModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return []

        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(DataQualityReportModel).order_by(desc(DataQualityReportModel.scanned_at))
                )
                rows = result.scalars().all()
                reports = []
                seen = set()
                for r in rows:
                    key = f"{r.symbol}:{r.timeframe}"
                    if key not in seen:
                        seen.add(key)
                        reports.append({
                            "symbol": r.symbol, "timeframe": r.timeframe,
                            "total_candles": r.total_candles,
                            "missing_count": r.missing_count,
                            "duplicate_count": r.duplicate_count,
                            "invalid_count": r.invalid_count,
                            "quality_score": r.quality_score,
                            "scanned_at": r.scanned_at.isoformat() if r.scanned_at else None,
                        })
                return reports
            except Exception as e:
                logger.warning(f"Get quality reports error: {e}")
                return []

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _load_candles(self, symbol: str, timeframe: str) -> list[dict]:
        """Load all candles for a symbol/timeframe, ordered by timestamp."""
        from sqlalchemy import select

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return []

        async with session_factory() as session:
            try:
                result = await session.execute(
                    select(CandleModel)
                    .where(CandleModel.symbol == symbol, CandleModel.timeframe == timeframe)
                    .order_by(CandleModel.timestamp)
                )
                rows = result.scalars().all()
                return [
                    {
                        "id": r.id, "timestamp": r.timestamp,
                        "open": r.open, "high": r.high, "low": r.low,
                        "close": r.close, "volume": r.volume,
                        "provider": r.provider or "yfinance",
                    }
                    for r in rows
                ]
            except Exception as e:
                logger.warning(f"Load candles error: {e}")
                return []

    async def _save_report(self, report: dict[str, Any]):
        """Persist quality report to database."""
        from app.database.manager import db_manager
        from app.database.models.market import DataQualityReportModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return

        async with session_factory() as session:
            try:
                record = DataQualityReportModel(
                    symbol=report["symbol"],
                    timeframe=report["timeframe"],
                    total_candles=report["total_candles"],
                    missing_count=report["missing_count"],
                    duplicate_count=report["duplicate_count"],
                    invalid_count=report["invalid_count"],
                    negative_price_count=report.get("negative_price_count", 0),
                    out_of_order_count=report.get("out_of_order_count", 0),
                    quality_score=report["quality_score"],
                    details_json={"issues": report.get("issues", [])},
                )
                session.add(record)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.warning(f"Save quality report error: {e}")

    async def _remove_invalid_candles(self, symbol: str, timeframe: str) -> int:
        """Remove candles with negative/zero prices."""
        from sqlalchemy import delete, or_

        from app.database.manager import db_manager
        from app.database.models.market import CandleModel

        session_factory = db_manager.get_session()
        if not session_factory:
            return 0

        async with session_factory() as session:
            try:
                result = await session.execute(
                    delete(CandleModel).where(
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == timeframe,
                        or_(
                            CandleModel.open <= 0,
                            CandleModel.high <= 0,
                            CandleModel.low <= 0,
                            CandleModel.close <= 0,
                        )
                    )
                )
                await session.commit()
                return result.rowcount
            except Exception as e:
                await session.rollback()
                logger.warning(f"Remove invalid candles error: {e}")
                return 0


# Singleton
data_quality_engine = DataQualityEngine()
