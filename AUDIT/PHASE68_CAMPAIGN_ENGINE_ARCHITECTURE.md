# AUDIT: PHASE 68 PROSPECTIVE CAMPAIGN ENGINE ARCHITECTURE
**System:** TradeSignalAI-v3  
**Module:** `app/runtime/prospective_campaign_engine.py`  
**Active Campaign:** `CAMPAIGN-PROSPECTIVE-2026-v1`  
**Configuration Master Hash:** `79a4f8e12b79310d`  
**Git Anchor:** `94d5efa`  

---

## 1. Campaign Lifecycle & State Machine

```
              +-------------+
              |   CREATED   |
              +-------------+
                     |
                     v
              +-------------+   pause()    +-------------+
              |   ACTIVE    | <----------> |   PAUSED    |
              +-------------+   resume()   +-------------+
                     |
                     +------------------------+
                     |                        |
                     v                        v
              +-------------+          +-------------+
              |  COMPLETED  |          |   ABORTED   |
              +-------------+          +-------------+
```

### State Machine Rules:
- **`CREATED`:** Initialized with frozen `policy_version`, `model_version`, `config_hash`, `git_commit`.
- **`ACTIVE`:** Currently accumulating forward prospective signals and paper positions.
- **`PAUSED`:** Signal generation temporarily halted with documented `pause_reason`.
- **`COMPLETED`:** Formally sealed upon reaching objective horizon without errors.
- **`ABORTED`:** Terminated due to policy change, severe drift, or critical data failure.

---

## 2. Freeze Invariants & Database Schema

The SQLite schema preserves complete tamper-proof metadata:

```sql
CREATE TABLE IF NOT EXISTS prospective_campaigns (
    campaign_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    policy_version TEXT NOT NULL,
    model_version TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    snapshot_version TEXT NOT NULL,
    campaign_objective TEXT NOT NULL,
    total_signals_generated INTEGER NOT NULL,
    total_signals_resolved INTEGER NOT NULL,
    total_realized_net_r REAL NOT NULL,
    current_win_rate_pct REAL NOT NULL,
    current_drawdown_r REAL NOT NULL,
    pause_reason TEXT
);

CREATE TABLE IF NOT EXISTS campaign_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    payload TEXT NOT NULL,
    FOREIGN KEY(campaign_id) REFERENCES prospective_campaigns(campaign_id)
);
```
