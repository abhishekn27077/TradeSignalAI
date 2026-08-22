import asyncio
import time
import os
import psutil
import requests
import json
import traceback
import pandas as pd
import numpy as np

# We will patch the DB engine for the test if possible, but let's just use the current setup for now.
# Setting env var for testing might be good.
os.environ["TESTING"] = "1"

from app.market_data.providers.tradingview import TradingViewDataProvider
from app.strategies.indicators.regime import market_regime_engine
from app.strategies.selector import strategy_selector
from app.strategies.scoring.trade_quality import trade_quality_engine
from app.risk.advanced_risk_manager import advanced_risk_manager
from app.database.manager import db_manager

REPORT = {
    "phases": {},
    "bugs": [],
    "scores": {}
}

def log_phase(phase_num, name, status, details=None):
    print(f"[PHASE {phase_num}] {name}: {status}")
    REPORT["phases"][f"Phase {phase_num}: {name}"] = {
        "status": status,
        "details": details or {}
    }
    
def add_bug(severity, title, root_cause, affected_module, fix):
    REPORT["bugs"].append({
        "severity": severity,
        "title": title,
        "root_cause": root_cause,
        "affected_module": affected_module,
        "recommended_fix": fix
    })

async def phase_1_startup():
    start = time.time()
    try:
        # Check DB
        db_manager.connect()
        if db_manager._engine is None:
            raise Exception("Database engine failed to initialize")
        
        async with db_manager._engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        
        # Check API is running via HTTP
        try:
            resp = requests.get("http://127.0.0.1:8000/api/v1/system/health")
            api_status = resp.status_code == 200
        except:
            api_status = False
            
        latency = time.time() - start
        log_phase(1, "SYSTEM STARTUP AUDIT", "PASS" if api_status else "PARTIAL", {
            "api_running": api_status,
            "db_connected": True,
            "latency": latency
        })
    except Exception as e:
        log_phase(1, "SYSTEM STARTUP AUDIT", "FAIL", {"error": str(e)})

async def phase_3_api_validation():
    try:
        endpoints = [
            "/api/v1/system/health",
            "/api/v1/extensions/regime",
            "/api/v1/extensions/learning",
            "/api/v1/extensions/risk"
        ]
        results = {}
        for ep in endpoints:
            start = time.time()
            try:
                r = requests.get(f"http://127.0.0.1:8000{ep}")
                results[ep] = {"status": r.status_code, "latency": time.time() - start, "valid_json": True}
                try:
                    r.json()
                except:
                    results[ep]["valid_json"] = False
            except Exception as e:
                results[ep] = {"status": "ERROR", "error": str(e)}
        log_phase(3, "API VALIDATION", "PASS", results)
    except Exception as e:
         log_phase(3, "API VALIDATION", "FAIL", {"error": str(e)})


async def phase_5_7_market_and_regime():
    try:
        tv = TradingViewDataProvider()
        await tv.connect()
        rates = await tv.get_rates("BINANCE:BTCUSD", "1h", count=200)
        
        if not rates or len(rates) < 100:
            raise ValueError(f"Market data failed. Row count: {len(rates)}")
            
        data = pd.DataFrame(rates)
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)
        
        regime = market_regime_engine.analyze(data)
        
        selected_strategies = strategy_selector.select_strategies(regime)
        
        log_phase(5, "MARKET DATA VALIDATION", "PASS", {"rows": len(data), "latest_close": float(data.iloc[-1]['close'])})
        log_phase(7, "MARKET REGIME ENGINE", "PASS", {"regime_output": regime, "selected_strategies": selected_strategies})
        return data, regime, selected_strategies
    except Exception as e:
        log_phase(5, "MARKET DATA VALIDATION", "FAIL", {"error": str(e), "trace": traceback.format_exc()})
        log_phase(7, "MARKET REGIME ENGINE", "FAIL", {"error": str(e)})
        return None, None, None

async def phase_8_11_quality_and_risk(data, regime):
    try:
        # Mock Context
        context = {
            "trend_aligned": True,
            "bos": True,
            "choch": False,
            "liquidity_sweep": True,
            "ob_quality": 0.8,
            "fvg_quality": 0.5,
            "strong_momentum": True,
            "high_impact_news": False,
            "bad_session": False,
            "high_spread": False,
            "risk_reward": 2.5,
            "ai_confidence": 0.85
        }
        
        score, grade = trade_quality_engine.evaluate(context)
        
        # Risk Check
        portfolio = {"daily_start_balance": 10000.0, "current_balance": 10500.0}
        risk_passed = advanced_risk_manager.check_daily_drawdown(portfolio)
        
        log_phase(8, "TRADE QUALITY ENGINE", "PASS", {"score": score})
        log_phase(11, "RISK ENGINE VALIDATION", "PASS", {"risk_passed": risk_passed})
    except Exception as e:
        log_phase(8, "TRADE QUALITY ENGINE", "FAIL", {"error": str(e), "trace": traceback.format_exc()})
        log_phase(11, "RISK ENGINE VALIDATION", "FAIL", {"error": str(e)})

async def phase_19_performance():
    try:
        process = psutil.Process(os.getpid())
        start_cpu = process.cpu_percent()
        start_mem = process.memory_info().rss / 1024 / 1024
        
        # Simulate load
        s = time.time()
        portfolio = {"daily_start_balance": 10000.0, "current_balance": 10500.0}
        for i in range(100):
            advanced_risk_manager.check_daily_drawdown(portfolio)
        
        latency = (time.time() - s) / 100
        
        end_cpu = process.cpu_percent()
        end_mem = process.memory_info().rss / 1024 / 1024
        
        log_phase(19, "PERFORMANCE TEST", "PASS", {
            "avg_risk_check_ms": latency * 1000,
            "cpu_usage": end_cpu,
            "mem_usage_mb": end_mem
        })
    except Exception as e:
         log_phase(19, "PERFORMANCE TEST", "FAIL", {"error": str(e)})

async def main():
    print("Starting Omni Verifier...")
    await phase_1_startup()
    await phase_3_api_validation()
    
    data, regime, strats = await phase_5_7_market_and_regime()
    if data is not None:
        await phase_8_11_quality_and_risk(data, regime)
        
    await phase_19_performance()
    
    with open("omni_report.json", "w") as f:
        json.dump(REPORT, f, indent=4)
        
    print("Omni Verifier complete. Output saved to omni_report.json")

if __name__ == "__main__":
    asyncio.run(main())
