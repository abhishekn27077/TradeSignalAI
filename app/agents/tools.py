from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

_TOOLS: dict[str, dict[str, Any]] = {
    "get_market_data": {
        "name": "get_market_data",
        "description": "Fetch current market data for a symbol",
        "parameters": {"symbol": {"type": "string"}},
    },
    "execute_trade": {
        "name": "execute_trade",
        "description": "Execute a trade order",
        "parameters": {
            "symbol": {"type": "string"},
            "direction": {"type": "string", "enum": ["BUY", "SELL"]},
            "quantity": {"type": "number"},
        },
    },
    "get_portfolio": {
        "name": "get_portfolio",
        "description": "Get current portfolio state",
        "parameters": {},
    },
    "get_risk_metrics": {
        "name": "get_risk_metrics",
        "description": "Get current risk metrics",
        "parameters": {},
    },
    "get_news": {
        "name": "get_news",
        "description": "Get latest news for analysis",
        "parameters": {"symbol": {"type": "string"}},
    },
    "search_memory": {
        "name": "search_memory",
        "description": "Search episodic memory for past events",
        "parameters": {"query": {"type": "string"}},
    },
}


def get_tool(name: str) -> dict[str, Any] | None:
    tool = _TOOLS.get(name)
    if tool is None:
        logger.warning(f"Unknown tool: {name}")
    return tool


def register_tool(name: str, definition: dict[str, Any]):
    _TOOLS[name] = definition


def list_tools() -> dict[str, dict[str, Any]]:
    return dict(_TOOLS)