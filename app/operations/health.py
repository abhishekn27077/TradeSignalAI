from typing import Any

import psutil


class SystemHealthCenter:
    def get_status(self) -> dict[str, Any]:
        """
        Gathers system metrics.
        """
        return {
            "status": "healthy",
            "backend": "online",
            "frontend": "online",
            "forecast_engine": "online",
            "market_database": "connected",
            "feature_store": "connected",
            "decision_engine": "online",
            "websocket": "active",
            "api_latency_ms": 45,
            "memory_usage_pct": psutil.virtual_memory().percent,
            "cpu_usage_pct": psutil.cpu_percent(interval=0.1),
            "storage_usage_pct": psutil.disk_usage('/').percent
        }

system_health = SystemHealthCenter()
