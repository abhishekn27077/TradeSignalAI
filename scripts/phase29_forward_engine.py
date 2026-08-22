import os
import time
import json
import asyncio
from datetime import datetime
import pandas as pd
import yfinance as yf

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analytics.feature_engine import FeatureEngine
from app.analytics.models.kronos.adapter import KronosAdapter
from app.logs.logger import get_logger

logger = get_logger("phase29_forward_engine")

class Phase29ForwardEngine:
    """
    Live Forward Paper-Trading Engine.
    This strictly runs in real-time, fetching live data, running all intelligence 
    ablation variants independently, and logging EVERY decision (approved and rejected) 
    to prevent survivorship bias.
    """
    def __init__(self):
        self.assets = ["BTC-USD", "ETH-USD", "EURUSD=X", "GBPUSD=X", "SPY", "QQQ"]
        self.kronos = KronosAdapter()
        
        self.artifacts_dir = os.path.abspath(r"C:\Users\Abhis\.gemini\antigravity-ide\brain\d1f3a00e-4c5b-494d-8d0b-14018e87107f")
        self.signals_file = os.path.join(self.artifacts_dir, "phase29_signals.csv")
        self.metrics_file = os.path.join(self.artifacts_dir, "phase29_metrics.csv")
        
        self._init_csv()

    def _init_csv(self):
        if not os.path.exists(self.signals_file):
            pd.DataFrame(columns=[
                "signal_id", "timestamp", "asset", "ablation_mode", "direction", 
                "entry_price", "stop_loss", "take_profit", "confidence", 
                "kronos_probability", "news_sentiment", "reason", "status"
            ]).to_csv(self.signals_file, index=False)

    def _log_signal(self, data: dict):
        df = pd.DataFrame([data])
        df.to_csv(self.signals_file, mode='a', header=False, index=False)

    def fetch_live_data(self, asset: str) -> pd.DataFrame:
        df = yf.download(asset, period="7d", interval="1h", progress=False)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df.reset_index(inplace=True)
        df.rename(columns={'Datetime': 'timestamp', 'Date': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
        df.set_index('timestamp', inplace=True)
        return FeatureEngine.add_all_features(df)

    async def run_ablation_cycle(self):
        logger.info(f"Running Phase 29 Forward Ablation Cycle at {datetime.utcnow()}")
        
        for asset in self.assets:
            try:
                df = self.fetch_live_data(asset)
                if df.empty:
                    continue
                    
                current_price = df['close'].iloc[-1]
                
                # Baseline 1: RSI (Quant Only)
                rsi = df['RSI_14'].iloc[-1]
                quant_dir = "BUY" if rsi < 30 else "SELL" if rsi > 70 else "NEUTRAL"
                self._log_signal({
                    "signal_id": f"sig_{int(time.time())}_Q_{asset}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "asset": asset,
                    "ablation_mode": "Quant Only",
                    "direction": quant_dir,
                    "entry_price": current_price,
                    "stop_loss": current_price * 0.95 if quant_dir == "BUY" else current_price * 1.05,
                    "take_profit": current_price * 1.10 if quant_dir == "BUY" else current_price * 0.90,
                    "confidence": 60,
                    "kronos_probability": 0.0,
                    "news_sentiment": 0.0,
                    "reason": "RSI Threshold Triggered" if quant_dir != "NEUTRAL" else "No Edge",
                    "status": "APPROVED" if quant_dir != "NEUTRAL" else "REJECTED"
                })
                
                # Baseline 2: Quant + Kronos
                if self.kronos.model:
                    kronos_pred = self.kronos.predict(df.iloc[-100:])
                    k_dir = "BUY" if kronos_pred > 0 else "SELL"
                    k_conf = min(50 + abs(kronos_pred * 1000), 99)
                    self._log_signal({
                        "signal_id": f"sig_{int(time.time())}_QK_{asset}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "asset": asset,
                        "ablation_mode": "Quant + Kronos",
                        "direction": k_dir,
                        "entry_price": current_price,
                        "stop_loss": current_price * 0.95 if k_dir == "BUY" else current_price * 1.05,
                        "take_profit": current_price * 1.10 if k_dir == "BUY" else current_price * 0.90,
                        "confidence": k_conf,
                        "kronos_probability": float(kronos_pred),
                        "news_sentiment": 0.0,
                        "reason": "Kronos Forward Pass",
                        "status": "APPROVED"
                    })
                
            except Exception as e:
                logger.error(f"Error processing {asset}: {e}")

    async def start(self):
        logger.info("Phase 29 Forward Engine Initialized. Freezing weights and models.")
        # Run one cycle immediately so we generate CSVs for the test
        await self.run_ablation_cycle()
        # Simulating a continuous loop running every hour for H4/H1 testing
        while True:
            await asyncio.sleep(3600)
            await self.run_ablation_cycle()

if __name__ == "__main__":
    engine = Phase29ForwardEngine()
    asyncio.run(engine.start())
