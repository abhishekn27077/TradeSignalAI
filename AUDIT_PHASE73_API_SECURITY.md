# Phase 73 — API Security Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **MEDIUM / HIGH RISK (UNPROTECTED STATE-CHANGING ENDPOINTS & PERMISSIVE CORS)**

---

## 1. Executive Summary

A non-destructive forensic security assessment was performed across all 357 HTTP and WebSocket endpoints to evaluate injection risks, CORS policies, rate limiting, and parameter handling.

---

## 2. API Security Evaluation Matrix

| Security Vector | Implementation / Policy | Forensic Finding | Risk Severity |
|:---|:---|:---|:---:|
| **Authentication Coverage** | Route-level dependencies | **98.9% of endpoints unauthenticated** | **CRITICAL** |
| **CORS Configuration** | `app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True)` | In development, `ALLOWED_ORIGINS=["*"]` allows any origin with credentials | **HIGH** |
| **Rate Limiting** | `RateLimitMiddleware` (60 req/min) | Bypasses `127.0.0.1`, `localhost`, `::1`, `testclient` | **MEDIUM** |
| **SQL Injection** | SQLAlchemy ORM & parameterized raw queries | Parameterized queries with `?` or `:params` across SQL statements | **LOW / PASS** |
| **Command Injection** | No `subprocess.Popen(shell=True)` or `os.system` calls in API routes | Clean | **PASS** |
| **Path Traversal** | File download endpoints in `data.py` | Validates symbol against `asset_registry` | **LOW / PASS** |
| **Request Logging & Redaction** | `RequestLoggingMiddleware` | Redacts Authorization headers and password fields | **PASS** |
| **Security Headers** | `SecurityHeadersMiddleware` | Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block` | **PASS** |
| **WebSocket Access Control** | `app/api/v1/ws.py` | Anonymous connections permitted; allows topic subscription and event publishing | **HIGH** |

---

## 3. Detailed Security Vulnerabilities

### 3.1 Unauthenticated Signal Injection (`/api/v1/system/inject_signal`)
- **Method:** `POST`
- **Location:** `app/api/v1/health.py` / `system.py`
- **Risk:** Allows an unauthenticated attacker to inject fabricated signals into the system event bus, triggering consensus evaluation and potential simulated trade execution.

### 3.2 Strategy Manipulation Endpoints
- **Endpoints:**
  - `POST /api/v1/strategies/{strategy_name}/enable`
  - `POST /api/v1/strategies/{strategy_name}/disable`
  - `POST /api/v1/strategies/{strategy_name}/pause`
  - `POST /api/v1/strategies/{strategy_name}/resume`
  - `PUT /api/v1/strategies/{strategy_name}/config`
- **Risk:** Without authentication, an adversary can disable defensive strategies or manipulate risk configurations.

### 3.3 Permissive CORS in Settings
In `app/config/settings.py:34`:
```python
ALLOWED_ORIGINS: list[str] = ["*"]
```
When `allow_credentials=True` is combined with `allow_origins=["*"]`, standard browsers block wildcard credentials per CORS specification. In production, `ALLOWED_ORIGINS` must be set to explicit trusted frontend domains.

---

## 4. Remediation Required
1. Enforce global authentication on all API routes except public health checks.
2. Configure explicit trusted domain origins for CORS in production.
3. Reject anonymous WebSocket connections.
4. Remove test/debug endpoints (`/api/v1/system/inject_signal`, `/debug/inject`) from production builds.
