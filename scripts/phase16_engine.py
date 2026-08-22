import asyncio
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analytics.feature_engine import FeatureEngine
from app.market_intelligence.pattern_engine import MarketMemoryEngine
from app.forecast.consensus import ConsensusEngine
from app.logs.logger import get_logger

logger = get_logger("phase16_engine")

class BacktestValidationEngine:
    def __init__(self, db_url="sqlite+aiosqlite:///./trading_fallback.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.feature_engine = FeatureEngine()
        self.pattern_engine = MarketMemoryEngine()
        self.consensus_engine = ConsensusEngine()
        
    async def load_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        query = text("""
            SELECT timestamp, open, high, low, close, volume 
            FROM historical_candles 
            WHERE symbol = :s AND timeframe = :t 
            ORDER BY timestamp ASC
        """)
        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"s": symbol, "t": timeframe})
            rows = result.fetchall()
            
        if not rows:
            return pd.DataFrame()
            
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df

    def run_walk_forward(self, df: pd.DataFrame, asset: str, min_window: int = 500, dynamic_costs: bool = True):
        """
        Runs a STRICT zero-leakage walk-forward test.
        """
        if len(df) < min_window + 100:
            logger.warning(f"Not enough data for {asset}. Needed {min_window+100}, got {len(df)}")
            return None
            
        # 1. We pre-compute features for SPEED, but we MUST drop the lookahead column `Future_Return_5`
        # and ensure no other features leak. The FeatureEngine only uses rolling/shift which are backward looking.
        logger.info(f"Pre-computing features for {asset} ({len(df)} candles)...")
        features_df = self.feature_engine.add_all_features(df)
        if 'Future_Return_5' in features_df.columns:
            features_df.drop(columns=['Future_Return_5'], inplace=True)
            
        if len(features_df) < min_window + 5:
            logger.warning(f"Feature engineering dropped too many rows for {asset}. Expected {min_window+5}, got {len(features_df)}")
            return None
            
        # Ensure we only iterate over indices where we have features
        valid_indices = features_df.index
        
        results = []
        trades = []
        
        # Start iteration
        logger.info(f"Starting walk-forward for {asset} from {valid_indices[min_window]} to {valid_indices[-5]}")
        
        feature_cols = [c for c in features_df.columns if c not in ['open', 'high', 'low', 'close', 'volume', 'timestamp']]
        feature_matrix = features_df[feature_cols].fillna(0).values
        
        for i in range(min_window, len(valid_indices) - 5): # Reserve 5 candles for actual future outcome evaluation
            current_time = valid_indices[i]
            
            # --- STRICT ZERO LEAKAGE SLICE ---
            # All historical data strictly BEFORE and INCLUDING current_time
            history_slice = features_df.iloc[:i+1] 
            current_features = history_slice.iloc[-1]
            
            # 1. Historical Pattern Match (Brute Force Cosine Sim to guarantee no leakage)
            # We compare current_features to all previous features in history_slice (excluding the current one)
            vec_current = feature_matrix[i]
            history_matrix = feature_matrix[:i]
            
            # Normalize
            norm_curr = np.linalg.norm(vec_current)
            norm_hist = np.linalg.norm(history_matrix, axis=1)
            
            # Avoid division by zero
            norm_hist = np.where(norm_hist == 0, 1e-9, norm_hist)
            norm_curr = norm_curr if norm_curr > 0 else 1e-9
            
            sims = np.dot(history_matrix, vec_current) / (norm_hist * norm_curr)
            
            # Top 10 matches
            top_10_idx = np.argsort(sims)[-10:]
            
            # Evaluate what happened 5 candles AFTER those historical matches
            historical_outcomes = []
            for idx in top_10_idx:
                if idx + 5 < len(history_slice): # Ensure we don't look past the slice
                    h_entry = history_slice.iloc[idx]['close']
                    h_exit = history_slice.iloc[idx+5]['close']
                    ret = (h_exit - h_entry) / h_entry
                    historical_outcomes.append(ret)
                    
            if not historical_outcomes:
                continue
                
            avg_hist_return = np.mean(historical_outcomes)
            hist_direction = "BUY" if avg_hist_return > 0 else "SELL"
            hist_confidence = min(100, 50 + abs(avg_hist_return) * 1000) # Dummy scaling for memory confidence
            
            # 2. Mocking ML Models (In a real run we'd call XGBoost here using only `history_slice` for inference)
            # For this validation script, we use the Pattern Engine + Technical Confluence to simulate the model consensus
            
            macd_bull = current_features['MACD'] > current_features['MACD_signal']
            rsi = current_features['RSI_14']
            
            ml_direction = "BUY" if macd_bull and rsi < 70 else ("SELL" if not macd_bull and rsi > 30 else "NEUTRAL")
            
            predictions = [
                {"model_id": "FAISS_Memory", "direction": hist_direction, "confidence": hist_confidence, "expected_move_pct": avg_hist_return * 100, "expected_hold_time_hours": 24, "target_price": 0, "stop_price": 0},
                {"model_id": "XGBoost_Mock", "direction": ml_direction, "confidence": 65, "expected_move_pct": 0.5, "expected_hold_time_hours": 24, "target_price": 0, "stop_price": 0}
            ]
            
            consensus = self.consensus_engine.generate_consensus(predictions, current_features.to_dict())
            
            # 3. Execution & Costs
            if consensus['final_confidence'] > 60 and consensus['direction'] != 'NEUTRAL':
                # WE HAVE A SIGNAL. Now we look into the actual future to see what happened.
                entry_price = current_features['close']
                future_slice = features_df.iloc[i+1 : i+6] # Next 5 candles
                exit_price = future_slice.iloc[-1]['close']
                
                # Dynamic Costs
                if dynamic_costs:
                    # e.g., Spread = 0.02% + 0.05% slippage
                    cost_pct = 0.0007 
                else:
                    cost_pct = 0.0
                    
                if consensus['direction'] == 'BUY':
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - exit_price) / entry_price
                    
                net_pnl_pct = pnl_pct - cost_pct
                
                # Maximum Adverse/Favorable Excursion
                if consensus['direction'] == 'BUY':
                    mfe = (future_slice['high'].max() - entry_price) / entry_price
                    mae = (future_slice['low'].min() - entry_price) / entry_price
                else:
                    mfe = (entry_price - future_slice['low'].min()) / entry_price
                    mae = (entry_price - future_slice['high'].max()) / entry_price
                
                trades.append({
                    "timestamp": current_time.isoformat(),
                    "asset": asset,
                    "direction": consensus['direction'],
                    "confidence": consensus['final_confidence'],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "gross_return": pnl_pct,
                    "net_return": net_pnl_pct,
                    "mfe": mfe,
                    "mae": mae,
                    "win": net_pnl_pct > 0
                })
                
        # Calculate Metrics
        if not trades:
            return None
            
        trades_df = pd.DataFrame(trades)
        wins = trades_df['win'].sum()
        total_trades = len(trades_df)
        win_rate = wins / total_trades
        
        gross_profit = trades_df[trades_df['net_return'] > 0]['net_return'].sum()
        gross_loss = abs(trades_df[trades_df['net_return'] < 0]['net_return'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        net_return_total = trades_df['net_return'].sum()
        
        returns = trades_df['net_return']
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 6) if returns.std() != 0 else 0 # Approx H4 annualized
        
        return {
            "asset": asset,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "net_return": net_return_total,
            "sharpe": sharpe,
            "trades": trades
        }

async def run_all():
    engine = BacktestValidationEngine()
    
    assets = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]
    timeframe = "4h"
    
    all_results = {}
    
    for asset in assets:
        logger.info(f"Processing {asset} {timeframe}...")
        df = await engine.load_data(asset, timeframe)
        if df.empty:
            logger.warning(f"No data for {asset}")
            continue
            
        res = engine.run_walk_forward(df, asset)
        if res:
            all_results[asset] = {
                "win_rate": res['win_rate'],
                "profit_factor": res['profit_factor'],
                "net_return": res['net_return'],
                "total_trades": res['total_trades']
            }
            logger.info(f"--- {asset} RESULTS ---")
            logger.info(f"Win Rate: {res['win_rate']*100:.2f}% | PF: {res['profit_factor']:.2f} | Net: {res['net_return']*100:.2f}% | Trades: {res['total_trades']}")
            
    # Save to file
    import json
    with open("phase16_walkforward_results.json", "w") as f:
        json.dump(all_results, f, indent=4)
        
if __name__ == "__main__":
    asyncio.run(run_all())
