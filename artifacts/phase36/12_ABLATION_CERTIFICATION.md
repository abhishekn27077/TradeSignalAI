# PHASE 36 — 12_ABLATION_CERTIFICATION.md

> Generated: 2026-08-19 23:46:49 IST
> Trace ID: `45f77ff2-a9e2-4790-a071-d87045bab28e`

## 1. Phase 35 Multi-Mode Ablation
- **Mode A**: Quant Statistical Models Only (XGBoost, RandomForest, HistGB).
- **Mode B**: Quant Models + Kronos Foundation Model.
- **Mode C**: Full Stack (Quant + Kronos + FAISS + TimePattern + Regime + CrossMarket).

## 2. Separation & Isolation
- Each mode runs independently on identical market input observations.
- Results stored with explicit `ablation_mode` keys. Zero cross-talk.

## 3. Verdict
**STATUS: VERIFIED** — Ablation pipeline isolated and verified.
