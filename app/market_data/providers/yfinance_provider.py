import asyncio
from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from app.logs.logger import get_logger
from app.market_data.providers.base import BaseDataProvider
from app.market_data.types import Candle, OrderBook, Timeframe

logger = get_logger(__name__)

class YFinanceDataProvider(BaseDataProvider):
    """
    Market Data Provider using yfinance.
    """

    def __init__(self):
        self._connected = True
        
        # Mapping Timeframe to yfinance intervals
        self._interval_map = {
            Timeframe.M1: "1m",
            Timeframe.M5: "5m",
            Timeframe.M15: "15m",
            Timeframe.M30: "30m",
            Timeframe.H1: "1h",
            Timeframe.H4: "1h", # yf does not have native 4h in all cases, might need to resample, but we'll try 1h and aggregate if needed, or just use 1h for simplicity if 4h fails
            Timeframe.D1: "1d",
            Timeframe.W1: "1wk",
            Timeframe.MN1: "1mo",
        }

    @property
    def name(self) -> str:
        return "yfinance"

    async def connect(self) -> bool:
        self._connected = True
        logger.info("YFinance Data Provider 'connected' (stateless).")
        return True

    async def check_health(self) -> bool:
        return True

    async def is_connected(self) -> bool:
        return self._connected

    def _format_symbol(self, symbol: str) -> str:
        # yfinance expects symbols like BTC-USD or EURUSD=X depending on asset class
        symbol = symbol.upper()
        if ":" in symbol:
            symbol = symbol.split(":")[1]
        
        yf_symbol = symbol
        if symbol == "XAUUSD" or symbol == "XAU/USD":
            yf_symbol = "GC=F"
        elif symbol == "NAS100":
            yf_symbol = "NQ=F"
        elif symbol == "SPX500":
            yf_symbol = "ES=F"
        elif symbol == "US30":
            yf_symbol = "YM=F"
        elif symbol.replace("/", "") in ["EURUSD", "GBPUSD", "USDCAD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "EURJPY", "GBPJPY"]:
            yf_symbol = f"{symbol.replace('/', '')}=X"
        elif symbol.replace("/", "") in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT", "SOLUSDT", "DOTUSDT", "BTCUSD", "ETHUSD"]:
            yf_symbol = symbol.replace("/", "").replace("USDT", "-USD").replace("USD", "-USD")
            # If it already had -USD, the replace might make it --USD, so fix that:
            yf_symbol = yf_symbol.replace("--", "-")
        return yf_symbol

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        try:
            yf_sym = self._format_symbol(symbol)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yf_sym)
            
            # Use fast_info to get the last price efficiently
            info = await loop.run_in_executor(None, getattr, ticker, "fast_info")
            if info and 'lastPrice' in info:
                ticker_data = {
                    "symbol": symbol,
                    "price": float(info['lastPrice']),
                    "volume": float(info.get('lastVolume', 0.0)),
                    "timestamp": datetime.utcnow().isoformat()
                }
                logger.debug(f"YFinance get_ticker for {symbol} returned: {ticker_data}")
                return ticker_data
            
            # Fallback to history
            df = await loop.run_in_executor(None, ticker.history, "1d")
            if df is not None and not df.empty:
                last_row = df.iloc[-1]
                ticker_data = {
                    "symbol": symbol,
                    "price": float(last_row['Close']),
                    "volume": float(last_row.get('Volume', 0.0)),
                    "timestamp": last_row.name.isoformat() if hasattr(last_row, 'name') and last_row.name else datetime.utcnow().isoformat()
                }
                return ticker_data
                
            return None
        except Exception as e:
            logger.warning(f"Failed to get ticker for {symbol} from YFinance: {e}")
            return None

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> list[dict[str, Any]]:
        try:
            yf_sym = self._format_symbol(symbol)
            
            tf_enum = None
            for t in Timeframe:
                if t.value == timeframe:
                    tf_enum = t
                    break
                    
            interval = self._interval_map.get(tf_enum, "1m")
            
            # yfinance requires start/end or period. 
            # period depends on interval
            if interval == "1m":
                period = "7d"
            elif interval in ["5m", "15m", "30m"]:
                period = "60d"
            elif interval == "1h":
                period = "730d"
            else:
                period = "10y"
                
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yf_sym)
            df = await loop.run_in_executor(None, ticker.history, period, interval)
            
            if df is None or df.empty:
                return []
                
            # Keep only the last 'count' rows
            df = df.tail(count)
            
            rates = []
            for index, row in df.iterrows():
                rates.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": index.isoformat() if isinstance(index, pd.Timestamp) else str(index),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": float(row.get('Volume', 0.0))
                })
            return rates
        except Exception as e:
            logger.warning(f"Failed to get rates for {symbol} from YFinance: {e}")
            return []

    async def get_historical_klines(self, symbol: str, interval: str, limit: int = 100) -> list[Candle]:
        rates = await self.get_rates(symbol, interval, limit)
        candles = []
        for r in rates:
            candles.append(Candle(
                symbol=r["symbol"],
                timeframe=Timeframe(r["timeframe"]),
                timestamp=pd.to_datetime(r["timestamp"]),
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                volume=r["volume"]
            ))
        return candles

    async def get_orderbook(self, symbol: str, depth: int = 10) -> OrderBook:
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bids=[],
            asks=[]
        )
