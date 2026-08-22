import importlib
import inspect
import os

from app.logs.logger import get_logger
from app.strategies.strategy_engine.core import BaseStrategy
from app.strategies.strategy_engine.metadata import (
    StrategyCategory,
    StrategyMetadata,
    StrategyStatus,
)

logger = get_logger(__name__)


STRATEGY_METADATA_MAP: dict[str, StrategyMetadata] = {}


def register_strategy_metadata(name: str, metadata: StrategyMetadata):
    STRATEGY_METADATA_MAP[name] = metadata


class StrategyRegistry:
    def __init__(self):
        self._strategies: dict[str, type[BaseStrategy]] = {}

    def load_plugins(self, plugin_dir: str = "app/strategies"):
        logger.info(f"Scanning for strategy plugins in {plugin_dir}...")
        for root, dirs, files in os.walk(plugin_dir):
            if "__pycache__" in root:
                continue
            norm_root = os.path.normpath(root)
            base_module = norm_root.replace(os.sep, ".")
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = file[:-3]
                    full_module_name = f"{base_module}.{module_name}"
                    try:
                        module = importlib.import_module(full_module_name)
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                                self._strategies[obj.__name__] = obj
                                logger.info(f"Loaded Strategy Plugin: {obj.__name__}")
                                if obj.__name__ not in STRATEGY_METADATA_MAP:
                                    metadata = getattr(obj, 'metadata', None)
                                    if metadata is None and hasattr(obj, 'get_default_metadata'):
                                        metadata = obj.get_default_metadata()
                                    if metadata is None:
                                        metadata = StrategyMetadata(
                                            name=obj.__name__,
                                            description=f"{obj.__name__} - auto-registered strategy",
                                            category=StrategyCategory.HYBRID,
                                        )
                                    STRATEGY_METADATA_MAP[obj.__name__] = metadata
                    except Exception as e:
                        logger.debug(f"Failed to load module {full_module_name}: {e}")

    def get_strategy(self, name: str) -> type[BaseStrategy] | None:
        return self._strategies.get(name)

    def list_strategies(self) -> list[str]:
        return list(self._strategies.keys())

    def get_metadata(self, name: str) -> StrategyMetadata | None:
        return STRATEGY_METADATA_MAP.get(name)

    def get_all_metadata(self) -> dict[str, StrategyMetadata]:
        return dict(STRATEGY_METADATA_MAP)

    def get_enabled_strategies(self) -> list[str]:
        return [name for name, meta in STRATEGY_METADATA_MAP.items()
                if meta.status == StrategyStatus.ENABLED]

    def set_status(self, name: str, status: StrategyStatus) -> bool:
        if name in STRATEGY_METADATA_MAP:
            from datetime import datetime
            meta = STRATEGY_METADATA_MAP[name]
            meta.status = status
            meta.updated_at = datetime.utcnow()
            logger.info(f"Strategy {name} status set to {status}")
            return True
        return False

    def set_priority(self, name: str, priority: int) -> bool:
        if name in STRATEGY_METADATA_MAP:
            STRATEGY_METADATA_MAP[name].priority = priority
            return True
        return False

    def set_weight(self, name: str, weight: float) -> bool:
        if name in STRATEGY_METADATA_MAP:
            STRATEGY_METADATA_MAP[name].weight = weight
            return True
        return False


strategy_registry = StrategyRegistry()
