from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class BacktestEngine:
    def __init__(self):
        self._history: list = []

    async def run(
        self,
        symbol: str = "EURUSD",
        timeframe: str = "1h",
        strategy_name: str = "",
        capital: float = 10000.0,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        try:
            import pandas as pd

            from app.database.manager import db_manager
            from app.strategies.plugins.registry import strategy_registry
            
            # 1. Fetch Data
            conn = db_manager._engine
            if conn is None:
                raise Exception("Database engine not initialized")
            
            query = "SELECT timestamp, open, high, low, close, volume FROM historical_candles WHERE symbol = ? AND timeframe = ? ORDER BY timestamp ASC"
            async with conn.begin() as sql_conn:
                df = await sql_conn.run_sync(lambda sync_conn: pd.read_sql_query(query, sync_conn, params=(symbol, timeframe)))
                
            if df.empty:
                raise Exception(f"No historical data found for {symbol} {timeframe}")
                
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 2. Load Strategy
            strategy_registry.load_plugins()
            s_class = strategy_registry.get_strategy(strategy_name)
            if not s_class:
                raise Exception(f"Strategy {strategy_name} not found in registry")
            
            strategy = s_class(name=strategy_name)
            strategy.initialize()
            
            # 3. Simulate Loop
            min_window = 200
            signals = []
            
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
                    logger.debug(f"Strategy error at {current_time}: {e}")
                    
            # 4. Analyze Results
            wins = 0
            losses = 0
            gross_profit = 0.0
            gross_loss = 0.0
            returns = []
            trades = []
            
            if signals:
                signals_df = pd.DataFrame(signals)
                strong_signals = signals_df[signals_df['strength'] == 'STRONG']
                logger.info(f"Total Signals: {len(signals_df)}, Strong Signals: {len(strong_signals)}")
                
                for _, sig in strong_signals.iterrows():
                    b_time = pd.to_datetime(sig['backtest_time'])
                    try:
                        idx = df.index.get_loc(b_time)
                        if idx + 5 < len(df):
                            entry_price = float(df.iloc[idx]['close'])
                            exit_price = float(df.iloc[idx + 5]['close'])
                            
                            pnl = exit_price - entry_price if sig['direction'] == 'BUY' else entry_price - exit_price
                            pct_return = pnl / entry_price
                            returns.append(pct_return)
                            
                            if pnl > 0:
                                wins += 1
                                gross_profit += pnl
                            else:
                                losses += 1
                                gross_loss += abs(pnl)
                                
                            trades.append({
                                'time': b_time.isoformat(),
                                'direction': sig['direction'],
                                'entry': entry_price,
                                'exit': exit_price,
                                'pnl': pnl,
                                'return_pct': pct_return * 100
                            })
                        else:
                            logger.info(f"Trade ignored: index {idx} too close to end of df ({len(df)})")
                    except Exception as e:
                        logger.info(f"Error processing trade at {b_time}: {e}")
            else:
                logger.info(f"No signals generated for {symbol} {timeframe}")
            
            total_trades = wins + losses
            logger.info(f"Generated {total_trades} trades")
            win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0)
            
            result = {
                "config": {"symbol": symbol, "timeframe": timeframe, "capital": capital, "strategy": strategy_name},
                "metrics": {
                    "total_trades": total_trades,
                    "win_rate": round(win_rate, 2),
                    "profit_factor": round(profit_factor, 2),
                    "gross_profit": round(gross_profit, 2),
                    "gross_loss": round(gross_loss, 2)
                },
                "trades": trades
            }
            self._history.append(result)
            return result
            
        except Exception as e:
            logger.warning(f"Backtest run error: {e}")
            return {
                "config": {"symbol": symbol, "timeframe": timeframe, "capital": capital},
                "metrics": {"total_trades": 0, "win_rate": 0, "profit_factor": 0, "max_drawdown": 0},
                "trades": [],
                "error": str(e),
            }

    def get_history(self) -> list:
        return list(self._history)


backtest_engine = BacktestEngine()