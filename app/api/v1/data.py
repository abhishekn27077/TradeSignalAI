"""
Market Intelligence Data API
===============================
REST endpoints for managing historical data downloads, quality reports,
feature store, and database statistics.
"""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


# ── Provider Endpoints ───────────────────────────────────────────────────────

@router.get("/providers", summary="List Available Data Providers")
async def list_providers():
    """List all available data providers."""
    from app.market_intelligence.providers.yfinance_adapter import yfinance_adapter
    providers = []
    if yfinance_adapter.is_available():
        providers.append({
            "name": "yfinance",
            "status": "available",
            "description": "Yahoo Finance — free, no API key required",
        })
    else:
        providers.append({
            "name": "yfinance",
            "status": "unavailable",
            "description": "yfinance package not installed",
        })
    return {"success": True, "providers": providers}


# ── Symbol Management ────────────────────────────────────────────────────────

@router.get("/symbols", summary="List Configured Symbols")
async def list_symbols():
    """List all configured symbols with metadata."""
    from sqlalchemy import select

    from app.database.manager import db_manager
    from app.database.models.market import SymbolModel

    session_factory = db_manager.get_session()
    if not session_factory:
        return {"success": True, "symbols": []}

    async with session_factory() as session:
        try:
            result = await session.execute(select(SymbolModel).order_by(SymbolModel.asset_class, SymbolModel.symbol))
            rows = result.scalars().all()
            symbols = [
                {
                    "symbol": r.symbol, "asset_class": r.asset_class,
                    "base_currency": r.base_currency, "quote_currency": r.quote_currency,
                    "exchange": r.exchange, "description": r.description,
                    "pip_size": r.pip_size, "data_provider": r.data_provider,
                    "is_active": r.is_active,
                    "last_synced": r.last_synced.isoformat() if r.last_synced else None,
                }
                for r in rows
            ]
            return {"success": True, "symbols": symbols}
        except Exception as e:
            logger.warning(f"List symbols error: {e}")
            return {"success": True, "symbols": []}


@router.post("/symbols", summary="Add a New Symbol")
async def add_symbol(payload: dict[str, Any]):
    """Add a new symbol to track."""
    from sqlalchemy import select

    from app.database.manager import db_manager
    from app.database.models.market import SymbolModel

    symbol = payload.get("symbol", "").upper()
    asset_class = payload.get("asset_class", "forex")

    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")

    session_factory = db_manager.get_session()
    if not session_factory:
        raise HTTPException(status_code=500, detail="Database unavailable")

    async with session_factory() as session:
        existing = await session.execute(select(SymbolModel).where(SymbolModel.symbol == symbol))
        if existing.scalar() is not None:
            raise HTTPException(status_code=409, detail=f"Symbol {symbol} already exists")

        session.add(SymbolModel(
            symbol=symbol,
            asset_class=asset_class,
            base_currency=payload.get("base_currency", ""),
            quote_currency=payload.get("quote_currency", ""),
            exchange=payload.get("exchange", "default"),
            description=payload.get("description"),
            pip_size=payload.get("pip_size", 0.0001),
            data_provider=payload.get("data_provider", "yfinance"),
            is_active=True,
        ))
        await session.commit()

    return {"success": True, "message": f"Symbol {symbol} added", "symbol": symbol}


@router.delete("/symbols/{symbol}", summary="Remove a Symbol")
async def remove_symbol(symbol: str):
    """Remove a symbol and optionally its historical data."""
    from sqlalchemy import delete

    from app.database.manager import db_manager
    from app.database.models.market import SymbolModel

    session_factory = db_manager.get_session()
    if not session_factory:
        raise HTTPException(status_code=500, detail="Database unavailable")

    async with session_factory() as session:
        result = await session.execute(delete(SymbolModel).where(SymbolModel.symbol == symbol.upper()))
        await session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    return {"success": True, "message": f"Symbol {symbol} removed"}


# ── Download Endpoints ───────────────────────────────────────────────────────

