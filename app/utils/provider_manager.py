import asyncio
import datetime
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from app.logs.logger import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class ProviderState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"
    SHUTDOWN = "SHUTDOWN"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    HALF_OPEN = "HALF_OPEN"
    OPEN = "OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0, half_open_max_retries: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_retries = half_open_max_retries
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_attempts = 0
        self.last_failure_time = 0.0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")

    def record_success(self):
        self.failure_count = 0
        self.half_open_attempts = 0
        self.state = CircuitState.CLOSED

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_attempts < self.half_open_max_retries:
                self.half_open_attempts += 1
                return True
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            return False
        return True

    async def call(self, fn, *args, **kwargs):
        if not self.allow_request():
            raise ConnectionError("Circuit breaker OPEN, rejecting request")
        try:
            result = await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise


class ProviderInstance:
    def __init__(
        self,
        name: str,
        connect_fn: Callable | None = None,
        disconnect_fn: Callable | None = None,
        health_check_fn: Callable | None = None,
        heartbeat_interval: float = 30.0,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        self.name = name
        self.state = ProviderState.UNINITIALIZED
        self._connect_fn = connect_fn
        self._disconnect_fn = disconnect_fn
        self._health_check_fn = health_check_fn
        self.heartbeat_interval = heartbeat_interval
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.retry_count = 0
        self.last_state_change = datetime.datetime.utcnow()
        self.last_heartbeat = 0.0
        self._heartbeat_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._listeners: dict[str, list] = {}
        self._healthy: bool = False
        self._metadata: dict[str, Any] = {}

    def on(self, event: str, callback: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def _emit(self, event: str, **kwargs):
        for cb in self._listeners.get(event, []):
            try:
                cb(provider=self.name, state=self.state, **kwargs)
            except Exception as e:
                logger.error(f"Listener error on {self.name}/{event}: {e}")

    def _transition(self, new_state: ProviderState):
        old = self.state
        self.state = new_state
        self.last_state_change = datetime.datetime.utcnow()
        logger.info(f"Provider {self.name}: {old.value} -> {new_state.value}")
        self._emit("state_change", old_state=old, new_state=new_state)

    def is_connected(self) -> bool:
        return self.state == ProviderState.CONNECTED

    def is_available(self) -> bool:
        return self.state in (ProviderState.CONNECTED, ProviderState.DEGRADED)

    @property
    def healthy(self) -> bool:
        return self._healthy

    async def initialize(self):
        self._transition(ProviderState.INITIALIZING)
        self._transition(ProviderState.CONNECTED if self._connect_fn is None else ProviderState.CONNECTING)
        if self._connect_fn:
            await self.connect()

    async def connect(self):
        if self.state == ProviderState.SHUTDOWN:
            return
        self._transition(ProviderState.CONNECTING)
        try:
            if asyncio.iscoroutinefunction(self._connect_fn):
                await self._connect_fn()
            else:
                self._connect_fn()
            self._transition(ProviderState.CONNECTED)
            self._healthy = True
            self.retry_count = 0
            self._emit("connected")
            self._start_heartbeat()
        except Exception as e:
            self._transition(ProviderState.ERROR)
            self._healthy = False
            self._emit("connect_failed", error=str(e))
            raise

    async def disconnect(self):
        if self.state == ProviderState.SHUTDOWN:
            return
        self._stop_heartbeat()
        self._stop_reconnect()
        if self._disconnect_fn:
            try:
                if asyncio.iscoroutinefunction(self._disconnect_fn):
                    await self._disconnect_fn()
                else:
                    self._disconnect_fn()
            except Exception as e:
                logger.warning(f"Disconnect error on {self.name}: {e}")
        self._transition(ProviderState.DISCONNECTED)
        self._healthy = False

    async def shutdown(self):
        self._transition(ProviderState.SHUTDOWN)
        await self.disconnect()

    async def check_health(self) -> bool:
        if self._health_check_fn is None:
            return self._healthy
        try:
            healthy = self._health_check_fn()
            if asyncio.iscoroutine(healthy):
                healthy = await healthy
            self._healthy = bool(healthy)
            if not self._healthy and self.state == ProviderState.CONNECTED:
                self._transition(ProviderState.DEGRADED)
                self._emit("health_degraded")
            elif self._healthy and self.state == ProviderState.DEGRADED:
                self._transition(ProviderState.CONNECTED)
                self._emit("health_restored")
            return self._healthy
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            self._healthy = False
            if self.state == ProviderState.CONNECTED:
                self._transition(ProviderState.DEGRADED)
                self._emit("health_degraded")
            return False

    def _start_heartbeat(self):
        self._stop_heartbeat()
        self.last_heartbeat = time.time()

        async def _heartbeat_loop():
            while self.state not in (ProviderState.SHUTDOWN, ProviderState.DISCONNECTED):
                await asyncio.sleep(self.heartbeat_interval)
                if self.state in (ProviderState.CONNECTED, ProviderState.DEGRADED):
                    healthy = await self.check_health()
                    if not healthy and self.state == ProviderState.CONNECTED:
                        logger.warning(f"{self.name} heartbeat: unhealthy, reconnecting")
                        asyncio.ensure_future(self._reconnect_loop())

        self._heartbeat_task = asyncio.ensure_future(_heartbeat_loop())

    def _stop_heartbeat(self):
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    def _stop_reconnect(self):
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            self._reconnect_task = None

    async def _reconnect_loop(self):
        if self.state == ProviderState.RECONNECTING:
            return
        self._transition(ProviderState.RECONNECTING)
        delay = self.base_delay
        attempt = 0
        while attempt < self.max_retries and self.state not in (ProviderState.SHUTDOWN, ProviderState.CONNECTED):
            attempt += 1
            logger.info(f"{self.name} reconnect attempt {attempt}/{self.max_retries} in {delay:.1f}s")
            await asyncio.sleep(delay)
            try:
                await self.connect()
                self._emit("reconnected", attempts=attempt)
                return
            except Exception as e:
                logger.warning(f"{self.name} reconnect attempt {attempt} failed: {e}")
                delay = min(delay * 2, self.max_delay)
                self.retry_count = attempt
        if self.state != ProviderState.CONNECTED:
            logger.error(f"{self.name} failed to reconnect after {self.max_retries} attempts")
            self._transition(ProviderState.ERROR)
            self._emit("reconnect_failed", max_retries=self.max_retries)
        self._reconnect_task = None

    async def trigger_reconnect(self):
        if self.state in (ProviderState.SHUTDOWN, ProviderState.RECONNECTING):
            return
        asyncio.ensure_future(self._reconnect_loop())

    def get_status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "state": self.state.value,
            "connected": self.is_connected(),
            "available": self.is_available(),
            "healthy": self._healthy,
            "retry_count": self.retry_count,
            "circuit_state": self.circuit_breaker.state.value,
            "last_state_change": self.last_state_change.isoformat(),
            "heartbeat_interval": self.heartbeat_interval,
        }


class ProviderManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers: dict[str, ProviderInstance] = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, name: str, instance: ProviderInstance):
        self._providers[name] = instance
        logger.info(f"Registered provider: {name}")

    def get(self, name: str) -> ProviderInstance | None:
        return self._providers.get(name)

    def __getitem__(self, name: str) -> ProviderInstance:
        p = self._providers.get(name)
        if p is None:
            raise KeyError(f"Provider {name} not registered")
        return p

    async def initialize_all(self):
        self._initialized = True
        results = {}
        for name, provider in self._providers.items():
            try:
                await provider.initialize()
                results[name] = {"status": "ok", "state": provider.state.value}
            except Exception as e:
                logger.warning(f"Provider {name} initialization failed: {e}")
                results[name] = {"status": "error", "state": provider.state.value, "error": str(e)}
        return results

    async def shutdown_all(self):
        for name, provider in self._providers.items():
            try:
                await provider.shutdown()
            except Exception as e:
                logger.warning(f"Provider {name} shutdown error: {e}")

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        results = {}
        for name, provider in self._providers.items():
            healthy = await provider.check_health()
            results[name] = {"healthy": healthy, "state": provider.state.value, "connected": provider.is_connected()}
        return results

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        return {name: p.get_status() for name, p in self._providers.items()}

    async def reconnect_all(self):
        for name, provider in self._providers.items():
            if not provider.is_connected() and provider.state != ProviderState.SHUTDOWN:
                await provider.trigger_reconnect()

    @property
    def all_healthy(self) -> bool:
        return all(p.healthy for p in self._providers.values())

    @property
    def any_critical_failure(self) -> bool:
        critical = {p for p_name, p in self._providers.items() if p_name in ("database",)}
        return any(p.state == ProviderState.ERROR for p in critical)


provider_manager = ProviderManager()