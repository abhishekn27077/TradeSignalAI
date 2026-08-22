# 02 — Candle Clock Audit & Timing Verification
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Timing Engine Architecture
The Candle Clock (`app/core/timing.py`) provides authoritative, synchronized candle boundaries for all trading timeframes (M1, M5, M15, M30, H1, H4, D1, W1).

### Authoritative H4 Boundaries
- **Candle Schedule (UTC):** `00:00`, `04:00`, `08:00`, `12:00`, `16:00`, `20:00 UTC`
- **Candle Schedule (IST):** `05:30`, `09:30`, `13:30`, `17:30`, `21:30`, `01:30 IST`
- **Formula:**
  $$\text{Open UTC} = \text{Hour} - (\text{Hour} \bmod 4)$$
  $$\text{Close UTC} = \text{Open UTC} + 4\text{ hours}$$

---

## 2. Live Synchronization Verification
Live audit timestamp: `2026-08-20T07:20:51 UTC` (`12:50:51 IST`):
- **Current Candle Open (UTC):** `2026-08-20T04:00:00+00:00`
- **Current Candle Open (IST):** `2026-08-20 09:30:00 IST`
- **Current Candle Close (UTC):** `2026-08-20T08:00:00+00:00`
- **Current Candle Close (IST):** `2026-08-20 13:30:00 IST`
- **Remaining Seconds:** `2348s`
- **Live Countdown Display:** `00:39:08`

### Certification Verdict
- Boundary precision: $\pm 0.00\text{s}$ error.
- Timezone handling: Dual UTC & Indian Standard Time (IST) formatting verified.
- Status: **PASSED & VERIFIED**.
