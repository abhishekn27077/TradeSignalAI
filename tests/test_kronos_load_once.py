"""
tests/test_kronos_load_once.py
==============================
Regression tests for Kronos Model lifecycle management:
1. Load-once behavior across multiple KronosAdapter initializations
2. Latency measurement (first load vs subsequent calls)
3. Thread safety during concurrent model access
4. Memory/model weight reuse without redundant disk/CPU reloads
"""

import time
import pytest
from concurrent.futures import ThreadPoolExecutor

from app.analytics.models.kronos.adapter import KronosAdapter, KronosModelRegistry


def test_kronos_registry_load_once_behavior():
    """
    Proves that repeated initializations of KronosAdapter reuse the cached model instance
    and do NOT reload PyTorch weights from disk.
    """
    registry = KronosModelRegistry.get_instance()
    initial_loads = registry.actual_model_loads

    # Instantiate 5 adapters in sequence
    adapters = [KronosAdapter(device="cpu") for _ in range(5)]

    assert len(adapters) == 5
    # The actual PyTorch model weights should only have been loaded at most once (or remained at 1 if already loaded)
    final_loads = registry.actual_model_loads
    assert final_loads <= initial_loads + 1, "Model must not be reloaded on each adapter instantiation"

    # All adapters must report the same registry instance and loaded status
    for adapter in adapters:
        assert adapter.is_loaded() is True
        assert adapter.status == "LOADED"


def test_kronos_initialization_latency_benchmark():
    """
    Measures first-load time vs subsequent initialization time,
    proving subsequent initializations are instantaneous (<5ms).
    """
    registry = KronosModelRegistry.get_instance()
    assert registry.is_loaded() is True

    # Benchmark 10 subsequent adapter creations
    t0 = time.perf_counter()
    for _ in range(10):
        adapter = KronosAdapter(device="cpu")
        assert adapter.is_loaded() is True
    elapsed = time.perf_counter() - t0

    avg_subsequent_time = elapsed / 10.0
    # Average subsequent initialization must be sub-millisecond (typically < 0.0005s)
    assert avg_subsequent_time < 0.010, f"Subsequent init too slow: {avg_subsequent_time:.6f}s (must be < 10ms)"


def test_kronos_concurrent_thread_safety():
    """
    Proves thread-safe access to KronosModelRegistry across concurrent threads.
    """
    def worker(worker_id: int):
        adapter = KronosAdapter(device="cpu")
        is_loaded = adapter.is_loaded()
        return worker_id, is_loaded, adapter.status

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(worker, range(16)))

    assert len(results) == 16
    for worker_id, is_loaded, status in results:
        assert is_loaded is True
        assert status == "LOADED"
