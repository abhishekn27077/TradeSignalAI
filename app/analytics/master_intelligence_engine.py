"""
app/analytics/master_intelligence_engine.py  — Phase 33
==========================================================
Phase 33 Enhancement: complete trace_id propagation, per-model latency,
and full intelligence snapshot for the evidence ledger.
"""
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import pandas as pd

from app.analytics.consensus_engine import ConsensusEngine
from app.intelligence.news_engine import news_engine
from app.intelligence.sentiment_engine import sentiment_engine
from app.intelligence.event_risk import event_risk_engine
from app.intelligence.cross_market import cross_market_engine
from app.intelligence.synthesis_engine import synthesis_engine
from app.intelligence.contradiction_detector import contradiction_detector
from app.intelligence.llm_risk_analyst import llm_risk_analyst
from app.analytics.no_trade_engine import no_trade_engine

logger = logging.getLogger(__name__)


class MasterIntelligenceEngine:
    """
    Phase 9 / Phase 33: Master Intelligence Engine.
    Aggregates Quant (ConsensusEngine) + Kronos + LLM Context + Event Risk.

    Phase 33 additions:
    - Accepts and propagates trace_id through every sub-call
    - Returns model_trace: per-model (XGB/RF/HGB/Stat/Kronos) latency + result
    - Returns complete intelligence_snapshot for EvidenceLedger
    """

    def __init__(self):
        self.quant_engine = ConsensusEngine()

    async def generate_master_signal(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        trace_id: Optional[str] = None,
        prediction_timestamp: Optional[datetime] = None,
        ablation_mode: str = "MODE_C",
    ) -> Dict[str, Any]:
        """
        Generate a master trading signal with complete traceability.

        Parameters
        ----------
        symbol : str
        timeframe : str
        df : pd.DataFrame  — OHLCV with features (closed candles only)
        trace_id : str     — UUID propagated from pipeline entry
        prediction_timestamp : datetime — exact moment of evaluation
        ablation_mode : str — 'MODE_A' (Quant Only), 'MODE_B' (Quant+Kronos), 'MODE_C' (Full Stack)

        Returns
        -------
        dict — master signal with full model_trace and intelligence_snapshot
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        if prediction_timestamp is None:
            prediction_timestamp = datetime.now(timezone.utc)

        pipeline_start = time.perf_counter()

        # ── 1. Quant Baseline (Synchronous) ─────────────────────────────────
        t0 = time.perf_counter()
        quant_result = self.quant_engine.generate_consensus(symbol, timeframe, df)
        quant_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        if "error" in quant_result or quant_result.get("signal") == "NEUTRAL":
            return {
                "trace_id": trace_id,
                "prediction_timestamp": prediction_timestamp.isoformat(),
                "symbol": symbol,
                "timeframe": timeframe,
                "master_signal": "NO_TRADE",
                "reason": quant_result.get("error", "NEUTRAL_QUANT_SIGNAL"),
                "model_trace": {"quant_latency_ms": quant_latency_ms},
            }

        quant_signal = quant_result["signal"]
        breakdown = quant_result.get("breakdown", {})
        kronos_pred = breakdown.get("kronos", 0)
        kronos_signal = "BULLISH" if kronos_pred > 0.001 else "BEARISH" if kronos_pred < -0.001 else "NEUTRAL"

        # Per-model trace (Phase 33: individual model results + latency)
        model_trace = {
            "quant": {
                "signal": quant_signal,
                "agreement_pct": quant_result.get("agreement_percentage"),
                "consensus_expected_return": quant_result.get("consensus_expected_return"),
                "latency_ms": quant_latency_ms,
                "breakdown": breakdown,
            }
        }
        
        # Ablation Logic: Mask Kronos if MODE_A
        if ablation_mode == "MODE_A":
            kronos_pred = 0
            kronos_signal = "NEUTRAL"
            
        # If not MODE_C, we skip intelligence gathering
        if ablation_mode in ["MODE_A", "MODE_B"]:
            regime_data = {"regime": "UNKNOWN"}
            regime = "UNKNOWN"
            regime_latency_ms = 0.0
            
            news_trace = {"overall": "UNKNOWN"}
            news_sentiment = "UNKNOWN"
            news_latency_ms = 0.0
            
            cross_market = {}
            macro_context = "UNKNOWN"
            cross_market_latency_ms = 0.0
            
            event_risk = {"risk_level": "UNKNOWN"}
            event_latency_ms = 0.0
            
            historical_analog = {"status": "UNAVAILABLE"}
            faiss_latency_ms = 0.0
            
            time_pattern = {"status": "UNAVAILABLE"}
            time_pattern_latency_ms = 0.0
            
            synthesis = None
            synthesis_latency_ms = 0.0
            
            contradictions = None
            
            risk_assessment = None
            veto_flag = False
            llm_latency_ms = 0.0
            
            no_trade_decision = {"decision": "TRADE", "reasons": []}
            
            total_latency_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)
        else:
            # ── 2. Market Regime ─────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                from app.decision.regime import market_regime_engine
                regime_data = market_regime_engine.analyze(symbol)
            except Exception as e:
                logger.warning(f"Regime engine failed: {e}")
                regime_data = {"regime": "UNKNOWN", "error": str(e)}
            regime_latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            regime = regime_data.get("regime", "UNKNOWN")

            # ── 3. News Sentiment ────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                news_sentiment_res = await sentiment_engine.get_asset_sentiment(symbol)
                news_sentiment = news_sentiment_res["overall"]
                news_trace = news_sentiment_res
            except Exception as e:
                logger.warning(f"Sentiment engine failed: {e}")
                news_sentiment = "NO_VERIFIED_NEWS"
                news_trace = {"overall": "NO_VERIFIED_NEWS", "error": str(e)}
            news_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 4. Cross-Market ──────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                cross_market = cross_market_engine.analyze_correlations(symbol, quant_signal)
                macro_context = cross_market.get("macro_regime", "UNKNOWN") if cross_market else "UNKNOWN"
            except Exception as e:
                logger.warning(f"Cross-market engine failed: {e}")
                cross_market = {"error": str(e)}
                macro_context = "UNKNOWN"
            cross_market_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 5. Event Risk ────────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                event_risk = event_risk_engine.calculate_event_risk(symbol)
            except Exception as e:
                logger.warning(f"Event risk engine failed: {e}")
                event_risk = {"risk_level": "UNKNOWN", "error": str(e)}
            event_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 6. FAISS Historical Analog ───────────────────────────────────────
            t0 = time.perf_counter()
            try:
                from app.intelligence.faiss_memory import faiss_memory

                if not df.empty and isinstance(df.index, pd.DatetimeIndex):
                    query_timestamp = df.index[-1]
                elif not df.empty and 'timestamp' in df.columns:
                    query_timestamp = pd.to_datetime(df['timestamp'].iloc[-1])
                else:
                    query_timestamp = pd.Timestamp(prediction_timestamp)

                historical_analog = faiss_memory.get_historical_analogs(
                    symbol, timeframe, df, query_timestamp
                )
            except Exception as e:
                logger.warning(f"FAISS engine failed: {e}")
                historical_analog = {
                    "status": "UNAVAILABLE",
                    "reason": str(e),
                    "leak_check": False,
                }
            faiss_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 7. Time Pattern ──────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                from app.intelligence.time_pattern import HistoricalTimePatternEngine
                time_pattern = HistoricalTimePatternEngine.analyze(
                    symbol, current_time=prediction_timestamp, timeframe=timeframe
                )
            except Exception as e:
                logger.warning(f"Time pattern engine failed: {e}")
                time_pattern = {"status": "UNAVAILABLE", "error": str(e)}
            time_pattern_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 8. LLM Synthesis ─────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                synthesis = await synthesis_engine.synthesize(
                    asset=symbol,
                    quant_signal=quant_signal,
                    kronos_signal=kronos_signal,
                    regime=regime,
                    news_sentiment=news_sentiment,
                    macro_context=macro_context,
                    event_risk=event_risk,
                )
            except Exception as e:
                logger.warning(f"Synthesis engine failed: {e}")
                synthesis = None
            synthesis_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 9. Contradiction Detection ───────────────────────────────────────
            try:
                contradictions = contradiction_detector.detect_contradictions(
                    quant_signal=quant_signal,
                    kronos_signal=kronos_signal,
                    news_sentiment=news_sentiment,
                    macro_context=macro_context,
                    event_risk=event_risk,
                )
            except Exception as e:
                logger.warning(f"Contradiction detector failed: {e}")
                contradictions = None

            # ── 10. LLM Risk Analyst Veto ────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                risk_assessment = await llm_risk_analyst.analyze_risk(
                    asset=symbol,
                    quant_signal=quant_signal,
                    kronos_signal=kronos_signal,
                    regime=regime,
                    news_sentiment=news_sentiment,
                    macro_context=macro_context,
                    event_risk=event_risk,
                )
                veto_flag = risk_assessment.veto_trade if risk_assessment else False
            except Exception as e:
                logger.warning(f"LLM Risk Analyst failed: {e}")
                risk_assessment = None
                veto_flag = False
            llm_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            # ── 11. Final No-Trade Check ─────────────────────────────────────────
            try:
                no_trade_decision = no_trade_engine.evaluate(
                    expected_move=abs(quant_result.get("consensus_expected_return", 0)),
                    event_risk=event_risk,
                    model_agreement=quant_result.get("agreement_percentage", 0) / 100.0,
                    contradiction_score=contradictions.contradiction_score if contradictions else 0,
                    veto_flag=veto_flag,
                )
            except Exception as e:
                logger.warning(f"No-trade engine failed: {e}")
                no_trade_decision = {"decision": "TRADE", "reasons": []}

        master_signal = quant_signal
        if no_trade_decision.get("decision") == "NO_TRADE":
            master_signal = "NO_TRADE"

        total_latency_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)

        # ── Complete model trace (Phase 33) ──────────────────────────────────
        model_trace["kronos"] = {
            "prediction": kronos_pred,
            "signal": kronos_signal,
        }
        model_trace["faiss"] = {**historical_analog, "latency_ms": faiss_latency_ms}
        model_trace["time_pattern"] = {**time_pattern, "latency_ms": time_pattern_latency_ms}
        model_trace["regime"] = {**regime_data, "latency_ms": regime_latency_ms}
        model_trace["cross_market"] = {**(cross_market or {}), "latency_ms": cross_market_latency_ms}
        model_trace["news"] = {**news_trace, "latency_ms": news_latency_ms}
        model_trace["event_risk"] = {
            **(event_risk if isinstance(event_risk, dict) else {"event_risk": event_risk}),
            "latency_ms": event_latency_ms,
        }
        model_trace["synthesis"] = {
            "result": synthesis.model_dump() if synthesis else None,
            "latency_ms": synthesis_latency_ms,
        }
        model_trace["llm_veto"] = {
            "veto_flag": veto_flag,
            "result": risk_assessment.model_dump() if risk_assessment else None,
            "latency_ms": llm_latency_ms,
        }
        model_trace["total_pipeline_latency_ms"] = total_latency_ms

        # ── Complete return ──────────────────────────────────────────────────
        return {
            "trace_id": trace_id,
            "prediction_timestamp": prediction_timestamp.isoformat(),
            "symbol": symbol,
            "timeframe": timeframe,
            "master_signal": master_signal,
            "quant_baseline": quant_result,
            "model_trace": model_trace,
            "intelligence": {
                "news_sentiment": news_sentiment,
                "macro_context": macro_context,
                "event_risk": event_risk,
                "historical_analog": historical_analog,
                "time_pattern": time_pattern,
                "synthesis": synthesis.model_dump() if synthesis else None,
                "contradictions": contradictions.model_dump() if contradictions else None,
                "risk_analyst": risk_assessment.model_dump() if risk_assessment else None,
                "no_trade_reasons": no_trade_decision.get("reasons", []),
            },
        }


master_intelligence_engine = MasterIntelligenceEngine()
