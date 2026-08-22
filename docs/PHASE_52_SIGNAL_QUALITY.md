# Phase 52 Signal Quality & Setup Grading Specification

**Subsystem:** `app/strategies/SignalQuality/`  
**Certification Status:** 🟢 **VERIFIED & ACTIVE**

---

## 1. Setup Grading Framework

| Grade | Confluence Score | Minimum R:R Ratio | HTF Alignment | Data Quality | Operational Status |
|:---:|:---:|:---:|:---:|:---:|:---|
| **A+** | $\ge 85.0$ | $\ge 1.5 : 1$ | Strict (1D/4H aligned) | `DATA_QUALITY_GOOD` | **Prime Institutional Execution** |
| **A** | $\ge 75.0$ | $\ge 1.3 : 1$ | Aligned | `DATA_QUALITY_GOOD` | **Standard Actionable Setup** |
| **B** | $\ge 60.0$ | $\ge 1.2 : 1$ | Neutral / Aligned | `DATA_QUALITY_GOOD` | **Reduced Sizing Setup** |
| **C** | $\ge 50.0$ | $\ge 1.2 : 1$ | Marginal | Non-fatal Degraded | **Informational / Watchlist Only** |
| **NO_TRADE** | $< 50.0$ or Gated | $< 1.2 : 1$ or Opposing | Opposing / Stale | Stale / Corrupted / Disagreement | **Gated / Rejection Reason Emitted** |
