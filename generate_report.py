import asyncio
import sys
import os
import pandas as pd

from app.market_data.providers.tradingview import TradingViewDataProvider
from app.strategies.indicators.regime import market_regime_engine
from app.strategies.selector import strategy_selector
from app.strategies.scoring.trade_quality import trade_quality_engine
from app.risk.advanced_risk_manager import advanced_risk_manager

async def main():
    print("==================================================")
    print("OMNI-ENGINE LIVE BACKTEST & SIGNAL GENERATOR")

    print("==================================================")
    
    print("\n[1] Connecting to Data Provider (TradingView)...")
    tv = TradingViewDataProvider()
    await tv.connect()
    
    symbol = "BINANCE:BTCUSD"
    print(f"    Fetching latest 200 candles for {symbol} (1h timeframe)...")
    rates = await tv.get_rates(symbol, "1H", 200)
    
    if not rates:
        print("    ERROR: No data fetched.")
        return
        
    data = pd.DataFrame(rates)
    if 'timestamp' in data.columns:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)
    
    print(f"    Successfully fetched {len(data)} candles.")
    print(f"    Latest Price: ${data['close'].iloc[-1]:.2f}")
    
    print("\n[2] Market Regime Engine Analysis...")
    regime = market_regime_engine.analyze(data)
    print(f"    Trend: {regime['trend']}")
    print(f"    Volatility: {regime['volatility']}")
    print(f"    Regime Profile: {regime['state']}")
    
    print("\n[3] AI Strategy Selector...")
    strategies = strategy_selector.select_strategies(regime)
    print(f"    Selected Optimal Strategies based on Regime: {strategies}")
    
    print("\n[4] Risk Management Check...")
    # Mocking portfolio state for demonstration
    portfolio = {"daily_start_balance": 10000.0, "current_balance": 10200.0, "positions": []}
    can_trade = advanced_risk_manager.check_daily_drawdown(portfolio)
    print(f"    Daily Drawdown Check Passed: {can_trade}")
    
    print("\n[5] Live Signal Generation & Trade Quality Scoring...")
    print("    (Simulating signal evaluation for active strategies...)")
    
    for strat in strategies:
        print(f"\n    >> Analyzing {strat} conditions...")
        
        signal_context = {
            "strategy": strat,
            "trend_aligned": True if regime['trend'] in ["STRONG_BULLISH", "BULLISH", "STRONG_BEARISH", "BEARISH"] else False,
            "bos": True,
            "choch": False,
            "liquidity_sweep": True if regime['volatility'] in ["HIGH_VOLATILITY", "EXPANDING"] else False,
            "ob_quality": 0.85,
            "fvg_quality": 0.90,
            "strong_momentum": True if regime['trend'].startswith("STRONG") else False,
            "high_impact_news": False,
            "bad_session": False,
            "high_spread": False,
            "risk_reward": 3.0,
            "ai_confidence": 0.88
        }
        
        score, grade = trade_quality_engine.evaluate(signal_context)
        print(f"       AI Confidence Score: {score}/100")
        print(f"       Trade Quality Grade: {grade}")
        
        if grade in ["A+", "A", "B+", "B"]:
            print(f"       [AUTHORIZED] LIVE SIGNAL: {strat} on {symbol}")
            print(f"          Action: {'BUY' if 'BULLISH' in regime['trend'] else 'SELL' if 'BEARISH' in regime['trend'] else 'WAIT'}")
            print(f"          Risk/Reward: 3.0R")
        else:
            print(f"       [REJECTED] SIGNAL: Did not meet minimum quality threshold.")
            
    print("\n==================================================")
    print("Report complete.")

if __name__ == "__main__":
    asyncio.run(main())
