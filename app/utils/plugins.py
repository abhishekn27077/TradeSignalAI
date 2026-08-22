import importlib
import inspect
import logging
from typing import Any

logger = logging.getLogger(__name__)

class PluginRegistry:
    """
    Dynamically loads and registers modules/plugins.
    Enables loosely coupled architecture for Strategies, Agents, etc.
    """
    def __init__(self):
        # Maps plugin_type -> { plugin_name -> PluginClass/Instance }
        self._registry: dict[str, dict[str, Any]] = {}

    def register(self, plugin_type: str, plugin_name: str, plugin: Any):
        """
        Register a specific plugin into the registry.
        """
        if plugin_type not in self._registry:
            self._registry[plugin_type] = {}
            
        if plugin_name in self._registry[plugin_type]:
            logger.warning(f"Plugin {plugin_name} of type {plugin_type} is already registered. Overwriting.")
            
        self._registry[plugin_type][plugin_name] = plugin
        logger.info(f"Registered {plugin_type} plugin: {plugin_name}")

    def get_plugin(self, plugin_type: str, plugin_name: str) -> Any:
        """Retrieve a registered plugin."""
        return self._registry.get(plugin_type, {}).get(plugin_name)

    def load_from_module(self, module_path: str, plugin_type: str, base_class: type):
        """
        Dynamically scan a module and register classes that inherit from base_class.
        Example: load_from_module('app.strategies.price_action', 'strategy', BaseStrategy)
        """
        try:
            module = importlib.import_module(module_path)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, base_class) and obj is not base_class:
                    self.register(plugin_type, name, obj)
        except ImportError as e:
            logger.error(f"Failed to load plugins from module {module_path}: {e}")

# Global singleton plugin registry
plugin_registry = PluginRegistry()
