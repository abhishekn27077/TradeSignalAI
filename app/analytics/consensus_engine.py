import pandas as pd
import numpy as np
import logging
import time
from typing import Dict, Any

from app.analytics.models.kronos.adapter import KronosAdapter
from app.analytics.models.statistical_adapters import StatisticalAdapter
from app.market_intelligence.pattern_engine import market_memory

logger = logging.getLogger(__name__)

class ConsensusEngine:
    """
    Institutional Consensus Engine.
    Aggregates predictions from Kronos Foundation Model, XGBoost, RandomForest, 
    HistGradientBoosting, and Historical Pattern Memory to generate a final weighted forecast.
    """
    def __init__(self):
        self.kronos_model = KronosAdapter(device="cpu")
        self.xgb_model = StatisticalAdapter(model_name="xgboost")
        self.rf_model = StatisticalAdapter(model_name="random_forest")
        self.hgb_model = StatisticalAdapter(model_name="hist_gb")
        
        # Weights for the ensemble. Kronos validated in OOS tests!
        self.weights = {
            "kronos": 0.50,
            "xgboost": 0.15,
            "random_forest": 0.10,
            "hist_gb": 0.15,
            "pattern_memory": 0.10
        }

    def generate_consensus(self, symbol: str, timeframe: str, df: pd.DataFrame, prediction_timestamp: float = None) -> Dict[str, Any]:
        """
        Runs all models and memory engine to output a consensus decision.
        """
        if df.empty:
            return {"error": "Empty dataframe provided to ConsensusEngine"}

        # 1. Prepare data specifically for Kronos
        try:
            kronos_df = self.kronos_model.format_market_data(df)
            kronos_pred = self.kronos_model.predict(kronos_df, pred_len=1)
        except Exception as e:
            logger.error(f"Kronos prediction failed in consensus: {e}")
            kronos_pred = 0.0

        # 2. Prepare data for Statistical Models
        # (Assuming df passed to this function already has FeatureEngine.add_all_features applied 
        # based on prior logic, or we run it here if not. The previous logic didn't re-format, 
        # so we assume df is pre-formatted for stats).
        xgb_pred = self.xgb_model.predict(df)
        rf_pred = self.rf_model.predict(df)
        hgb_pred = self.hgb_model.predict(df)
        
        # 3. Run Pattern Memory
        latest_features = df.drop(columns=['Future_Return_5', 'close'], errors='ignore').iloc[-1].to_dict()
        
        if prediction_timestamp is None:
            # Fallback to the latest timestamp in the dataframe
            idx_val = df.index[-1]
            prediction_timestamp = idx_val.timestamp() if hasattr(idx_val, 'timestamp') else time.time()
            
        memory_result = market_memory.find_similar_patterns(
            symbol, timeframe, latest_features, k=50, prediction_timestamp=prediction_timestamp
        )
        
        # 4. Process Pattern Memory Output
        mem_expected_return = 0.0
        if "error" not in memory_result:
            mem_expected_return = memory_result.get("expected_return", 0.0)
            
        # 5. Calculate Weighted Consensus
        consensus_return = (
            (kronos_pred * self.weights["kronos"]) +
            (xgb_pred * self.weights["xgboost"]) +
            (rf_pred * self.weights["random_forest"]) +
            (hgb_pred * self.weights["hist_gb"]) +
            (mem_expected_return * self.weights["pattern_memory"])
        )
        
        # 6. Determine Agreement Level
        predictions = [kronos_pred, xgb_pred, rf_pred, hgb_pred, mem_expected_return]
        # Ignore zero predictions (e.g. if kronos is off/failed)
        valid_predictions = [p for p in predictions if abs(p) > 1e-6]
        if not valid_predictions:
            bullish_votes, bearish_votes = 0, 0
        else:
            bullish_votes = sum(1 for p in valid_predictions if p > 0)
            bearish_votes = sum(1 for p in valid_predictions if p < 0)
        
        agreement_pct = 0.0
        if len(valid_predictions) > 0:
            agreement_pct = max(bullish_votes, bearish_votes) / len(valid_predictions)
        
        signal = "NEUTRAL"
        # Require 75% agreement and a meaningful move (> 0.2% expected return over 5 bars)
        if agreement_pct >= 0.75:
            if consensus_return > 0.002:
                signal = "BULLISH"
            elif consensus_return < -0.002:
                signal = "BEARISH"
                
        # Calculate Confidence Score (0-100) based on agreement and magnitude
        magnitude_factor = min(abs(consensus_return) / 0.01, 1.0) # Cap at 1% move
        confidence = (agreement_pct * 0.7 + magnitude_factor * 0.3) * 100

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "consensus_expected_return": float(consensus_return),
            "confidence_score": float(confidence),
            "agreement_percentage": float(agreement_pct * 100),
            "breakdown": {
                "kronos": float(kronos_pred),
                "xgboost": float(xgb_pred),
                "random_forest": float(rf_pred),
                "hist_gb": float(hgb_pred),
                "pattern_memory": float(mem_expected_return)
            },
            "memory_narrative": memory_result.get("memory_narrative", "No historical memory found.")
        }

