from fastapi import APIRouter
from typing import Dict, Any, List
import pandas as pd
import os
import json

router = APIRouter(prefix="/forward-validation", tags=["Forward Validation"])

ARTIFACTS_DIR = r"C:\Users\Abhis\.gemini\antigravity-ide\brain\d1f3a00e-4c5b-494d-8d0b-14018e87107f"

def _safe_read_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(ARTIFACTS_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    signals_df = _safe_read_csv("phase29_signals.csv")
    resolved_df = _safe_read_csv("phase29_resolved.csv")
    
    total_signals = len(signals_df)
    
    # Very basic placeholder logic for a real system
    return {
        "experiment_status": "FORWARD PAPER VALIDATION CONTINUES",
        "experiment_start": "2026-08-19",
        "experiment_days": 0,
        "days_remaining": 30,
        "total_signals": total_signals,
        "approved_signals": len(signals_df[signals_df.get('status') == 'APPROVED']) if 'status' in signals_df else 0,
        "rejected_signals": len(signals_df[signals_df.get('status') == 'REJECTED']) if 'status' in signals_df else 0,
        "resolved_signals": len(resolved_df[resolved_df.get('resolution_status') != 'UNRESOLVED']) if 'resolution_status' in resolved_df else 0,
        "unresolved_signals": len(resolved_df[resolved_df.get('resolution_status') == 'UNRESOLVED']) if 'resolution_status' in resolved_df else total_signals,
        "wins": 0,
        "losses": 0,
        "breakeven": 0,
        "invalidated": 0,
        "data_anomalies": 0,
        "leakage_events": 0,
        "manifest_status": "LOCKED",
        "last_signal_timestamp": signals_df['timestamp'].iloc[-1] if not signals_df.empty else None,
        "last_resolution_timestamp": None,
        "last_integrity_check": None
    }

@router.get("/ablation")
async def get_ablation() -> Dict[str, Any]:
    modes = [
        "QUANT_ONLY", "QUANT_KRONOS", "QUANT_MEMORY", "QUANT_NEWS", 
        "QUANT_EVENTS", "QUANT_CROSS_MARKET", "FULL_STACK"
    ]
    res = {}
    for mode in modes:
        res[mode] = {
            "signals": 0, "resolved": 0, "wins": 0, "losses": 0, "win_rate": None,
            "gross_return": None, "net_return": None, "expectancy": None,
            "profit_factor": None, "sharpe": None, "sortino": None, 
            "max_drawdown": None, "average_confidence": None,
            "status": "INSUFFICIENT_DATA"
        }
    return res

@router.get("/assets")
async def get_assets() -> Dict[str, Any]:
    assets = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]
    timeframes = ["H4", "D1", "W1"]
    res = {}
    for a in assets:
        res[a] = {}
        for tf in timeframes:
            res[a][tf] = {
                "signal_count": 0, "resolved_count": 0, "win_rate": None,
                "expectancy": None, "profit_factor": None, "net_return": None,
                "sharpe": None, "sortino": None, "max_drawdown": None, 
                "average_confidence": None, "status": "INSUFFICIENT_DATA"
            }
    return res

@router.get("/calibration")
async def get_calibration() -> Dict[str, Any]:
    buckets = ["50-55", "55-60", "60-65", "65-70", "70-75", "75-80", "80-85", "85+"]
    return {
        b: {
            "predicted_confidence": b,
            "actual_win_rate": None,
            "sample_count": 0,
            "average_return": None,
            "status": "INSUFFICIENT_DATA"
        } for b in buckets
    }

@router.get("/kronos")
async def get_kronos() -> Dict[str, Any]:
    return {
        "accuracy_delta": None,
        "win_rate_delta": None,
        "expectancy_delta": None,
        "profit_factor_delta": None,
        "sharpe_delta": None,
        "drawdown_delta": None,
        "net_return_delta": None,
        "verdict": "INSUFFICIENT_DATA"
    }

@router.get("/context")
async def get_context() -> Dict[str, Any]:
    modes = ["NEWS", "ECONOMIC EVENTS", "CROSS-MARKET", "CAPITOL TRADES", "LLM SYNTHESIS"]
    return {
        m: {
            "signals_vetoed": 0,
            "losses_avoided": 0,
            "wins_rejected": 0,
            "net_return_difference": None,
            "expectancy_difference": None,
            "status": "INSUFFICIENT_DATA"
        } for m in modes
    }

@router.get("/friday-monday")
async def get_friday_monday() -> Dict[str, Any]:
    categories = ["FOREX", "CRYPTO", "GOLD", "INDICES"]
    res = {}
    for c in categories:
        res[c] = {
            "sample_count": 0,
            "directional_agreement": None,
            "agreement_rate": None,
            "average_gap": None,
            "median_gap": None,
            "Monday_return": None,
            "confidence_interval": None,
            "p_value": None,
            "verdict": "INSUFFICIENT DATA"
        }
    return res

@router.get("/signals/latest")
async def get_latest_signals() -> List[Dict[str, Any]]:
    signals_df = _safe_read_csv("phase29_signals.csv")
    if signals_df.empty:
        return []
    
    # Return last 10
    latest = signals_df.tail(10).fillna("").to_dict(orient="records")
    return latest
