import random
import time
from typing import Any

from app.market_data.providers.base import BaseDataProvider


class SimulatedDataProvider(BaseDataProvider):
    """
    Fallback simulated provider that generates realistic random prices.
    Supports regimes: trending, sideways, high_volatility, low_volatility, flash_crash, pump_dump
    """
    def __init__(self):
        super().__init__()
        self.regime = "trending"
        self._base_prices = {}

    @property
    def name(self) -> str:
        return "simulated"

    def set_regime(self, regime: str):
        self.regime = regime

    async def check_health(self) -> bool:
        return True

    async def is_connected(self) -> bool:
        return True

    def _get_price_delta(self) -> float:
        if self.regime == "trending":
            return random.uniform(-2, 10) # Upward bias
        elif self.regime == "sideways":
            return random.uniform(-5, 5)
        elif self.regime == "high_volatility":
            return random.uniform(-20, 20)
        elif self.regime == "low_volatility":
            return random.uniform(-1, 1)
        elif self.regime == "flash_crash":
            return random.uniform(-50, -5) # Heavy downward
        elif self.regime == "pump_dump":
            # 80% pump, 20% dump
            return random.uniform(10, 50) if random.random() < 0.8 else random.uniform(-80, -20)
        return random.uniform(-10, 10)

    async def get_ticker(self, symbol: str) -> dict[str, Any]:
        if symbol not in self._base_prices:
            self._base_prices[symbol] = 60000.0 if "BTC" in symbol else 3000.0 if "ETH" in symbol else 100.0
            
        self._base_prices[symbol] += self._get_price_delta()
        # Prevent negative prices
        self._base_prices[symbol] = max(1.0, self._base_prices[symbol])
        
        price = self._base_prices[symbol]
        spread = 0.5 if self.regime != "high_volatility" else 2.0
        
        return {
            "symbol": symbol,
            "bid": price - spread,
            "ask": price + spread,
            "last": price,
            "time": int(time.time()),
            "volume": random.uniform(1, 100 if self.regime == "high_volatility" else 10)
        }

    async def get_historical_klines(self, symbol: str, interval: str, limit: int = 100) -> list[dict[str, Any]]:
        return await self.get_rates(symbol, interval, limit)

    async def get_rates(self, symbol: str, timeframe: str, limit: int = 100) -> list[dict[str, Any]]:
        if symbol not in self._base_prices:
            self._base_prices[symbol] = 60000.0 if "BTC" in symbol else 3000.0 if "ETH" in symbol else 100.0
            
        now = int(time.time())
        rates = []
        p = self._base_prices[symbol]
        for i in range(limit):
            t = now - (limit - i) * 60
            delta = self._get_price_delta()
            p = max(1.0, p + delta)
            rates.append({
                "time": t,
                "open": p,
                "high": p + abs(delta) + random.uniform(0, 5),
                "low": max(1.0, p - abs(delta) - random.uniform(0, 5)),
                "close": p + random.uniform(-2, 2),
                "tick_volume": int(random.uniform(10, 100))
            })
        self._base_prices[symbol] = p
        return rates

    async def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        return {"bids": [], "asks": []}
