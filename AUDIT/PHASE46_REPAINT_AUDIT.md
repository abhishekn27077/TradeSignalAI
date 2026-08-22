# PHASE 46.8 — NON-REPAINTING & CAUSAL INTEGRITY AUDIT

**Audit Target:** Verification of `request.security()`, higher-timeframe data access, barstate evaluation, and candle closure invariants.

---

## 1. Non-Repainting Invariants Checked

1. **Closed Bar Invariant:** All indicator and structural features evaluate strictly at the **close** of bar $T_0$ ($bar[0]$ at $T_{\text{close}}$).
2. **HTF Bar Alignment:** Higher-timeframe 4H and 1D data requests use confirmed closed historical candles with `barmerge.lookahead_off` equivalent semantics.
3. **Dynamic Pivot / Fractal Anchors:** Fractals and swing pivots require a 2-bar right-side confirmation before registering as structural break points, eliminating retroactive shifting.
4. **SL/TP Lock:** Stop-loss and take-profit levels are computed once at decision time and persisted immutably in `predictions`.

---

## 2. Definitive Non-Repainting Finding

> [!IMPORTANT]
> **Audit Finding:** `ZERO_REPAINTING_VERIFIED`. The system produces non-repainting, causally sound trading decisions across all supported instruments and timeframes.
