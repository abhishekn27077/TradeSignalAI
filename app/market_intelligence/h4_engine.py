import asyncio
from datetime import datetime, timezone

from app.analytics.forecast_manager import ForecastManager
from app.logs.logger import get_logger

logger = get_logger(__name__)

class H4ForecastEngine:
    """
    Scheduled job that generates forecasts every 4 hours for active markets using True Consensus AI.
    """
    
    def __init__(self):
        self._task = None
        self._running = False
        self._last_run_hour = None
        self.manager = ForecastManager()
        self.symbols = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("H4 Forecast Engine (Consensus AI) started")

    async def _run_loop(self):
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                # Check for 4-hour boundary (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
                if now.hour % 4 == 0 and now.minute < 5 and self._last_run_hour != now.hour:
                    logger.info(f"Triggering H4 Forecast Scan at {now.isoformat()}")
                    await self.generate_forecasts()
                    self._last_run_hour = now.hour
            except Exception as e:
                logger.error(f"Error in H4 Forecast Engine loop: {e}")
            
            await asyncio.sleep(60)

    async def generate_forecasts(self):
        """
        Executes H4 market scan using ForecastManager and publishes results.
        """
        try:
            results = await self.manager.scan_market(self.symbols, timeframes=["4H"])
            await self.publish_results(results)
            return results
        except Exception as e:
            logger.error(f"Failed to generate H4 forecasts: {e}")
            return []

    async def publish_results(self, results: list):
        try:
            import math
            import uuid
            from app.utils.event_bus import event_bus
            
            for r in results:
                quant_base = r.get('quant_baseline', {})
                conf = quant_base.get('confidence_score', 0)
                norm_conf = conf / 100.0 if conf > 1.0 else conf
                agree_pct = quant_base.get('agreement_percentage', 0)
                
                setup = r.get("setup", {})
                decision = setup.get("decision") or r.get("master_signal")
                direction = r.get("direction") or r.get("signal") or quant_base.get("signal")
                
                # Normalize direction
                if direction in ["BULLISH", "BUY", "LONG"]:
                    trade_dir = "BUY"
                elif direction in ["BEARISH", "SELL", "SHORT"]:
                    trade_dir = "SELL"
                else:
                    trade_dir = "NO_TRADE"
                
                entry_price = setup.get("entry_price") or setup.get("current_price")
                stop_loss = setup.get("stop_loss")
                take_profit = setup.get("take_profit")
                rr = setup.get("risk_reward_ratio") or setup.get("risk_reward") or 0.0

                # Strict Zero-Trust Validation Gate for Canonical Signal Emission
                is_valid_levels = (
                    entry_price is not None and not math.isnan(entry_price) and entry_price > 0 and
                    stop_loss is not None and not math.isnan(stop_loss) and stop_loss > 0 and
                    take_profit is not None and not math.isnan(take_profit) and take_profit > 0
                )
                
                if (
                    norm_conf >= 0.65 and 
                    agree_pct >= 75.0 and 
                    rr >= 1.50 and 
                    trade_dir in ["BUY", "SELL"] and 
                    is_valid_levels and
                    decision in ["TAKE_NOW", "ACTIVE"]
                ):
                    signal_payload = {
                        "signal_id": str(uuid.uuid4()),
                        "symbol": r['symbol'],
                        "asset": r['symbol'],
                        "direction": trade_dir,
                        "signal": trade_dir,
                        "decision": decision,
                        "confidence": norm_conf,
                        "strategy_name": "Consensus Ensemble Engine",
                        "winning_strategy": "Consensus Ensemble Engine",
                        "strategy_votes": [],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "trade_quality": r.get("trade_quality", "A"),
                        "expected_hold_hours": 4,
                        "market_regime": r.get('intelligence', {}).get('macro_context', 'UNKNOWN'),
                        "current_price": entry_price,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "target": take_profit,
                        "risk_reward": rr,
                        "expected_move": setup.get("expected_move_pct") or setup.get("expected_move"),
                        "intelligence": r.get('intelligence', {}),
                        "quant_baseline": quant_base,
                        "consensus_pct": norm_conf * 100.0,
                        "status": "ACTIVE",
                        "timeframe": "H4"
                    }
                    await event_bus.publish("SignalGenerated", payload=signal_payload)
                    await event_bus.publish("ConsensusCompleted", payload=signal_payload)
                    logger.info(f"Published Validated Canonical H4 Signal for {r['symbol']}: {trade_dir} @ {entry_price} (Conf: {norm_conf*100:.1f}%, R:R: {rr:.2f})")
                else:
                    logger.debug(f"H4 Scan candidate for {r['symbol']} did not pass canonical Zero-Trust gate (Conf={norm_conf*100:.1f}%, R:R={rr}, Dir={trade_dir})")
                    
        except Exception as e:
            logger.error(f"Failed to publish H4 forecasts: {e}")

h4_forecast_engine = H4ForecastEngine()

