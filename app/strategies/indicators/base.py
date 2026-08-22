from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseIndicator(ABC):
    """
    Abstract Base Class for all indicators.
    Required by Phase 5 Master Architecture.
    """
    def __init__(self, name: str, params: dict[str, Any] = None):
        self.name = name
        self.params = params or {}
        self.is_initialized = False

    @abstractmethod
    def initialize(self):
        """Setup initial state if needed."""
        self.is_initialized = True

    @abstractmethod
    def update(self, new_data: pd.DataFrame):
        """Update indicator with new streaming data incrementally if supported."""

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Perform the full calculation over a dataset."""

    @abstractmethod
    def validate(self) -> bool:
        """Ensure parameters and data are valid for this indicator."""

    @abstractmethod
    def reset(self):
        """Clear state."""
        self.is_initialized = False
