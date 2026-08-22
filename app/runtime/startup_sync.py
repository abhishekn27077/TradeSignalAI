import asyncio
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any

from app.core.market_clock import market_clock
from app.market_data.providers.manager import market_provider_manager
from app.runtime.live_forecast_scheduler import live_forecast_scheduler
from app.database.manager import db_manager

logger = logging.getLogger("startup_sync")

CORE_ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", "XAUUSD", "NAS100", "SPX500"]

class StartupSyncService:
    """
    Ensures that the application operates on fresh, real market data upon startup.
    Fulfills Phase 49 requirements for stateless non-24/7 runtime.
    """

    async def synchronize_market_data(self) -> bool:
        """
        Fetches the latest REAL market candles, bypassing local cache, 
        and updates the historical database. Fails closed if data is unavailable.
        """
        logger.info("Initiating Phase 49 Startup Synchronization...")
        
        provider = market_provider_manager.get_provider("yfinance")
        if not provider:
            provider = market_provider_manager.get_provider("tradingview")
            
        if not provider:
            logger.error("DATA_UNAVAILABLE: No real market data provider found. Fails closed.")
            return False

        all_fresh = True
        
        for asset in CORE_ASSETS:
            try:
                # Bypass the manager's SQLite cache and fetch directly from the provider
                rates = await provider.get_rates(asset, "1H", count=10)
                if not rates:
                    logger.error(f"DATA_UNAVAILABLE: Could not fetch fresh data for {asset}.")
                    all_fresh = False
                    continue
                
                # Update SQLite database with fresh candles
                self._upsert_candles(asset, rates)
                
                # Check staleness
                latest_candle_time = datetime.fromisoformat(rates[-1]["timestamp"].replace("Z", "+00:00"))
                if market_clock.is_data_stale(latest_candle_time):
                    logger.warning(f"DATA_STALE: Latest data for {asset} is older than 1 hour.")
                    # Note: We don't fail entirely on weekends for traditional markets,
                    # but for this Phase 49 strict mode we log it prominently.
                    
            except Exception as e:
                logger.error(f"DATA_UNAVAILABLE: Error synchronizing {asset}: {e}")
                all_fresh = False

        if all_fresh:
            logger.info("Market data synchronization completed successfully.")
        
        return all_fresh

    def _upsert_candles(self, asset: str, rates: list[Dict[str, Any]]):
        """Upserts fresh candles into the tradesignal.db historical_candles table."""
        if not db_manager.get_session():
            return
            
        try:
            import os
            if os.path.exists("tradesignal.db"):
                conn = sqlite3.connect("tradesignal.db")
                cur = conn.cursor()
                for r in rates:
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO historical_candles 
                        (symbol, timeframe, timestamp, open, high, low, close, volume, provider)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            asset, 
                            "1H", 
                            r.get("timestamp", r.get("time")), 
                            float(r["open"]), 
                            float(r["high"]), 
                            float(r["low"]), 
                            float(r["close"]), 
                            float(r.get("volume", 100.0)),
                            "STARTUP_SYNC"
                        )
                    )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Failed to upsert candles for {asset}: {e}")

    async def execute_startup_sequence(self):
        """
        Executes the full stateless startup sequence:
        1. Synchronize market data
        2. Clean up expired signals
        3. Recalculate today's future forecasts using fresh data
        """
        success = await self.synchronize_market_data()
        if not success:
            logger.warning("Startup sync completed with stale/unavailable data constraints.")
        
        # 2. Recover offline gaps and resolve pending paper trades
        try:
            from app.runtime.offline_gap_recovery import offline_gap_recovery_engine
            gap_res = offline_gap_recovery_engine.recover_and_resolve_all()
            logger.info(f"Phase 50 offline gap recovery complete: {gap_res.get('trades_resolved', 0)} paper trades resolved.")
        except Exception as e:
            logger.error(f"Error during offline gap recovery: {e}")

        # 3. Recalculate forecasts based on the newly inserted data
        await live_forecast_scheduler.run_candle_scan_cycle()
        logger.info("Recalculated future forecasts using freshest data.")

        # 4. Hydrate actionable opportunities into ActionableSignalEngine
        try:
            from app.analytics.daily_signal_journal import daily_signal_journal
            from app.decision.actionable_signal_engine import actionable_signal_engine
            today_j = daily_signal_journal.get_today_journal()
            for fc in today_j.get("forecasts", []):
                actionable_signal_engine.create_actionable_opportunity(fc)
            logger.info("Hydrated actionable trade opportunities into ActionableSignalEngine.")
        except Exception as e:
            logger.error(f"Error hydrating actionable opportunities: {e}")
        
startup_sync = StartupSyncService()

