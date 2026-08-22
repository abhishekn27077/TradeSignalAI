
class PluginLoader:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.loaded_plugins: list[str] = []

    def load_all(self) -> list[str]:
        """
        Dynamically load plugins from the plugins directory.
        """
        # Stub logic: pretend we loaded some
        self.loaded_plugins = ["new_indicator_v1", "custom_broker_adapter"]
        return self.loaded_plugins

    def get_status(self) -> dict:
        return {
            "plugins_enabled": True,
            "active_plugins": self.loaded_plugins,
            "count": len(self.loaded_plugins)
        }

plugin_loader = PluginLoader()
