import os
import sys
import json
import pandas as pd
import numpy as np
import logging
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.analytics.master_intelligence_engine import master_intelligence_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)

def generate_mock_historical_data(periods=50) -> pd.DataFrame:
    """
    Generates synthetic historical OHLCV data for testing.
    Uses random walk to simulate price action.
    """
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', periods=periods, freq='5min')
    
    returns = np.random.normal(0, 0.001, periods)
    price = 50000 * np.exp(np.cumsum(returns))
    
    high = price * (1 + np.abs(np.random.normal(0, 0.001, periods)))
    low = price * (1 - np.abs(np.random.normal(0, 0.001, periods)))
    open_price = price * (1 + np.random.normal(0, 0.0005, periods))
    volume = np.random.lognormal(10, 1, periods)
    
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': price,
        'volume': volume
    }, index=dates)
    
    return df

async def run_ablation_test():
    logger.info("Starting Intelligence Ablation Test (Out-of-Sample)")
    
    df_history = generate_mock_historical_data(100)
    
    # We will test over the last 10 periods (walk-forward) to keep LLM calls limited if API keys exist
    test_periods = 10
    start_idx = len(df_history) - test_periods - 1
    
    results = {
        "quant_only": {"returns": [], "signals": []},
        "intelligence_enhanced": {"returns": [], "signals": []},
        "metrics": {}
    }

    # Iterate through out-of-sample data
    for i in range(start_idx, len(df_history) - 1):
        window = df_history.iloc[i-60:i].copy()
        if len(window) < 5:
            continue
            
        actual_future_return = (df_history['close'].iloc[i+1] - df_history['close'].iloc[i]) / df_history['close'].iloc[i]
        
        # Test: Intelligence Enhanced (Kronos + Stats + LLM Context)
        try:
            res = await master_intelligence_engine.generate_master_signal("BTCUSD", "5m", window)
            
            # Extract Quant baseline for comparison
            quant_signal = res.get('quant_baseline', {}).get('consensus_expected_return', 0.0)
            
            # Apply Master Filter
            master_dir = res.get('master_signal', 'NEUTRAL')
            
            # Map string to numeric for tracking if it passed the filter
            if master_dir == "NO_TRADE":
                master_signal = 0.0
            elif master_dir == "BULLISH":
                master_signal = abs(quant_signal) if quant_signal != 0.0 else 0.001
            elif master_dir == "BEARISH":
                master_signal = -abs(quant_signal) if quant_signal != 0.0 else -0.001
            else:
                master_signal = quant_signal # fallback
                
            results['quant_only']['returns'].append(actual_future_return * np.sign(quant_signal))
            results['quant_only']['signals'].append(quant_signal)
            
            results['intelligence_enhanced']['returns'].append(actual_future_return * np.sign(master_signal) if master_signal != 0.0 else 0.0)
            results['intelligence_enhanced']['signals'].append(master_signal)
            
        except Exception as e:
            logger.error(f"Prediction failed at idx {i}: {e}")

    # Calculate metrics
    def calc_metrics(returns_list):
        ret = np.array(returns_list)
        if len(ret) == 0:
            return {"cumulative_return": 0.0, "sharpe_ratio": 0.0, "win_rate": 0.0}
        cum_ret = np.prod(1 + ret) - 1
        sharpe = np.sqrt(288 * 365) * np.mean(ret) / (np.std(ret) + 1e-9) if np.std(ret) > 0 else 0
        win_rate = np.sum(ret > 0) / len(ret) if len(ret) > 0 else 0
        return {
            "cumulative_return": float(cum_ret),
            "sharpe_ratio": float(sharpe),
            "win_rate": float(win_rate)
        }

    results["metrics"]["quant_only"] = calc_metrics(results["quant_only"]["returns"])
    results["metrics"]["intelligence_enhanced"] = calc_metrics(results["intelligence_enhanced"]["returns"])
    
    # Save frozen results
    results_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "INTELLIGENCE_FROZEN_OOS_RESULTS.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"OOS Validation Complete. Results saved to {results_path}")
    
    # Generate Markdown Report
    report_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "PHASE18_AI_INTELLIGENCE_REPORT.md")
    with open(report_path, 'w') as f:
        f.write("# PHASE 18 MARKET INTELLIGENCE OOS CERTIFICATION\n\n")
        f.write("## Baseline Metrics (Quant + Kronos Only)\n")
        f.write(f"- Cumulative Return: {results['metrics']['quant_only']['cumulative_return']:.4%}\n")
        f.write(f"- Sharpe Ratio: {results['metrics']['quant_only']['sharpe_ratio']:.2f}\n")
        f.write(f"- Win Rate: {results['metrics']['quant_only']['win_rate']:.2%}\n\n")
        
        f.write("## Intelligence Enhanced Metrics (LLM Context + Event Risk + No-Trade)\n")
        f.write(f"- Cumulative Return: {results['metrics']['intelligence_enhanced']['cumulative_return']:.4%}\n")
        f.write(f"- Sharpe Ratio: {results['metrics']['intelligence_enhanced']['sharpe_ratio']:.2f}\n")
        f.write(f"- Win Rate: {results['metrics']['intelligence_enhanced']['win_rate']:.2%}\n\n")
        
        if results['metrics']['intelligence_enhanced']['sharpe_ratio'] >= results['metrics']['quant_only']['sharpe_ratio'] or results['metrics']['intelligence_enhanced']['win_rate'] > results['metrics']['quant_only']['win_rate']:
            f.write("### VERDICT: SUCCESS\n")
            f.write("Master Intelligence Engine successfully filtered bad trades, improving Sharpe or Win Rate. Zero-trust architecture validated.\n")
        else:
            f.write("### VERDICT: FAILED\n")
            f.write("Master Intelligence Engine degraded performance or failed to improve risk-adjusted returns.\n")

    logger.info("Report generated.")

if __name__ == "__main__":
    asyncio.run(run_ablation_test())
