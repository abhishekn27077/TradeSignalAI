import asyncio
import pandas as pd
from app.database.manager import db_manager
from app.strategies.plugins.otc_confluence import OTCConfluenceStrategy
from app.config import settings

async def debug_bt_core():
    db_manager.connect()
    await db_manager.init_db()
    
    symbol = 'EURUSD'
    timeframe = 'D1'
    
    query = f"SELECT timestamp, open, high, low, close, volume FROM historical_candles WHERE symbol = '{symbol}' AND timeframe = '{timeframe}' ORDER BY timestamp ASC"
    
    conn = db_manager._engine
    async with conn.begin() as sql_conn:
        df = await sql_conn.run_sync(lambda sync_conn: pd.read_sql_query(query, sync_conn))

    if df.empty:
        print("No data found!")
        return
        
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    print(f"Rows fetched: {len(df)}")
    
    strategy = OTCConfluenceStrategy(name="OTC")
    strategy.initialize()
    
    min_window = 200
    signals = []
    
    print(f"Simulating window {min_window} to {len(df)}")
    for i in range(min_window, len(df)):
        window = df.iloc[i-min_window : i]
        current_time = window.index[-1]
        
        try:
            signal = strategy.analyze(symbol, window)
            if signal:
                signal_dict = signal.dict()
                if hasattr(signal.strength, 'value'):
                    signal_dict['strength'] = signal.strength.value
                if hasattr(signal.direction, 'value'):
                    signal_dict['direction'] = signal.direction.value
                signal_dict['backtest_time'] = current_time.isoformat()
                signals.append(signal_dict)
        except Exception as e:
            pass

    print(f"Total Signals: {len(signals)}")
    if not signals:
        return

    signals_df = pd.DataFrame(signals)
    strong_signals = signals_df[signals_df['strength'] == 'STRONG']
    print(f"Strong Signals: {len(strong_signals)}")
    
    trades = []
    for _, sig in strong_signals.iterrows():
        b_time = pd.to_datetime(sig['backtest_time'])
        try:
            idx = df.index.get_loc(b_time)
            if idx + 5 < len(df):
                entry_price = float(df.iloc[idx]['close'])
                exit_price = float(df.iloc[idx + 5]['close'])
                
                pnl = exit_price - entry_price if sig['direction'] == 'BUY' else entry_price - exit_price
                
                trades.append({
                    'time': b_time.isoformat(),
                    'direction': sig['direction'],
                    'entry': entry_price,
                    'exit': exit_price,
                    'pnl': pnl,
                })
            else:
                print(f"Trade ignored: index {idx} too close to end.")
        except Exception as e:
            print(f"Error processing trade at {b_time}: {e}")

    print(f"Total Trades Generated: {len(trades)}")

asyncio.run(debug_bt_core())
