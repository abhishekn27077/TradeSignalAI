"""
app/analytics/correlation_defense_engine.py
===========================================
Empirical Feature Correlation & Double-Counting Defense Engine (Phase 71).

Computes empirical correlation matrices across technical, SMC, volatility, and volume indicators.
Calculates Effective Independent Evidence Degrees of Freedom (N_eff) via Eigenvalue Decomposition
to mathematically prevent collinear indicators from artificially inflating model consensus.
"""

from __future__ import annotations
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from app.strategies.Technical.indicators import compute_rsi, compute_macd, compute_atr
from app.strategies.Technical.supertrend import compute_supertrend
from app.strategies.indicators.indicator_registry import indicator_registry, IndicatorFamily

logger = logging.getLogger("correlation_defense_engine")


class CorrelationDefenseEngine:
    """
    Mathematical defense against collinearity and double-counting in multi-factor consensus.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        for candidate in [self.db_path, "trading_fallback.db", "app/database/trading_fallback.db"]:
            if os.path.exists(candidate):
                try:
                    return sqlite3.connect(candidate, timeout=30.0, check_same_thread=False)
                except Exception:
                    pass
        return None

    def compute_empirical_correlation_matrix(self, symbol: str = "EURUSD", timeframe: str = "1h", limit: int = 500) -> Dict[str, Any]:
        """
        Extracts real historical features from SQLite candles and computes empirical correlation matrix.
        """
        conn = self._get_connection()
        if not conn:
            return {"success": False, "error": "Database unavailable"}
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_candles
                WHERE symbol = ? AND timeframe IN (?, ?, ?)
                ORDER BY timestamp ASC LIMIT ?
                """,
                (symbol, timeframe, timeframe.upper(), timeframe.lower(), limit)
            )
            rows = cur.fetchall()
            if not rows or len(rows) < 50:
                # Fallback to general symbol query
                cur.execute(
                    """
                    SELECT timestamp, open, high, low, close, volume
                    FROM historical_candles
                    WHERE symbol = ?
                    ORDER BY timestamp ASC LIMIT ?
                    """,
                    (symbol, limit)
                )
                rows = cur.fetchall()

            if not rows or len(rows) < 30:
                return {"success": False, "error": "Insufficient candle depth"}

            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna().reset_index(drop=True)

            # Extract Indicator Feature Time Series
            close = df['close']
            rsi = compute_rsi(df, period=14).fillna(50.0)
            _, _, macd_hist = compute_macd(df, fast=12, slow=26, signal=9)
            macd_hist = macd_hist.fillna(0.0)
            atr = compute_atr(df, period=14).fillna(0.0010)
            atr_ratio = (atr / close).fillna(0.0010)
            
            _, st_dir = compute_supertrend(df, period=10, multiplier=3.0)
            ema20 = close.ewm(span=20, adjust=False).mean()
            ema50 = close.ewm(span=50, adjust=False).mean()
            ema_slope = ((ema20 - ema50) / close).fillna(0.0)
            
            # Bollinger Width
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std().fillna(0.0010)
            bb_width = ((std20 * 4.0) / sma20).fillna(0.01)

            # Feature DataFrame
            feature_df = pd.DataFrame({
                "RSI_14": rsi,
                "MACD_Hist": macd_hist,
                "SuperTrend_Dir": st_dir,
                "EMA_Trend_Slope": ema_slope,
                "ATR_Ratio": atr_ratio,
                "BB_Width": bb_width,
            }).dropna()

            if len(feature_df) < 10:
                return {"success": False, "error": "Feature computation produced empty series"}

            # Pearson Correlation Matrix
            corr_df = feature_df.corr().fillna(0.0)
            corr_matrix = corr_df.round(3).to_dict()

            # Eigenvalue Decomposition for Effective Degrees of Freedom (N_eff)
            corr_values = corr_df.values
            corr_values = np.nan_to_num((corr_values + corr_values.T) / 2.0, nan=0.0)
            np.fill_diagonal(corr_values, 1.0)
            
            eigenvalues = np.linalg.eigvalsh(corr_values)
            eigenvalues = np.maximum(eigenvalues, 1e-6)
            
            # Bretherton et al. Effective Degrees of Freedom formula:
            # N_eff = (sum lambda_i)^2 / sum (lambda_i^2)
            n_eff = float(round((np.sum(eigenvalues) ** 2) / np.sum(eigenvalues ** 2), 2))
            total_features = feature_df.shape[1]
            collinearity_reduction_pct = round((1.0 - (n_eff / total_features)) * 100.0, 1)

            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "sample_size": len(feature_df),
                "total_features": total_features,
                "effective_independent_features_neff": n_eff,
                "collinearity_reduction_pct": collinearity_reduction_pct,
                "correlation_matrix": corr_matrix,
                "eigenvalues": [round(float(ev), 4) for ev in sorted(eigenvalues, reverse=True)],
            }
        except Exception as e:
            logger.warning(f"Error computing correlation matrix for {symbol}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


# Global Singleton Instance
correlation_defense_engine = CorrelationDefenseEngine()
