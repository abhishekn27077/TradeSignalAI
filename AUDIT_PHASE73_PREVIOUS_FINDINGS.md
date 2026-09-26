# Phase 73 — Previous Critical Findings Forensic Audit

**Audit Date:** 2026-09-26  
**Repository:** `TradeSignalAI-v3`  
**Git Commit:** `8b7e502`  
**Methodology:** Independent code review, file/line verification, and test execution.

---

## 1. Summary Classification Table

| Finding ID | Title | Previous Status | Current Forensic Classification | File Location | Line Number |
|:---|:---|:---|:---|:---|:---|
| **TS-001** | Global Auth Bypass / `get_current_user` | Confirmed Critical | **[PARTIALLY FIXED]** | `app/api/dependencies.py` & `app/api/v1/*.py` | `dependencies.py:16-43`, routes |
| **TS-002** | Git-History Secret Leak | Confirmed Critical | **[FIXED]** | Git repository history | Commits 1-31 |
| **TS-003** | Canonical Signal Fabricated Market Data | Confirmed Critical | **[PARTIALLY FIXED]** | `app/core/canonical_signal_service.py` | Lines 149-160, 451-454 |
| **TS-004** | Coordinator Hardcoded Account Balance | Confirmed Critical | **[FIXED]** | `app/execution/coordinator.py` | Lines 99-119 |
| **TS-005** | Risk Engine Fail-Open / TP Key Mismatch | Confirmed High | **[PARTIALLY FIXED]** | `app/risk/engine.py` | Lines 40-75 |
| **TS-006** | Paper Executor P&L Double-Counting | Confirmed High | **[FIXED]** | `app/execution/paper/executor.py` | Lines 28-37, 76-135 |
| **TS-007** | Reconciliation Engine Is a Stub | Confirmed High | **[FIXED]** | `app/execution/reconciliation.py` | Full rewrite (lines 1-336) |
| **TS-008** | SignalIdentityGuard Not Enforced | Confirmed High | **[STILL BROKEN]** | `app/core/signal_identity.py` | Lines 59-94 (Never invoked in hot path) |
| **TS-009** | Unauthenticated WebSocket Broadcast | Confirmed High | **[STILL BROKEN]** | `app/api/v1/ws.py` | Lines 272-284 |
| **TS-010** | Hardcoded API Key in Source Code | Confirmed High | **[FIXED]** | `app/auth/security.py` | Lines 80-97 |
| **TS-011** | Password Fallback Returns Plaintext | Confirmed High | **[FIXED]** | `app/auth/security.py` | Lines 24-48 |
| **TS-012** | `importlib.import_module()` Dynamic Loading | Confirmed High | **[STILL BROKEN]** | `app/strategies/plugins/registry.py` | Lines 32-42 |
| **TS-013** | Heuristic Volatility/Confidence Inversion | Confirmed Medium | **[STILL BROKEN]** | `app/agents/providers/heuristic.py` | Lines 45, 53, 65-67 |
| **TS-014** | Snapshot TTL TOCTOU Race Condition | Confirmed Medium | **[FIXED]** | `app/core/canonical_signal_service.py` | Lines 290-295 |
| **TS-015** | `datetime.utcnow()` Deprecations | Confirmed Low | **[PARTIALLY FIXED]** | Throughout `app/` | 38 occurrences remain in Ruff scan |

---

## 2. In-Depth Forensic Analysis by Finding

### TS-001: Global Authentication Bypass / Unauthenticated State-Changing Endpoints
- **Status:** **[PARTIALLY FIXED]**
- **Evidence:**
  In `app/api/dependencies.py:16-43`, `get_current_user` was rewritten to raise `HTTPException(status_code=401, detail="Not authenticated: missing token")`. It no longer returns an anonymous user dictionary.
