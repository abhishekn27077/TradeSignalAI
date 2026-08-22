# 18 — Zero-Trust Certification & Anti-Fabrication Invariants
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Zero-Trust Core Invariants
TradeSignalAI-v3 operates under strict **Zero-Trust** mathematical principles:
1. **No Fake Confidences:** No placeholder 50.0%, 0.0%, or static values. Every confidence metric is a genuine calculated probability or inter-model agreement percentage.
2. **No Fabricated Signals:** Signals are generated ONLY when genuine quantitative and Kronos models agree ($> 65\%$) on a closed candle with $R:R \ge 1.50$.
3. **No Synthetic Prices:** Prices are strictly live rates fetched from global exchanges.
4. **Honest Observability:** When market conditions do not yield an actionable setup, the UI cleanly displays `NO_VALID_SETUP` and the exact per-asset multi-model intelligence scan breakdown explaining why each asset was rejected.

---

## 2. Invariant Compliance Checklist
- [x] Zero hardcoded signals in codebase.
- [x] Zero mock signals injected to populate empty screens.
- [x] Strict candle close boundary enforcement.
- [x] Full multi-model scan matrix accessible via `/api/v1/signals/h4-intelligence`.
- [x] Frontend builds with 0 errors and zero `'UNKNOWN'` fallback states.

### Final Zero-Trust Certification
- Status: **CERTIFIED COMPLIANT**.
