# Performance Report

## Overview
TradeSignalAI-v3 processes asynchronous market events via FastAPI and Python `asyncio`. 

## Bottlenecks Detected
1. **Synchronous Database Operations**: Many repository calls to SQLite/PostgreSQL are currently using synchronous `Session` objects rather than `AsyncSession`. Under high concurrent WebSocket load, this will block the event loop and degrade throughput.
2. **WebSocket Global Broadcast**: `ws_manager.broadcast` loops over all connected clients sequentially. If connections scale > 1,000, this loop will cause blocking latency. It should yield control `await asyncio.sleep(0)` or use a distributed message broker (Redis).
3. **Data Polling**: The frontend uses `setInterval` (30s) to refresh System Health and Portfolio data, which is redundant since WebSockets are already pushing these updates.

## Memory Footprint
- The `FeatureStore` loads large Pandas DataFrames into memory. While acceptable for a single asset, evaluating 50+ assets concurrently for the Heatmap could cause OOM (Out of Memory) spikes.
- **Recommendation:** Implement chunked processing or Dask for horizontal scaling of the Feature Store.

## Optimization Plan
1. **Critical:** Migrate all remaining `SessionLocal` database bindings to SQLAlchemy's `asyncio` extension.
2. **High:** Remove `setInterval` polling in React components; rely purely on the WebSocket store.
3. **Medium:** Add pagination and caching (`Redis`) to heavy endpoints like `/forecast/predictions`.
