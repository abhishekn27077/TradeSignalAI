import asyncio
from app.market_data.registry import DataRegistry
from app.strategies.manager import StrategyManager
from app.agents.consensus.engine import ConsensusEngine
import datetime

async def test_live_signals():
    print("Initializing Data Registry...")
    registry = DataRegistry()
    await registry.initialize()

    print("Initializing Strategy Manager...")
    strategy_manager = StrategyManager()
    
    print("Fetching recent data for BINANCE:BTCUSD...")
    try:
        # We need some live data to feed into the strategy engine
        # Many brokers or market data providers in the bot might do this.
        # Let's see if we can trigger an evaluation
        from app.market_data.providers.tradingview.provider import TradingViewProvider
        tv = TradingViewProvider()
        await tv.connect()
        data = await tv.get_historical_data("BINANCE:BTCUSD", "1h", 100)
        
        print(f"Got {len(data)} candles. Running strategies...")
        
        # We can evaluate strategies manually
        for name, strategy in strategy_manager.strategies.items():
            print(f"Evaluating {name}...")
            signal = await strategy.analyze("BINANCE:BTCUSD", data)
            if signal:
                print(f"SIGNAL FOUND from {name}: {signal.direction.name} | Confidence: {signal.confidence}")
                print(f"Reasoning: {signal.reasoning}")
            else:
                print(f"No active signal from {name} at this moment.")
                
    except Exception as e:
        print(f"Error fetching data or evaluating: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_signals())
