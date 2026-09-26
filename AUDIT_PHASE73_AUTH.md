# Phase 73 — Authentication & Authorization Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **CRITICAL ARCHITECTURAL VULNERABILITY (MISSING ROUTE-LEVEL AUTH ENFORCEMENT)**

---

## 1. Executive Summary

A forensic audit of password hashing, token creation/verification, route-level dependencies, and role enforcement was conducted.

### Core Findings
1. **Password Hashing (TS-011):** **[FIXED].** Fails closed if cryptography libraries are missing. Plaintext fallback has been eliminated.
2. **Token Verification (`get_current_user` in `dependencies.py`):** **[FIXED].** Raises HTTP 401 on missing or invalid tokens.
3. **Route Protection (TS-001):** **[CRITICAL DEFECT].** Out of **357 total API routes**, only **4 routes** require authentication. **61 state-changing endpoints accept unauthenticated requests.**
4. **WebSocket Endpoint (TS-009):** **[CRITICAL DEFECT].** Accepts unauthenticated connections from anonymous clients without rejection.

---

## 2. Authentication Architecture Verification

### 2.1 Password Hashing (`app/auth/security.py`)
- `verify_password()` and `get_password_hash()` check `if not _has_jose: raise RuntimeError(...)`.
- `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`.
- **Verdict:** Secure bcrypt implementation with fail-closed dependency guard.

### 2.2 JWT Token Issuance & Validation (`app/auth/security.py`)
- Standard HS256 JWT tokens with UTC expiration (`datetime.now(timezone.utc)`).
- Token verification checks `SECRET_KEY` and algorithm.
- If expired or altered, `verify_token()` returns `None`.

### 2.3 Dependency Fail-Closed Check (`app/api/dependencies.py`)
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```
- Missing token: Returns HTTP 401.
- Invalid token: Returns HTTP 401.
- Anonymous user fallback: **Removed**.

---

## 3. Endpoint Authorization Matrix (Forensic Scan of All 357 Routes)

| Category | Total Count | Authenticated | Unauthenticated |
|:---|:---:|:---:|:---:|
| **Total Routes in Application** | 357 | 4 (1.1%) | 353 (98.9%) |
| **State-Changing Routes (POST/PUT/DELETE)** | 65 | 4 (6.2%) | 61 (93.8%) |
| **WebSocket Endpoints** | 2 | 0 (0%) | 2 (100%) |

### The 4 Protected Routes:
1. `POST /api/v1/signals/debug/inject` -> `require_role(["admin"])`
2. `POST /api/v1/execution/cancel/{order_id}` -> `require_role(["admin", "trader"])`
3. `GET /api/v1/enterprise/audit` -> `require_role(["admin"])`
4. `POST /api/v1/enterprise/backup` -> `require_role(["admin"])`

### Critical Unprotected State-Changing Endpoints (Selection of 20 out of 61):
1. `POST /api/v1/system/inject_signal` — Injects arbitrary signals into event bus.
2. `POST /api/v1/agents/initialize` — Re-initializes trading agents.
3. `POST /api/v1/agents/consensus/trigger` — Forces consensus evaluation cycle.
4. `POST /api/v1/strategies/{strategy_name}/enable` — Activates trading strategy.
5. `POST /api/v1/strategies/{strategy_name}/disable` — Deactivates trading strategy.
6. `POST /api/v1/strategies/{strategy_name}/pause` — Pauses strategy.
7. `POST /api/v1/strategies/{strategy_name}/resume` — Resumes strategy.
8. `PUT /api/v1/strategies/{strategy_name}/config` — Overwrites strategy parameters.
9. `POST /api/v1/strategies/{strategy_name}/priority` — Alters strategy priority.
10. `POST /api/v1/system-intelligence/bootstrap` — Restarts full system intelligence bootstrap.
11. `POST /api/v1/system-intelligence/pipeline/run` — Executes pipeline run.
12. `POST /api/v1/signals/run-cycle` — Triggers signal generation cycle.
13. `POST /api/v1/signals/resolve-due` — Resolves open signals against price data.
14. `POST /api/v1/signals/replay` — Replays historical signal generation.
15. `POST /api/v1/campaigns/start` — Starts prospective trading campaign.
16. `POST /api/v1/qualification/start` — Starts model qualification run.
17. `POST /api/v1/qualification/stop` — Stops model qualification run.
18. `POST /api/v1/data/download/all` — Initiates bulk market data download.
19. `POST /api/v1/brokers/sync` — Triggers broker sync.
20. `POST /api/v1/forecast/run` — Executes forecast generation.

---

## 4. Role-Based Access Control (RBAC) Defect in `verify_role`
In `app/auth/security.py:91-97`:
```python
def verify_role(required_role: str):
    async def role_checker(api_key: str = Security(get_api_key)):
        if required_role == "admin" and api_key not in settings.VALID_API_KEYS:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return True
    return role_checker
```
- If `required_role != "admin"` (e.g. `required_role == "trader"` or `"viewer"`), the `if` check evaluates to `False`, and it **returns `True` for any API key**!
- Any valid API key is treated as having all non-admin roles without any permission mapping.

---

## 5. Remediation Required
1. Implement a **Global Authentication Middleware** in `app/main.py` that enforces authentication by default across all `/api/v1/*` routes except explicit public endpoints (`/health`, `/api/v1/auth/token`, `/docs`, `/redoc`).
2. Attach `dependencies=[Depends(get_current_user)]` or role checks to all routers in `app/api/v1/router.py`.
3. In `app/api/v1/ws.py`, close the WebSocket connection with code 1008 (Policy Violation) if a valid token is not provided.
4. Implement genuine RBAC role mapping in `verify_role()`.
