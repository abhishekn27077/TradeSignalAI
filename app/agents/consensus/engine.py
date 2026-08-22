from typing import Any

import pandas as pd

from app.agents.base import BaseAIAgent
from app.logs.logger import get_logger
from app.market_data.providers.manager import market_provider_manager
from app.strategies.strategy_engine.adaptive_weights import AdaptiveWeightsEngine
from app.strategies.strategy_engine.agreement_engine import (
    AGREEMENT_SKIP,
    agreement_engine,
)
from app.strategies.strategy_engine.regime_detector import MarketRegimeDetector
from app.utils.event_bus import event_bus

logger = get_logger(__name__)


class ConsensusEngine:
    def __init__(self, chief_trader: BaseAIAgent | None = None, subordinates: list[BaseAIAgent] | None = None):
        self.chief = chief_trader
        self.subordinates = subordinates or []
        self.regime_detector = MarketRegimeDetector()
        self.adaptive_weights = AdaptiveWeightsEngine()

    async def run_consensus(self, symbol: str) -> dict[str, Any]:
        logger.info(f"Starting consensus for {symbol}")
        result = {
            "symbol": symbol,
            "signal": "HOLD",
            "confidence": 0.0,
            "agents": [],
            "status": "UNRESOLVED",
        }
        try:
            await event_bus.publish("ConsensusStarted", payload={"symbol": symbol})
        except Exception:
            pass

        try:
            rates = await market_provider_manager.get_rates(symbol, "1m", count=100)
            df = pd.DataFrame(rates) if rates else pd.DataFrame()
            current_price = df['close'].iloc[-1] if not df.empty else 0.0
            
            # Simple technical extraction for agent context
            trend = "BULLISH"
            if not df.empty and len(df) > 20:
                sma20 = df['close'].rolling(20).mean().iloc[-1]
                trend = "BULLISH" if current_price > sma20 else "BEARISH"
                
            agent_context = {
                "symbol": symbol, 
                "price": current_price,
                "trend": trend,
                "volatility": df['close'].pct_change().std() if not df.empty else 0.0
            }
        except Exception as e:
            logger.error(f"Failed to fetch real market context for agents: {e}. Aborting consensus to prevent synthetic fallback data.")
            raise ValueError(f"Real market data unavailable for {symbol}. Will not use synthetic UNKNOWN/0.0 fallbacks.")

        decisions = []
        for agent in self.subordinates:
            try:
                d = await agent.analyze(agent_context)
                decisions.append(d)
            except Exception as e:
                logger.warning(f"Agent {agent.agent_id} failed: {e}")

        if decisions:
            signals = [d.get("signal", "HOLD") for d in decisions]
            confidences = [d.get("confidence", 0) for d in decisions]
            buy_count = signals.count("BUY")
            sell_count = signals.count("SELL")
            
            # Determine initial majority signal
            majority_signal = "HOLD"
            if buy_count > sell_count:
                majority_signal = "BUY"
            elif sell_count > buy_count:
                majority_signal = "SELL"
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Pass subordinate decisions to Chief Trader
            if self.chief:
                logger.info(f"Passing consensus to Chief Trader for {symbol}")
                chief_context = {
                    "symbol": symbol,
                    "subordinate_signals": signals,
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "avg_confidence": avg_confidence
                }
                try:
                    chief_decision = await self.chief.analyze(chief_context)
                    majority_signal = chief_decision.get("signal", majority_signal)
                    avg_confidence = chief_decision.get("confidence", avg_confidence)
                except Exception as e:
                    logger.warning(f"Chief Trader failed: {e}")
            
            # Now run the Agreement Engine, Regime Detector, and SMC Filters for final validation
            try:
                if not df.empty and majority_signal in ["BUY", "SELL"]:
                    regime = self.regime_detector.detect_regime(df)
                    
                    candidate_dir = "CALL" if majority_signal == "BUY" else "PUT"
                    
                    # SMC Filters Validation
                    from datetime import datetime

                    from app.strategies.filters.news import news_filter
                    
                    news_status = news_filter.analyze(datetime.utcnow(), symbol)
                    
                    if news_status["impact"] != "NONE":
                        adj = news_status.get("confidence_adjustment", 0.0)
                        logger.info(f"News Impact detected for {symbol}. Adjusting confidence by {adj*100}%")
                        avg_confidence += adj
                        
                        if not news_status["can_trade"] or avg_confidence <= 0.0:
                            logger.warning(f"SMC Filter: Trading blocked due to High Impact News for {symbol}.")
                            majority_signal = "HOLD"
                            avg_confidence = 0.0
                    
                    # Compute agreement
                    class ProbabilityResult:
                        probability_score = avg_confidence * 100
                        regime_min_score = 60.0 if regime in ["REVERSAL_HEAVY", "HIGH_VOLATILITY"] else 55.0
                        
                    if majority_signal != "HOLD":
                        agreement = agreement_engine.compute(
                            df=df,
                            direction=candidate_dir,
                            metrics={},
                            regime=regime,
                            prob_result=ProbabilityResult()
                        )
                        
                        if agreement.tier == AGREEMENT_SKIP:
                            logger.info(f"Agreement Engine rejected {majority_signal} for {symbol}. Overriding to HOLD.")
                            majority_signal = "HOLD"
                            avg_confidence = 0.0
                        else:
                            logger.info(f"Agreement Engine confirmed {majority_signal} for {symbol} ({agreement.tier}).")
                            if agreement.tier == "STRONG_SIGNAL":
                                avg_confidence = min(1.0, avg_confidence + 0.1)
                                
                        # Institutional metrics population (Decision Card)
                        if majority_signal in ["BUY", "SELL"]:
                            current_price = df['close'].iloc[-1]
                            
                            # Simple ATR approximation for SL
                            if 'high' in df.columns and 'low' in df.columns:
                                tr = df['high'] - df['low']
                                atr = tr.rolling(14).mean().iloc[-1]
                            else:
                                atr = current_price * 0.002 # 0.2% default
                                
                            sl_dist = atr * 1.5
                            tp_dist = atr * 3.0 # 1:2 Risk/Reward
                            
                            stop_loss = current_price - sl_dist if majority_signal == "BUY" else current_price + sl_dist
                            target = current_price + tp_dist if majority_signal == "BUY" else current_price - tp_dist
                            
                            result["target"] = target
                            result["stop_loss"] = stop_loss
                            result["market_regime"] = regime
                            result["volatility_pct"] = (atr / current_price) * 100 if current_price > 0 else 0
                            
                            # Adx approximation for trend strength
                            result["trend_strength"] = abs(df['close'].pct_change(14).iloc[-1]) * 100 if not df.empty else 0.0
                            result["trade_quality"] = getattr(agreement, "tier", "B")
                            result["news_impact"] = news_status["impact"]
                            
                            # Historical similar setups (Memory Engine)
                            try:
                                from app.memory.manager import memory_manager
                                mem_stats = await memory_manager.find_similar_setups(symbol, "1m", regime)
                                result["historical_similars"] = {
                                    "count": mem_stats.get("count", 0),
                                    "win_rate": mem_stats.get("win_rate", 0.0),
                                    "best_strategy": mem_stats.get("best_strategy", "N/A")
                                }
                            except Exception:
                                result["historical_similars"] = {
                                    "count": 0,
                                    "win_rate": 0.0,
                                    "best_strategy": "N/A"
                                }
                            
            except Exception as e:
                logger.error(f"Validation failed: {e}")

            result["signal"] = majority_signal
            result["confidence"] = avg_confidence
            result["agents"] = decisions
            result["status"] = "RESOLVED"

        try:
            await event_bus.publish("ConsensusCompleted", payload=result)
        except Exception:
            pass

        return result

    async def get_current_consensus(self) -> dict[str, Any]:
        return {"status": "standby", "signal": "HOLD", "confidence": 0}


consensus_engine = ConsensusEngine()
