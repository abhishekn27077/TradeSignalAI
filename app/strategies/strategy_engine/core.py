from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.strategies.strategy_engine.types import StrategySignal


class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    Strategies ONLY generate signals and perform analysis.
    They NEVER execute trades.
    """
    def __init__(self, name: str, params: dict[str, Any] = None):
        self.name = name
        self.params = params or {}
        self.is_initialized = False

    @abstractmethod
    def initialize(self):
        """Setup indicators and state."""
        self.is_initialized = True

    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignal | None:
        """
        Main execution loop.
        Analyzes data and returns a structured StrategySignal if criteria is met, else None.
        """

    def analyze_multi_timeframe(self, symbol: str, mtf_data: dict[str, pd.DataFrame]) -> StrategySignal | None:
        """
        Phase 3: Multi-Timeframe Engine.
        Analyzes alignment across H4 (Trend), H1 (Momentum), M15 (Entry), M5 (Precision).
        Returns a StrategySignal with alignment properties embedded in `reasons` or metadata.
        Override this method in strategies that require institutional multi-timeframe alignment.
        """

    @abstractmethod
    def reset(self):
        """Clear state."""
        self.is_initialized = False
