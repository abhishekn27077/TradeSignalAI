import asyncio
import os
import sys

import pandas as pd

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.logs.logger import get_logger
from app.market_data.providers.tradingview import TradingViewDataProvider
from app.strategies.plugins.registry import strategy_registry

logger = get_logger("backtest_engine")

async def run_backtest():
    logger.info("Initializing Backtest Engine...")
    
    # 1. Download Data
    tv = TradingViewDataProvider()
    await tv.connect()
    
    symbol = "BINANCE:BTCUSD"
    timeframe = "1H"
    count = 2160  # ~3 months of 1H data
    
    logger.info(f"Downloading {count} candles of {symbol} at {timeframe}...")
    rates = await tv.get_rates(symbol, timeframe, count=count)
    
    if not rates:
        logger.error("Failed to download data.")
        return
        
    df = pd.DataFrame(rates)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    logger.info(f"Downloaded data from {df.index[0]} to {df.index[-1]}")
    
    # 2. Load Strategies
    strategy_registry.load_plugins()
    active_strategies = []
    for s_name in strategy_registry.list_strategies():
        s_class = strategy_registry.get_strategy(s_name)
        strategy = s_class(name=s_name)
        strategy.initialize()
        active_strategies.append(strategy)
        logger.info(f"Loaded strategy: {s_name}")
        
    # 3. Simulate Live Data Feed
    min_window = 50  # Minimum candles needed for indicators
    signals = []
    
    logger.info("Starting simulation loop...")
    for i in range(min_window, len(df)):
        window = df.iloc[i-min_window : i]
        current_time = window.index[-1]
        
        for strategy in active_strategies:
            try:
                # Suppress strategy internal logs for speed, just capture signals
                signal = strategy.analyze(symbol, window)
                if signal:
                    # Inject backtest timestamp
                    signal_dict = signal.dict()
                    signal_dict['backtest_time'] = current_time.isoformat()
                    signals.append(signal_dict)
            except Exception as e:
                logger.error(f"Error in {strategy.name} at {current_time}: {e}")

    # 4. Analyze Results
    logger.info(f"Simulation complete. Total signals generated: {len(signals)}")
    
    if not signals:
        logger.info("No signals generated.")
        return
        
    signals_df = pd.DataFrame(signals)
    strong_signals = signals_df[signals_df['strength'] == 'STRONG']
    
    logger.info(f"Total Strong Signals: {len(strong_signals)}")
    
    # Evaluate forward returns for strong signals (simple 5-bar forward return)
    wins = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0
    returns = []
    
    print("\n--- STRONG SWING SIGNALS ---")
    for _, sig in strong_signals.iterrows():
        b_time = pd.to_datetime(sig['backtest_time'])
        # Find index of signal
        try:
            idx = df.index.get_loc(b_time)
            if idx + 5 < len(df):
                entry_price = df.iloc[idx]['close']
                exit_price = df.iloc[idx + 5]['close']
                
                if sig['direction'] == 'BUY':
                    pnl = exit_price - entry_price
                else:
                    pnl = entry_price - exit_price
                    
                pct_return = pnl / entry_price
                returns.append(pct_return)
                    
                if pnl > 0:
                    wins += 1
                    gross_profit += pnl
                else:
                    losses += 1
                    gross_loss += abs(pnl)
                
                print(f"[{b_time}] {sig['strategy_name']} | {sig['direction']} | Confidence: {sig['confidence']} | Reasoning: {sig['reasoning'][:80]}... | PnL: {pnl:.2f}")
        except Exception:
            pass
            
    total = wins + losses
    if total > 0:
        win_rate = (wins / total) * 100
        avg_win = gross_profit / wins if wins > 0 else 0
        avg_loss = gross_loss / losses if losses > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)
        
        returns_s = pd.Series(returns)
        sharpe = (returns_s.mean() / returns_s.std()) * (252**0.5) if returns_s.std() != 0 else 0.0
        monthly_return = returns_s.sum() * 100 * (30/90) # Approx scaled to monthly based on 3 months of data
        
        print("\n--- PERFORMANCE SUMMARY (Strong Signals) ---")
        print(f"Win Rate: {win_rate:.2f}% ({wins}W / {losses}L)")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"Expectancy ($ per trade): {expectancy:.2f}")
        print(f"Average RR (Reward/Risk): {avg_win/avg_loss if avg_loss > 0 else float('inf'):.2f}")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Est. Monthly Return: {monthly_return:.2f}%")
    
if __name__ == "__main__":
    asyncio.run(run_backtest())
