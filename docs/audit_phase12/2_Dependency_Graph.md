# Dependency Graph & Analysis

## Core Event Flow
1. `Market Data Provider` -> `Feature Store`
2. `Feature Store` -> `Forecast Engine`
3. `Forecast Engine` -> `Consensus Framework`
4. `Consensus Framework` -> `Decision Intelligence`
5. `Decision Intelligence` -> `Risk Engine`
6. `Risk Engine` -> `Opportunity Ranking`
7. `Opportunity Ranking` -> `Paper Trading Execution`
8. `Execution` -> `Journal & Memory`
9. `Journal & Memory` -> `AI Recommendation Engine`

## Tight Coupling Issues
- **`app.forecast_engine` -> `app.market_data`**: The forecast engine queries the market data directly in some places instead of subscribing to events. This creates a hard dependency.
- **`app.api.v1.ws`**: The WebSocket router subscribes to over 30 events globally. This file is monolithic and should ideally use a pub/sub router pattern.

## Recommendations
- **Decoupling Strategy**: Move direct DB queries out of the Forecast Engine and require it to receive pre-processed dataframes from the Feature Store via the Event Bus.
- **WebSocket Refactor**: Split `ws.py` into domain-specific handlers (e.g., `ws_market.py`, `ws_forecast.py`) that register to a central multiplexer.