- **Why it is only partially fixed:**
  A forensic scan of all 357 routes in `app/main.py` revealed that only **4 routes** actually attach the auth or role dependency (`/api/v1/signals/debug/inject`, `/api/v1/execution/cancel/{order_id}`, `/api/v1/enterprise/audit`, `/api/v1/enterprise/backup`).
  **61 state-changing POST/PUT/DELETE routes accept unauthenticated calls from anonymous clients**, including:
  - `POST /api/v1/system/inject_signal`
  - `POST /api/v1/agents/initialize`
  - `POST /api/v1/agents/consensus/trigger`
  - `POST /api/v1/strategies/{strategy_name}/enable`, `/disable`, `/pause`, `/resume`
  - `POST /api/v1/system-intelligence/bootstrap`
  - `POST /api/v1/signals/run-cycle`, `/replay`
  - `POST /api/v1/campaigns/start`

### TS-002: Git-History Secret Leak
- **Status:** **[FIXED]**
- **Evidence:**
  `gitleaks git --verbose` scanned all 31 commits in git history (commit `8b7e502` back to root) and found **0 leaks**.
  `gitleaks dir --verbose` scanned the 85.57 MB working directory and found **0 leaks**.
  The repository history was cleaned with `git-filter-repo` prior to publishing commit `8b7e502`. `.gitignore` correctly ignores `.env` and `*.db`.

### TS-003: Canonical Signal Fabricated Market Data
- **Status:** **[PARTIALLY FIXED]**
- **Evidence:**
  In `app/core/canonical_signal_service.py:134-173`, the engine queries `historical_candles` table in `tradesignal.db` and computes real technical scores via `_compute_real_technical_score()`.
- **Why it is only partially fixed:**
  Lines 149-160 still state:
  ```python
  if not rows or len(rows) < 10:
      base_p = ASSET_BASE_PRICES.get(asset, 100.0)
      now = datetime.now(timezone.utc)
      times = [now - timedelta(hours=i) for i in range(limit, 0, -1)]
      df = pd.DataFrame({
          'open': [base_p] * limit,
          'high': [base_p * 1.002] * limit,
          'low': [base_p * 0.998] * limit,
          'close': [base_p * 1.0005] * limit,
          'volume': [1000.0] * limit
      }, index=times)
      return df
  ```
  And line 451-452:
  ```python
  if ref_price is None:
      ref_price = ASSET_BASE_PRICES.get(asset, 100.0)
  ```
  If candle data is missing, the engine **fabricates synthetic OHLCV candles** instead of failing closed with `INSUFFICIENT_DATA`.

### TS-004: Coordinator Hardcoded Account Balance
- **Status:** **[FIXED]**
- **Evidence:**
  In `app/execution/coordinator.py:99-119`, the coordinator now reads actual balance and equity from `account_manager.accounts`:
  ```python
  from app.paper_trading.account_manager import account_manager
  accounts = list(account_manager.accounts.values())
  if accounts:
      acc = accounts[0]
      initial_balance = 100000.0
      daily_loss_pct = max(0.0, (initial_balance - acc.balance) / initial_balance * 100)
      max_equity = max(initial_balance, acc.equity)
      drawdown_pct = ((max_equity - acc.equity) / max_equity * 100) if max_equity > 0 else 0.0
  ```
  The hardcoded `daily_loss_pct: 0.0` was removed.

### TS-005: Risk Engine Fail-Open / TP Key Mismatch
- **Status:** **[PARTIALLY FIXED]**
- **Evidence:**
  In `app/risk/engine.py:40`, the key check now supports both keys:
  `take_profit = trade_proposal.get("target") or trade_proposal.get("take_profit", 0)`.
  In lines 71-75, exceptions during failsafe checks fail closed (`result["approved"] = False`).
- **Why it is only partially fixed:**
  In lines 43-61:
  `if take_profit > 0 and stop_loss > 0 and price > 0:`
  If a proposal has `stop_loss == 0` or missing SL/TP, the entire RR validation block is bypassed, and the default `result["approved"] = True` is returned! Missing SL/TP proposals are approved!

### TS-006: Paper Executor P&L Double-Counting
- **Status:** **[FIXED]**
- **Evidence:**
  In `app/execution/paper/executor.py:28-37`, strict input validation rejects non-positive quantities (`quantity <= 0`), NaN prices, and Infinite prices before state mutation.
  The short-cover balance logic was rewritten to prevent double deductions. Tests in `test_phase60_security_audit.py` pass.