@router.post("/download", summary="Start Download Job")
async def start_download(payload: dict[str, Any], background_tasks: BackgroundTasks):
    """Start downloading historical data for a symbol/timeframe."""
    from app.market_intelligence.downloader import historical_downloader

    symbol = payload.get("symbol", "").upper()
    timeframe = payload.get("timeframe", "H1")
    asset_class = payload.get("asset_class", "forex")

    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")

    from app.market_intelligence.config import VALID_TIMEFRAMES
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Valid: {VALID_TIMEFRAMES}")

    background_tasks.add_task(
        historical_downloader.download_symbol, symbol, timeframe, asset_class
    )

    return {
        "success": True,
        "message": f"Download started for {symbol} {timeframe}",
        "symbol": symbol, "timeframe": timeframe,
    }


@router.post("/download/all", summary="Start Download for All Configured Symbols")
async def start_download_all(background_tasks: BackgroundTasks):
    """Start downloading historical data for all configured symbols."""
    from app.market_intelligence.config import data_config
    from app.market_intelligence.downloader import historical_downloader

    all_symbols = data_config.get_all_symbols_flat()
    tasks_started = 0

    for sym_info in all_symbols:
        symbol = sym_info["symbol"]
        asset_class = sym_info["asset_class"]
        timeframes = data_config.timeframes.get(asset_class, ["D1"])

        for tf in timeframes:
            background_tasks.add_task(
                historical_downloader.download_symbol, symbol, tf, asset_class
            )
            tasks_started += 1

    return {
        "success": True,
        "message": f"Download started for {tasks_started} symbol/timeframe combinations",
        "tasks_started": tasks_started,
    }


# ── Status & Statistics ──────────────────────────────────────────────────────

@router.get("/status", summary="Current Sync Status")
async def get_status():
    """Get current sync status and active download jobs."""
    from app.market_intelligence.downloader import historical_downloader
    from app.market_intelligence.sync_service import data_sync_service

    return {
        "success": True,
        "sync_service": data_sync_service.get_status(),
        "active_jobs": historical_downloader.get_active_jobs(),
    }


@router.get("/database", summary="Database Statistics")
async def get_database_stats():
    """Get database statistics — total symbols, candles, size, coverage."""
    from sqlalchemy import func, select

    from app.database.manager import db_manager
    from app.database.models.market import CandleModel, SymbolModel

    session_factory = db_manager.get_session()
    if not session_factory:
        return {"success": True, "stats": {}}

    async with session_factory() as session:
        try:
            # Count symbols
            sym_count = await session.execute(select(func.count(SymbolModel.symbol)))
            total_symbols = sym_count.scalar() or 0

            # Count candles
            candle_count = await session.execute(select(func.count(CandleModel.id)))
            total_candles = candle_count.scalar() or 0

            # Count by asset class
            asset_counts = await session.execute(
                select(SymbolModel.asset_class, func.count(SymbolModel.symbol))
                .group_by(SymbolModel.asset_class)
            )
            by_asset = {r[0]: r[1] for r in asset_counts}

            # Count candles per symbol
            per_symbol = await session.execute(
                select(
                    CandleModel.symbol, CandleModel.timeframe,
                    func.count(CandleModel.id).label("count"),
                    func.min(CandleModel.timestamp).label("earliest"),
                    func.max(CandleModel.timestamp).label("latest"),
                ).group_by(CandleModel.symbol, CandleModel.timeframe)
            )
            datasets = [
                {
                    "symbol": r.symbol, "timeframe": r.timeframe,
                    "candle_count": r.count,
                    "earliest": r.earliest.isoformat() if r.earliest else None,
                    "latest": r.latest.isoformat() if r.latest else None,
                }
                for r in per_symbol
            ]

            return {
                "success": True,
                "stats": {
                    "total_symbols": total_symbols,
                    "total_candles": total_candles,
                    "symbols_by_asset_class": by_asset,
                    "datasets": datasets,
                    "providers": ["yfinance"],
                },
            }
        except Exception as e:
            logger.warning(f"Database stats error: {e}")
            return {"success": True, "stats": {"error": str(e)}}


