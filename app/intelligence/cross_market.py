import pandas as pd
import numpy as np
try:
    import yfinance as yf
except ImportError:
    yf = None
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.logs.logger import get_logger

logger = get_logger(__name__)

class CrossMarketEngine:
    """
    Phase 19: Cross-Market Intelligence (Real Data)
    Analyzes cross-market relationships as contextual evidence using yfinance.
    """
    def __init__(self):
        self._cache = {}
        self._last_fetch = None
        # Core macro symbols to track for cross-market relationships
        self.macro_symbols = {
            "DXY": "DX-Y.NYB",    # US Dollar Index
            "US10Y": "^TNX",      # US 10-Year Treasury Yield
            "SPX500": "^GSPC",    # S&P 500
            "NAS100": "^IXIC",    # NASDAQ
            "GOLD": "GC=F",       # Gold Futures
            "VIX": "^VIX"         # Volatility Index
        }

    def _fetch_macro_data(self) -> pd.DataFrame:
        now = datetime.utcnow()
        if self._last_fetch and (now - self._last_fetch).total_seconds() < 3600 and not self._cache.empty:
            return self._cache

        if yf is None:
            return pd.DataFrame()

        try:
            logger.info("Fetching real macro cross-market data via yfinance...")
            # Fetch 60 days of daily data for correlation calculation
            tickers = list(self.macro_symbols.values())
            df = yf.download(tickers, period="60d", interval="1d", progress=False)
            
            if 'Close' in df.columns:
                df = df['Close']
            
            # Rename columns back to our standard keys
            rename_map = {v: k for k, v in self.macro_symbols.items()}
            df = df.rename(columns=rename_map)
            
            # Forward fill any missing days
            df.ffill(inplace=True)
            self._cache = df
            self._last_fetch = now
            return df
        except Exception as e:
            logger.error(f"Failed to fetch cross-market data: {e}")
            if not isinstance(self._cache, pd.DataFrame):
                return pd.DataFrame()
            return self._cache

    def analyze_correlations(self, asset: str, direction: str) -> Dict[str, Any]:
        """
        Mathematically derive if the current macro environment supports or contradicts the trade.
        """
        contradictions = []
        supporting = []
        
        df = self._fetch_macro_data()
        if df.empty or len(df) < 5:
            return {
                "supporting_evidence": [],
                "contradicting_evidence": ["Cross-market data unavailable."],
                "has_contradiction": False
            }

        # Calculate recent momentum (5-day return)
        recent_returns = (df.iloc[-1] - df.iloc[-5]) / df.iloc[-5]
        
        # Analyze USD pairs (e.g. EURUSD, GBPUSD, XAUUSD)
        if "USD" in asset and asset.endswith("USD"):
            dxy_momentum = recent_returns.get("DXY", 0)
            us10y_momentum = recent_returns.get("US10Y", 0)
            
            if direction == "BUY":
                # Expecting USD to be weak (DXY falling)
                if dxy_momentum > 0.005:
                    contradictions.append(f"DXY is currently rising ({dxy_momentum:.2%}), contradicting a long position against USD.")
                elif dxy_momentum < -0.005:
                    supporting.append(f"DXY is falling ({dxy_momentum:.2%}), supporting a long position against USD.")
                    
                if us10y_momentum > 0.02:
                    contradictions.append(f"US 10Y Yields are rising sharply ({us10y_momentum:.2%}), often strengthening USD.")
            else: # SELL
                if dxy_momentum < -0.005:
                    contradictions.append(f"DXY is currently falling ({dxy_momentum:.2%}), contradicting a short position against USD.")
                elif dxy_momentum > 0.005:
                    supporting.append(f"DXY is rising ({dxy_momentum:.2%}), supporting a short position against USD.")
                    
        # Analyze Indices (SPX500, NAS100)
        elif asset in ["SPX500", "NAS100"]:
            vix_momentum = recent_returns.get("VIX", 0)
            
            if direction == "BUY":
                if vix_momentum > 0.05:
                    contradictions.append(f"VIX is spiking ({vix_momentum:.2%}), indicating risk-off sentiment.")
                elif vix_momentum < -0.05:
                    supporting.append(f"VIX is dropping ({vix_momentum:.2%}), supporting risk-on equity longs.")
            else:
                if vix_momentum < -0.05:
                    contradictions.append(f"VIX is dropping ({vix_momentum:.2%}), indicating risk-on sentiment which contradicts shorts.")
                elif vix_momentum > 0.05:
                    supporting.append(f"VIX is spiking ({vix_momentum:.2%}), supporting risk-off equity shorts.")

        return {
            "supporting_evidence": supporting,
            "contradicting_evidence": contradictions,
            "has_contradiction": len(contradictions) > 0
        }

cross_market_engine = CrossMarketEngine()
