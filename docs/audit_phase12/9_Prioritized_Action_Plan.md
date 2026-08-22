# Prioritized Action Plan

## Priority 1: Critical (Must fix before Production)
1. **Remove Local Auth Bypasses:** Remove `if api_key_header == ""` in `app.auth.security` to ensure endpoints are fully protected.
2. **Fix Pytest Configuration:** Exclude `/scratch` from `pytest.ini` and implement `pytest-asyncio` mock timeouts so CI/CD pipelines do not break on external API failures (e.g., `test_omni8.py`).
3. **Database Migrations for Phase 11:** Replace mock dictionaries in `app/strategy_lab/library.py` with SQLAlchemy models.

## Priority 2: Recommended (For institutional scale)
1. **Redis Pub/Sub for WebSockets:** Refactor `app.utils.websocket_manager` to use Redis to support multiple Uvicorn workers.
2. **Async Database Sessions:** Convert remaining synchronous `SessionLocal` references to `AsyncSession` to prevent event-loop blocking.
3. **Redis Rate Limiter:** Move `app.auth.rate_limiter` off in-memory structures to Redis.

## Priority 3: Enhancements (Nice to have)
1. **Refactor Pipeline Tracer:** Break down `pipeline_tracer.py` into smaller domain-specific modules.
2. **Remove Polling:** Remove `setInterval` in React `App.tsx` and rely exclusively on WebSocket events.
3. **Clean Up Router:** Remove commented-out Phase 6 research endpoints in `app/api/v1/router.py`.
