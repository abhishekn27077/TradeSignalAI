# Phase 73 — Risk Engine & Failsafe Integrity Forensic Audit

**Audit Date:** 2026-09-26  
**Auditor:** Independent Zero-Trust Forensic Auditor  
**Repository:** `TradeSignalAI-v3`  
**Classification:** **HIGH SEVERITY FLAW IN RISK ENGINE (MISSING SL/TP APPROVED)**

---

## 1. Executive Summary

A forensic review of `app/risk/engine.py`, `app/execution/failsafe.py`, and `app/execution/coordinator.py` evaluated risk controls against malicious, malformed, and edge-case inputs.

While TS-005 partially fixed key resilience (`take_profit = trade_proposal.get("target") or trade_proposal.get("take_profit", 0)`) and failsafe exception handling now fails closed, a major vulnerability remains: **Trade proposals with missing or zero Stop Loss are approved by default**.

---

## 2. Risk Engine Implementation Analysis (`app/risk/engine.py`)

### 2.1 Missing Stop Loss / Take Profit Bypass
- **Location:** `app/risk/engine.py:24-61`
- **Code:**
  ```python
  def validate_trade(self, trade_proposal: dict[str, Any]) -> dict[str, Any]:
      result = {"approved": True, "reason": "Risk check passed", "checks": {}}
      ...
      take_profit = trade_proposal.get("target") or trade_proposal.get("take_profit", 0)
      stop_loss = trade_proposal.get("stop_loss", 0)
      
      if take_profit > 0 and stop_loss > 0 and price > 0:
          # RR calculation and validation
          ...
      # If take_profit == 0 or stop_loss == 0, the entire block is skipped!
      return result
  ```
- **Forensic Assessment:**
  If a proposal omits `stop_loss` or sets `stop_loss = 0`, the `if take_profit > 0 and stop_loss > 0 and price > 0:` condition evaluates to `False`. The check is skipped entirely. Because `result["approved"]` defaults to `True` at line 25, the trade is **approved without a stop loss**!
- **Severity:** HIGH (P0 in any live environment). Stop loss is a mandatory condition for trade execution.

### 2.2 Failsafe Exception Handling (TS-005 Fix Verified)
- **Location:** `app/risk/engine.py:71-75`
- **Code:**
  ```python
  except Exception as e:
      logger.warning(f"Failsafe check error: {e}")
      result["approved"] = False
      result["reason"] = f"Failsafe check error: {e}"
  ```
- **Forensic Assessment:** **PASS.** If failsafe checks fail, the trade is rejected (fail-closed).

---

## 3. Malformed Input Matrix & Chaos Verification

| Input Scenario | Expected Behavior | Actual Behavior in `validate_trade` | Risk Verdict |
|:---|:---|:---|:---:|
| `quantity = 150` (max=100) | Reject (`quantity exceeds max`) | Rejected (`result['approved']=False`) | **PASS** |
| `quantity = -5.0` | Reject (`negative quantity`) | **Approved (`approved=True`)** | **FAIL** |
| `quantity = 0` | Reject (`zero quantity`) | **Approved (`approved=True`)** | **FAIL** |
| `stop_loss = None` / `0` | Reject (`mandatory SL missing`) | **Approved (`approved=True`)** | **FAIL** |
| `take_profit = None` / `0` | Reject (`mandatory TP missing`) | **Approved (`approved=True`)** | **FAIL** |
| `price = NaN` / `Inf` | Reject | **Approved (skips RR check)** | **FAIL** |
| `direction = "INVALID"` | Reject | **Approved (`approved=True`)** | **FAIL** |
| Kill Switch Active | Reject | Rejected (`Kill switch active`) | **PASS** |
| Daily Loss Limit Exceeded | Reject | Evaluated in `failsafe_manager` | **PASS** |

---

## 4. Failsafe Manager & Real Balance Integration (TS-004 Verified)

In `app/execution/coordinator.py:99-119`:
The coordinator reads the real balance from `account_manager.accounts[0]`:
```python
acc = accounts[0]
initial_balance = 100000.0
daily_loss_pct = max(0.0, (initial_balance - acc.balance) / initial_balance * 100)
drawdown_pct = ((max_equity - acc.equity) / max_equity * 100) if max_equity > 0 else 0.0
```
- Kill switch triggers when daily loss exceeds `MAX_DAILY_LOSS_PCT`.
- Drawdown circuit breaker triggers when drawdown exceeds `MAX_DRAWDOWN_PCT`.

---

## 5. Remediation Required
Refactor `validate_trade` in `app/risk/engine.py` to be fail-closed by default:
```python
def validate_trade(self, trade_proposal: dict[str, Any]) -> dict[str, Any]:
    # Mandatory checks
    direction = str(trade_proposal.get("direction", "")).upper()
    if direction not in ("BUY", "SELL"):
        return {"approved": False, "reason": "Invalid direction", "checks": {}}
        
    quantity = trade_proposal.get("quantity", 0)
    if quantity <= 0 or math.isnan(quantity) or math.isinf(quantity) or quantity > 100:
        return {"approved": False, "reason": "Invalid quantity", "checks": {}}
        
    price = trade_proposal.get("price", 0)
    stop_loss = trade_proposal.get("stop_loss", 0)
    take_profit = trade_proposal.get("target") or trade_proposal.get("take_profit", 0)
    
    if price <= 0 or stop_loss <= 0 or take_profit <= 0:
        return {"approved": False, "reason": "Mandatory pricing/SL/TP missing or non-positive", "checks": {}}
```
