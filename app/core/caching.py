from collections.abc import Callable
from functools import wraps
from typing import Any


def cache_response(expire_seconds: int = 60):
    """
    Decorator to cache API responses.
    """
    def decorator(func: Callable) -> Callable:
        # Stub in-memory cache
        cache = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Simple stub implementation for architecture
            # Real implementation would use Redis or memcached
            return await func(*args, **kwargs)
        return wrapper
    return decorator
