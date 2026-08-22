"""
Market Intelligence Configuration
===================================
Central configuration for symbols, timeframes, history targets, and download parameters.
All values are overridable via Settings / .env.
"""

from dataclasses import dataclass, field

# ── Timeframe definitions ────────────────────────────────────────────────────

VALID_TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]

TIMEFRAME_MINUTES = {
    "M1": 1, "M5": 5, "M15": 15, "M30": 30,
    "H1": 60, "H4": 240, "D1": 1440, "W1": 10080,
}


# ── Default history targets (in days) ────────────────────────────────────────

DEFAULT_HISTORY_TARGETS: dict[str, dict[str, int]] = {
    "forex": {
        "M1": 90,       # 3 months
        "M5": 180,      # 6 months
        "M15": 365,     # 12 months
        "H1": 730,      # 24 months
        "H4": 1825,     # 5 years
        "D1": 3650,     # 10 years
    },
    "crypto": {
        "M1": 90,
        "M5": 365,
        "M15": 730,
        "H1": 1825,
        "H4": 3650,
        "D1": 3650,     # Maximum available
    },
    "indices": {
        "M15": 365,
        "H1": 1825,
        "H4": 1825,
        "D1": 3650,
    },
    "commodities": {
        "M15": 365,
        "H1": 1825,
        "H4": 1825,
        "D1": 3650,
    },
}


# ── Default symbols per asset class ──────────────────────────────────────────

DEFAULT_SYMBOLS: dict[str, list[dict[str, str]]] = {
    "forex": [
        {"symbol": "EURUSD", "base": "EUR", "quote": "USD", "pip_size": "0.0001"},
        {"symbol": "GBPUSD", "base": "GBP", "quote": "USD", "pip_size": "0.0001"},
        {"symbol": "USDJPY", "base": "USD", "quote": "JPY", "pip_size": "0.01"},
        {"symbol": "AUDUSD", "base": "AUD", "quote": "USD", "pip_size": "0.0001"},
        {"symbol": "USDCHF", "base": "USD", "quote": "CHF", "pip_size": "0.0001"},
        {"symbol": "USDCAD", "base": "USD", "quote": "CAD", "pip_size": "0.0001"},
        {"symbol": "NZDUSD", "base": "NZD", "quote": "USD", "pip_size": "0.0001"},
        {"symbol": "EURGBP", "base": "EUR", "quote": "GBP", "pip_size": "0.0001"},
        {"symbol": "EURJPY", "base": "EUR", "quote": "JPY", "pip_size": "0.01"},
        {"symbol": "GBPJPY", "base": "GBP", "quote": "JPY", "pip_size": "0.01"},
    ],
    "crypto": [
        {"symbol": "BTCUSDT", "base": "BTC", "quote": "USDT", "pip_size": "0.01"},
        {"symbol": "ETHUSDT", "base": "ETH", "quote": "USDT", "pip_size": "0.01"},
        {"symbol": "BNBUSDT", "base": "BNB", "quote": "USDT", "pip_size": "0.01"},
        {"symbol": "SOLUSDT", "base": "SOL", "quote": "USDT", "pip_size": "0.01"},
        {"symbol": "XRPUSDT", "base": "XRP", "quote": "USDT", "pip_size": "0.0001"},
    ],
    "indices": [
        {"symbol": "SPX500", "base": "SPX", "quote": "USD", "pip_size": "0.01"},
        {"symbol": "NAS100", "base": "NDX", "quote": "USD", "pip_size": "0.01"},
        {"symbol": "US30", "base": "DJI", "quote": "USD", "pip_size": "1.0"},
    ],
    "commodities": [
        {"symbol": "XAUUSD", "base": "XAU", "quote": "USD", "pip_size": "0.01"},
        {"symbol": "XAGUSD", "base": "XAG", "quote": "USD", "pip_size": "0.001"},
        {"symbol": "USOIL", "base": "CL", "quote": "USD", "pip_size": "0.01"},
    ],
}


# ── Default timeframes to download per asset class ───────────────────────────

DEFAULT_TIMEFRAMES: dict[str, list[str]] = {
    "forex": ["M5", "M15", "H1", "H4", "D1"],
    "crypto": ["M5", "M15", "H1", "H4", "D1"],
    "indices": ["M15", "H1", "H4", "D1"],
    "commodities": ["M15", "H1", "H4", "D1"],
}


# ── Trading session schedule (UTC) ──────────────────────────────────────────

TRADING_SESSIONS = {
    "Asian":    {"start": "00:00", "end": "08:00"},
    "London":   {"start": "08:00", "end": "16:00"},
    "New York": {"start": "13:00", "end": "22:00"},
    "Sydney":   {"start": "22:00", "end": "06:00"},
}


def get_session_for_hour(hour: int) -> str:
    """Determine trading session from UTC hour."""
    if 0 <= hour < 8:
        return "Asian"
    elif 8 <= hour < 13:
        return "London"
    elif 13 <= hour < 22:
        return "New York"
    else:
        return "Sydney"


@dataclass
class DataConfig:
    """Runtime-resolved data configuration."""
    provider: str = "yfinance"
    symbols: dict[str, list[dict[str, str]]] = field(default_factory=lambda: DEFAULT_SYMBOLS.copy())
    timeframes: dict[str, list[str]] = field(default_factory=lambda: DEFAULT_TIMEFRAMES.copy())
    history_targets: dict[str, dict[str, int]] = field(default_factory=lambda: DEFAULT_HISTORY_TARGETS.copy())
    max_concurrent_downloads: int = 3
    retry_limit: int = 3
    rate_limit_per_minute: int = 30
    sync_interval_minutes: int = 15

    def get_history_days(self, asset_class: str, timeframe: str) -> int:
        """Get target history depth in days for a given asset class and timeframe."""
        targets = self.history_targets.get(asset_class, {})
        return targets.get(timeframe, 365)  # default 1 year

    def get_all_symbols_flat(self) -> list[dict[str, str]]:
        """Return flattened list of all symbols with their asset class."""
        result = []
        for asset_class, syms in self.symbols.items():
            for s in syms:
                result.append({**s, "asset_class": asset_class})
        return result


# Singleton
data_config = DataConfig()
