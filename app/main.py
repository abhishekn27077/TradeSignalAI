from contextlib import asynccontextmanager

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub.*")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.middleware import (
    CorrelationIdMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    global_exception_handler,
)
from app.api.router import main_api_router
from app.config.settings import get_settings
from app.logs.logger import get_logger, setup_logging
from app.utils.provider_manager import ProviderInstance, provider_manager

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} in {settings.ENVIRONMENT} mode "
        f"(Execution Mode: {settings.EXECUTION_MODE})."
    )

    from app.database.manager import db_manager
    db_manager.connect()
    await db_manager.init_db()

    from app.utils.startup_validator import startup_validator
    results = await startup_validator.validate_all()

    db_provider = ProviderInstance(
        name="database",
        health_check_fn=lambda: db_manager._engine is not None,
        heartbeat_interval=30.0,
        max_retries=5,
    )
    provider_manager.register("database", db_provider)

    from app.market_data.providers.manager import market_provider_manager
    provider_manager.register("market", ProviderInstance(
        name="market",
        health_check_fn=lambda: len(market_provider_manager.available_providers) > 0,
        heartbeat_interval=60.0,
    ))
    provider_manager.register("tradingview", ProviderInstance(
        name="tradingview",
        health_check_fn=lambda: "tradingview" in market_provider_manager.available_providers,
        heartbeat_interval=60.0,
    ))

    from app.agents.providers.router import model_router
    provider_manager.register("openrouter", ProviderInstance(
        name="openrouter",
        health_check_fn=model_router.health_check_all,
        heartbeat_interval=60.0,
    ))
    provider_manager.register("openai", ProviderInstance(
        name="openai",
        health_check_fn=model_router.health_check_all,
        heartbeat_interval=60.0,
    ))

    provider_manager.register("ai", ProviderInstance(
        name="ai",
        health_check_fn=lambda: True,
        heartbeat_interval=60.0,
    ))

    provider_manager.register("news", ProviderInstance(name="news", health_check_fn=lambda: True, heartbeat_interval=60.0))
    provider_manager.register("memory", ProviderInstance(name="memory", health_check_fn=lambda: True, heartbeat_interval=60.0))
    provider_manager.register("paper", ProviderInstance(name="paper", health_check_fn=lambda: True, heartbeat_interval=60.0))

    import asyncio
    asyncio.ensure_future(provider_manager.initialize_all())
    
    from app.market_data.realtime.stream_manager import stream_manager
    asyncio.create_task(stream_manager.start_polling())
    
    from app.strategies.manager import strategy_manager
    asyncio.create_task(strategy_manager.start())
    
    from app.agents.manager import lifecycle_manager
    lifecycle_manager.start()

    from app.execution.coordinator import coordinator
    from app.journal.manager import journal_manager
    from app.tasks.monitoring import system_monitor
    from app.tasks.validation_tracker import validation_tracker
    try:
        coordinator.start()
        system_monitor.start() if hasattr(system_monitor, "start") else None
        validation_tracker.start()
        journal_manager.start()
    except Exception as e:
        logger.warning(f"Coordinator start warning: {e}")

    # Start Market Intelligence Background Sync
    from app.market_intelligence.sync_service import data_sync_service
    await data_sync_service.ensure_symbols_registered()
    # asyncio.create_task(data_sync_service.start())

    # Initialize Forecast Engine Registry
    from app.forecast_engine.registry.manager import model_registry
    await model_registry.ensure_default_providers()
    await model_registry.initialize()

    # Start Market Intelligence Background Services
    from app.forecast_engine.lifecycle import prediction_lifecycle_manager
    from app.market_intelligence.execution_bridge import execution_bridge
    from app.market_intelligence.h4_engine import h4_forecast_engine
    from app.market_intelligence.schedule_engine import schedule_engine
    from app.market_intelligence.swing_scanner import swing_scanner
    from app.research.self_learning_engine import self_learning_engine
    
    tasks = []
    tasks.append(asyncio.create_task(h4_forecast_engine.start()))
    tasks.append(asyncio.create_task(swing_scanner.start()))
    tasks.append(asyncio.create_task(prediction_lifecycle_manager.start()))
    tasks.append(asyncio.create_task(schedule_engine.start()))
    tasks.append(asyncio.create_task(self_learning_engine.start()))
    execution_bridge.start()

    if settings.EXECUTION_MODE in ("DEMO", "LIVE"):
        from app.brokers.factory import BrokerFactory
        from app.execution.router import smart_router
        try:
            tv_adapter = BrokerFactory.create("TradingView")
            if await tv_adapter.connect():
                smart_router.add_broker("TradingView", tv_adapter)
                logger.info("TradingView Broker registered with SmartOrderRouter.")
            else:
                logger.warning("TradingView broker connect returned False, continuing in degraded mode.")
        except Exception as e:
            logger.warning(f"TradingView Broker registration skipped: {e}")

    import webbrowser
    def launch_tradingview():
        try:
            url = "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSD"
            logger.info(f"Automatically launching TradingView at {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to launch TradingView automatically: {e}")
            
    # Start Phase 45/47/49: Autonomous Live-Shadow Forecast Scheduler & Outcome Worker
    from app.runtime.live_forecast_scheduler import live_forecast_scheduler
    from app.runtime.shadow_outcome_worker import shadow_outcome_worker
    
    # Run Phase 49 stateless startup sequence (Fetch fresh data & Recalculate forecasts)
    from app.runtime.startup_sync import startup_sync
    await startup_sync.execute_startup_sequence()

    tasks.append(asyncio.create_task(live_forecast_scheduler.start()))
    tasks.append(asyncio.create_task(shadow_outcome_worker.start()))

    # Start Phase 8: Portfolio Intelligence Manager
    from app.portfolio_intelligence.manager import portfolio_intelligence_manager
    tasks.append(asyncio.create_task(portfolio_intelligence_manager.start()))
        
    # Wait for tasks to start up but do not block forever
    # We remove await asyncio.gather(*tasks) so that lifespan yields

    import asyncio
    loop = asyncio.get_event_loop()
    # loop.run_in_executor(None, launch_tradingview)

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    await provider_manager.shutdown_all()
    await system_monitor.stop()
    
    from app.market_intelligence.sync_service import data_sync_service
    await data_sync_service.stop()
    
    from app.forecast_engine.lifecycle import prediction_lifecycle_manager
    from app.market_intelligence.h4_engine import h4_forecast_engine
    from app.market_intelligence.schedule_engine import schedule_engine
    from app.market_intelligence.swing_scanner import swing_scanner
    from app.research.self_learning_engine import self_learning_engine
    
    # Shutdown background tasks
    await h4_forecast_engine.stop()
    await swing_scanner.stop()
    await prediction_lifecycle_manager.stop()
    await schedule_engine.stop()
    await self_learning_engine.stop()
    await live_forecast_scheduler.stop()
    await shadow_outcome_worker.stop()
    await portfolio_intelligence_manager.stop()
    
    try:
        await db_manager.disconnect()
    except Exception:
        pass

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Professional AI Trading Platform API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.add_exception_handler(Exception, global_exception_handler)

    # Root Health Check endpoints
    @app.get("/health", tags=["health"])
    async def root_health():
        return {"status": "ok", "message": f"{settings.PROJECT_NAME} v{settings.VERSION} is operational"}

    @app.get("/", tags=["root"])
    async def root():
        return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}

    app.include_router(main_api_router)

    return app

app = create_app()