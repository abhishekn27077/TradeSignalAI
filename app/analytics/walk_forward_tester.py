import pandas as pd
import logging
from typing import Dict, Any

from app.analytics.consensus_engine import ConsensusEngine

logger = logging.getLogger(__name__)

class WalkForwardTester:
    """
    Performs walk-forward optimization and backtesting on the Consensus Engine.
    Phase 11: Validation and Backtesting.
    """
    def __init__(self):
        self.consensus = ConsensusEngine()
        
    def run_backtest(self, symbol: str, timeframe: str, df: pd.DataFrame, window_size: int = 500, step_size: int = 50) -> Dict[str, Any]:
        """
        Simulates trading through historical data using an expanding window to prevent data snooping.
        """
        if len(df) < window_size + step_size:
            return {"error": "Not enough data for walk-forward testing"}
            
        logger.info(f"Starting Walk-Forward test for {symbol} {timeframe}")
        
        results = []
        # Walk forward through the dataset
        for end_idx in range(window_size, len(df) - 5, step_size):
            train_df = df.iloc[:end_idx]
            test_df = df.iloc[end_idx:end_idx + step_size]
            
            # Re-train models on train_df
            self.consensus.xgb_model.train(train_df)
            self.consensus.rf_model.train(train_df)
            self.consensus.hgb_model.train(train_df)
            
            # Predict on test_df row by row
            for i in range(len(test_df)):
                current_context = train_df._append(test_df.iloc[:i+1])
                forecast = self.consensus.generate_consensus(symbol, timeframe, current_context)
                
                signal = forecast.get("signal", "NEUTRAL")
                if signal != "NEUTRAL" and forecast.get("confidence_score", 0) > 65.0:
                    # Execute hypothetical trade
                    entry_price = current_context['close'].iloc[-1]
                    # Check next 5 bars for outcome
                    if end_idx + i + 5 < len(df):
                        future_close = df['close'].iloc[end_idx + i + 5]
                        actual_return = (future_close - entry_price) / entry_price
                        
                        trade_profit = actual_return if signal == "BULLISH" else -actual_return
                        results.append({
                            "timestamp": current_context.index[-1],
                            "signal": signal,
                            "entry": entry_price,
                            "exit": future_close,
                            "profit_pct": trade_profit,
                            "confidence": forecast["confidence_score"]
                        })
                        
        if not results:
            return {"trades": 0, "win_rate": 0.0, "total_return": 0.0}
            
        results_df = pd.DataFrame(results)
        win_rate = (results_df['profit_pct'] > 0).mean()
        total_return = results_df['profit_pct'].sum()
        
        return {
            "trades": len(results),
            "win_rate": float(win_rate * 100),
            "total_return": float(total_return * 100),
            "avg_profit_per_trade": float(results_df['profit_pct'].mean() * 100)
        }
