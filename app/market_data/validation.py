import logging
from datetime import datetime, timezone

from app.market_data.types import Candle, Tick

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Ensures market data quality by checking for anomalies, negative prices, and bad timestamps.
    """
    
    @staticmethod
    def validate_tick(tick: Tick) -> bool:
        if tick.price <= 0:
            logger.warning(f"Validation failed: Negative or zero price for {tick.symbol}")
            return False
        if tick.timestamp > datetime.now(timezone.utc):
            # Slight drift might be acceptable, but strict validation for future timestamps
            logger.warning(f"Validation failed: Future timestamp for {tick.symbol} tick")
            return False
        return True

    @staticmethod
    def validate_candle(candle: Candle) -> bool:
        if any(p <= 0 for p in [candle.open, candle.high, candle.low, candle.close]):
            logger.warning(f"Validation failed: Negative price in candle for {candle.symbol}")
            return False
        if candle.high < candle.low:
            logger.warning(f"Validation failed: High < Low in candle for {candle.symbol}")
            return False
        return True

class DataNormalizer:
    """
    Standardizes data formats across different providers.
    """
    
    @staticmethod
    def normalize_symbol(symbol: str, exchange: str = "GENERIC") -> str:
        """
        Convert exchange-specific symbols to internal standard.
        Example: BINANCE:BTCUSDT -> BTC-USD
        """
        symbol = symbol.upper()
        if exchange == "BINANCE" and symbol.endswith("USDT"):
            return symbol.replace("USDT", "-USD")
        if "/" in symbol:
            return symbol.replace("/", "-")
        return symbol

class GapDetector:
    """
    Detects missing candles or gaps in tick sequences.
    """
    
    @staticmethod
    def detect_missing_candles(last_candle: Candle, current_candle: Candle, expected_interval_seconds: int) -> bool:
        """
        Returns True if a gap exists between the last candle and the current one.
        """
        delta = (current_candle.timestamp - last_candle.timestamp).total_seconds()
        # Allow a small margin (e.g., 5 seconds) for network jitter
        if delta > (expected_interval_seconds + 5):
            logger.warning(f"Gap detected in {current_candle.symbol} candles. Delta: {delta}s")
            return True
        return False