# ── Quality Endpoints ────────────────────────────────────────────────────────

@router.get("/quality", summary="All Quality Reports")
async def get_quality_reports():
    """Get quality reports for all datasets."""
    from app.market_intelligence.quality import data_quality_engine
    reports = await data_quality_engine.get_all_reports()
    return {"success": True, "reports": reports}


@router.get("/quality/{symbol}/{timeframe}", summary="Quality Report for Dataset")
async def get_quality_report(symbol: str, timeframe: str):
    """Run quality check and return report for a specific symbol/timeframe."""
    from app.market_intelligence.quality import data_quality_engine
    report = await data_quality_engine.validate(symbol.upper(), timeframe)
    return {"success": True, "report": report}


# ── Feature Store Endpoints ──────────────────────────────────────────────────

@router.get("/features/{symbol}/{timeframe}", summary="Get Features")
async def get_features(symbol: str, timeframe: str, limit: int = 100, offset: int = 0):
    """Get candles with computed features."""
    from app.market_intelligence.features import feature_store
    data = await feature_store.get_features(symbol.upper(), timeframe, limit, offset)
    return {"success": True, "data": data, "count": len(data)}


@router.post("/features/generate", summary="Generate Features")
async def generate_features(payload: dict[str, Any], background_tasks: BackgroundTasks):
    """Trigger feature generation for a symbol/timeframe."""
    from app.market_intelligence.features import feature_store

    symbol = payload.get("symbol", "").upper()
    timeframe = payload.get("timeframe", "H1")

    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")

    background_tasks.add_task(feature_store.generate_features, symbol, timeframe)

    return {
        "success": True,
        "message": f"Feature generation started for {symbol} {timeframe}",
    }


@router.get("/features/coverage", summary="Feature Coverage")
async def get_feature_coverage():
    """Get feature coverage stats across all datasets."""
    from app.market_intelligence.features import feature_store
    coverage = await feature_store.get_coverage()
    return {"success": True, "coverage": coverage}


# ── History Endpoint ─────────────────────────────────────────────────────────

@router.get("/history/{symbol}/{timeframe}", summary="Get Raw OHLCV Candles")
async def get_history(symbol: str, timeframe: str, limit: int = 500, offset: int = 0):
    """Get raw historical OHLCV candles."""
    from sqlalchemy import desc, select

    from app.database.manager import db_manager
    from app.database.models.market import CandleModel

    session_factory = db_manager.get_session()
    if not session_factory:
        return {"success": True, "candles": []}

    async with session_factory() as session:
        try:
            result = await session.execute(
                select(CandleModel)
                .where(CandleModel.symbol == symbol.upper(), CandleModel.timeframe == timeframe)
                .order_by(desc(CandleModel.timestamp))
                .limit(limit).offset(offset)
            )
            rows = result.scalars().all()
            candles = [
                {
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "open": r.open, "high": r.high, "low": r.low,
                    "close": r.close, "volume": r.volume,
                    "spread": r.spread, "session": r.session,
                }
                for r in reversed(rows)
            ]
            return {"success": True, "candles": candles, "count": len(candles)}
        except Exception as e:
            logger.warning(f"Get history error: {e}")
            return {"success": True, "candles": []}


# ── Repair Endpoint ──────────────────────────────────────────────────────────

@router.post("/repair/{symbol}/{timeframe}", summary="Trigger Gap Repair")
async def repair_gaps(symbol: str, timeframe: str, background_tasks: BackgroundTasks):
    """Detect and repair gaps in stored candle data."""
    from app.market_intelligence.downloader import historical_downloader

    background_tasks.add_task(
        historical_downloader.repair_gaps, symbol.upper(), timeframe
    )

    return {
        "success": True,
        "message": f"Gap repair started for {symbol} {timeframe}",
    }