### TS-007: Reconciliation Engine Stub
- **Status:** **[FIXED]**
- **Evidence:**
  In `app/execution/reconciliation.py:1-336`, the stub `internal_positions = []` was replaced with a complete 336-line reconciliation implementation:
  - Fetches internal state via `position_manager.get_all_positions_as_list()`.
  - Fetches broker state via `paper_executor.get_all_positions()`.
  - Computes `diff_positions` for `MISSING_EXTERNAL`, `MISSING_INTERNAL`, `QUANTITY_MISMATCH`.
  - Fails closed: If broker is unavailable, status is set to `UNKNOWN` (not `MATCHED`).

### TS-008: SignalIdentityGuard Not Enforced in Hot Path
- **Status:** **[STILL BROKEN]**
- **Evidence:**
  `SignalIdentityGuard` in `app/core/signal_identity.py` is defined, but a global grep across `app/` confirms it is **never invoked** in `app/execution/coordinator.py`, `app/strategies/manager.py`, or `app/core/canonical_signal_service.py`.
  Furthermore, lines 90-93 still have:
  ```python
  except Exception as e:
      logger.error(f"SignalIdentityGuard.is_duplicate error: {e}")
      return False  # FAIL-OPEN on DB error
  ```

### TS-009: Unauthenticated WebSocket
- **Status:** **[STILL BROKEN]**
- **Evidence:**
  In `app/api/v1/ws.py:280-284`:
  ```python
  if not user:
      logger.info("WebSocket connected without a valid token. Proceeding as anonymous.")
  client_id = str(uuid.uuid4())
  await ws_manager.connect(websocket, client_id)
  ```
  Anonymous clients connect, receive broadcast ticks and order updates, and can publish `symbol_changed` events directly to the system event bus.

### TS-010: Hardcoded API Key in Source Code
- **Status:** **[FIXED]**
- **Evidence:**
  In `app/auth/security.py:80-97`, `get_api_key` and `verify_role` read from `settings.VALID_API_KEYS`, which loads from `.env`. The hardcoded string `ENTERPRISE_DEV_KEY` was removed.

### TS-011: Plaintext Password Fallback
- **Status:** **[FIXED]**
- **Evidence:**
  In `app/auth/security.py:24-48`, if cryptography dependencies (`python-jose` / `passlib`) are missing, both `verify_password()` and `get_password_hash()` raise `RuntimeError` immediately. Plaintext password fallback is removed.

### TS-012: `importlib.import_module()` Dynamic Loading
- **Status:** **[STILL BROKEN]**
- **Evidence:**
  In `app/strategies/plugins/registry.py:32-42`, `os.walk(plugin_dir)` dynamically calls `importlib.import_module(full_module_name)` without validating against a cryptographically signed manifest or strict whitelist.

### TS-013: Heuristic Volatility/Confidence Inversion
- **Status:** **[STILL BROKEN]**
- **Evidence:**
  In `app/agents/providers/heuristic.py:45` and `line 53`:
  ```python
  confidence = 0.75 + (volatility * 10)
  ```
  High volatility still increases confidence.
  Lines 65-67:
  ```python
  prompt_hash = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
  hash_val = (prompt_hash % 100) / 100.0
  confidence = min(1.0, max(0.0, confidence * (0.8 + (hash_val * 0.4))))
  ```
  Confidence is modulated using the MD5 hash of the prompt string.

### TS-014: Snapshot TTL Race Condition
- **Status:** **[FIXED]**
- **Evidence:**
  In `app/core/canonical_signal_service.py:290`, `with self._lock:` is acquired before checking snapshot expiry (`if not force_refresh and self._current_snapshot is not None:`). The TOCTOU window is eliminated.

### TS-015: `datetime.utcnow()` Deprecations
- **Status:** **[PARTIALLY FIXED]**
- **Evidence:**
  `datetime.now(timezone.utc)` was introduced in several files, but static analysis with `ruff` identifies **38 remaining occurrences** of `DTZ003: call-datetime-utcnow` across `app/`.
