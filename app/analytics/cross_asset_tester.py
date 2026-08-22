import random


class SyntheticDataGenerator:
    ASSET_PROFILES = {
        "BTC": {"volatility": 0.05, "trend_bias": 0.001, "base_price": 60000},
        "ETH": {"volatility": 0.06, "trend_bias": 0.0012, "base_price": 3000},
        "SOL": {"volatility": 0.08, "trend_bias": 0.002, "base_price": 150},
        "EURUSD": {"volatility": 0.005, "trend_bias": 0.00001, "base_price": 1.10},
        "GBPUSD": {"volatility": 0.006, "trend_bias": 0.00001, "base_price": 1.25},
        "XAUUSD": {"volatility": 0.015, "trend_bias": 0.0005, "base_price": 2300},
        "NASDAQ": {"volatility": 0.012, "trend_bias": 0.0008, "base_price": 18000},
        "SP500": {"volatility": 0.01, "trend_bias": 0.0005, "base_price": 5200}
    }

    @staticmethod
    def generate_series(asset: str, bars: int = 1000) -> list[float]:
        profile = SyntheticDataGenerator.ASSET_PROFILES.get(asset, SyntheticDataGenerator.ASSET_PROFILES["BTC"])
        price = profile["base_price"]
        series = [price]
        for _ in range(bars - 1):
            change = random.gauss(profile["trend_bias"], profile["volatility"])
            price = price * (1 + change)
            series.append(price)
        return series
