import logging
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy import select

from app.database.manager import db_manager
from app.database.models.market import CandleModel
from app.analytics.master_intelligence_engine import master_intelligence_engine

logger = logging.getLogger(__name__)

class ForecastManager:
    """
    Institutional Forecast Manager.
    Scans the database for recent H4, D1, W1 candles, runs the consensus engine,
    and publishes valid trade setups if confidence is high.
    """
    def __init__(self):
        self.consensus = master_intelligence_engine
        # Minimum requirements for a trade setup
        self.min_confidence = 65.0 # 65% minimum confidence
        self.min_agreement = 0.75 # 3 out of 4 engines must agree

    async def scan_market(
        self,
        symbols: List[str],
        trace_id: str = None,
        prediction_timestamp: Any = None,
        timeframes: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans given symbols across specified timeframes for trading setups.
        Phase 35: Executes 3-way ablation (MODE_A, MODE_B, MODE_C) in parallel.
        """
        import asyncio
        setups = []
        target_tfs = timeframes if timeframes else ["4H", "1D", "1W"]
        seen_keys = set()
        
        for symbol in symbols:
            for tf in target_tfs:
                df = await self._fetch_recent_data(symbol, tf)
                if df.empty or len(df) < 50:
                    continue
                    
                # Phase 35: 3-Way Ablation Parallel Execution
                tasks = [
                    self.consensus.generate_master_signal(symbol, tf, df, trace_id, prediction_timestamp, "MODE_A"),
                    self.consensus.generate_master_signal(symbol, tf, df, trace_id, prediction_timestamp, "MODE_B"),
                    self.consensus.generate_master_signal(symbol, tf, df, trace_id, prediction_timestamp, "MODE_C")
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Each mode returns a setup dictionary, we process them individually
                for i, mode_name in enumerate(["MODE_A", "MODE_B", "MODE_C"]):
                    res = results[i]
                    if isinstance(res, Exception):
                        logger.error(f"Error in {mode_name} for {symbol} {tf}: {res}")
                        continue
                        
                    if "error" in res:
                        logger.warning(f"Consensus error on {symbol} {tf} ({mode_name}): {res['error']}")
                        continue
                        
                    res["ablation_mode"] = mode_name  # Ensure it is tracked
                    
                    if res.get("master_signal") not in ["NEUTRAL", "NO_TRADE"]:
                        quant_baseline = res.get("quant_baseline", {})
                        conf_score = quant_baseline.get("confidence_score", 0)
                        agree_pct = quant_baseline.get("agreement_percentage", 0)
                        
                        if conf_score >= self.min_confidence and agree_pct >= (self.min_agreement * 100):
                            setup = self._build_trade_setup(df, res)
                            setup["ablation_mode"] = mode_name  # Copy down
                            setup["timeframe"] = tf
                            setup["symbol"] = symbol
                            
                            # Deterministic deduplication key
                            dedup_key = (symbol, tf, str(df.index[-1]), mode_name, str(setup.get("master_signal")))
                            if dedup_key not in seen_keys:
                                seen_keys.add(dedup_key)
                                setups.append(setup)
                            
                            # Phase 35: Record to CSV immediately
                            try:
                                from app.execution.evidence_ledger import evidence_ledger
                                evidence_ledger.write_phase35_signal_csv(res, trace_id)
                            except Exception as e:
                                logger.error(f"Failed to write Phase 35 signal CSV: {e}")
                            
        return setups

    async def _fetch_recent_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Fetches the most recent 200 candles from DB for feature inference.
        """
        if db_manager._session_factory is None:
            return pd.DataFrame()

        tf_map = {
            "4H": ["4H", "4h", "H4", "h4"],
            "4h": ["4H", "4h", "H4", "h4"],
            "H4": ["4H", "4h", "H4", "h4"],
            "1D": ["1D", "1d", "D1", "d1"],
            "1d": ["1D", "1d", "D1", "d1"],
            "D1": ["1D", "1d", "D1", "d1"],
            "1W": ["1W", "1w", "1wk", "W1", "w1"],
            "1wk": ["1W", "1w", "1wk", "W1", "w1"],
            "W1": ["1W", "1w", "1wk", "W1", "w1"],
            "1H": ["1H", "1h", "H1", "h1"],
            "1h": ["1H", "1h", "H1", "h1"],
            "H1": ["1H", "1h", "H1", "h1"],
        }
        valid_tfs = tf_map.get(timeframe, [timeframe, timeframe.lower(), timeframe.upper()])
            
        async with db_manager._session_factory() as session:
            stmt = select(CandleModel).filter(
                CandleModel.symbol == symbol,
                CandleModel.timeframe.in_(valid_tfs)
            ).order_by(CandleModel.timestamp.desc()).limit(200)
            
            result = await session.execute(stmt)
            candles = result.scalars().all()
            
        if not candles:
            return pd.DataFrame()
            
        # Reverse to chronological order
        candles = list(reversed(candles))
        
        records = []
        for c in candles:
            rec = {
                "timestamp": c.timestamp,
                "open": float(c.open or 0.0),
                "high": float(c.high or 0.0),
                "low": float(c.low or 0.0),
                "close": float(c.close or 0.0),
                "volume": float(c.volume or 0.0)
            }
            if c.features_json:
                rec.update(c.features_json)
            records.append(rec)
            
        df = pd.DataFrame(records)
        df.set_index("timestamp", inplace=True)
        return df

    def _build_trade_setup(self, df: pd.DataFrame, consensus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates Stop Loss and Take Profit based on ATR using the strict Risk Engine.
        """
        from app.strategies.risk_engine import risk_engine
        return risk_engine.calculate_setup(df, consensus)
