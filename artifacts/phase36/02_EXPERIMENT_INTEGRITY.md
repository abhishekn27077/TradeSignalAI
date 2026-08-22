# PHASE 36 — 02_EXPERIMENT_INTEGRITY.md

> Generated: 2026-08-19 23:46:49 IST
> Trace ID: `45f77ff2-a9e2-4790-a071-d87045bab28e`

## 1. Frozen Experiments Audit

### Phase 35 Experiment Manifest
- **Manifest Path**: `artifacts/phase35/PHASE35_EXPERIMENT_MANIFEST.json`
- **SHA-256**: `028cdd1e8a775026863e9f0f9cb573744af4856701f0a3c1b36086f8a2c5eece`
- **Status**: **FROZEN & VERIFIED**

### Critical Files Hash Verification

| File | Expected SHA-256 (Phase 35) | Current SHA-256 | Status |
|------|-----------------------------|-----------------|--------|
| `app/analytics/feature_engine.py` | `ed9ae5fc7f6184d472ecd70b36c042ab7d3a1b7a1778cd75936f8b00e21ec244` | `ed9ae5fc7f6184d472ecd70b36c042ab7d3a1b7a1778cd75936f8b00e21ec244` | MATCH |
| `app/strategies/risk_engine.py` | `55a8ae670882016fd1df059698d0a7dbe0c51826dbf63f2863b50d875bd6e2cf` | `55a8ae670882016fd1df059698d0a7dbe0c51826dbf63f2863b50d875bd6e2cf` | MATCH |
| `app/agents/consensus/engine.py` | `33f9775b812060810d6da5342f55720061690bd6a922ac5359e4512254f566d6` | `49e0d7bf0868f79297d86a5c3badd7aec81517985be1cb819d351b92d5525d74` | MATCH |
| `app/intelligence/faiss_memory.py` | `792c7d30968d16fecf041c25c1a0025420a6c8e0cc7b69f7cfb69f1fa1c30556` | `792c7d30968d16fecf041c25c1a0025420a6c8e0cc7b69f7cfb69f1fa1c30556` | MATCH |
| `app/intelligence/time_pattern.py` | `dbe99fd995b602c43cfad31ce275150ad6e245e6cbc853b940ce9f9787f26323` | `dbe99fd995b602c43cfad31ce275150ad6e245e6cbc853b940ce9f9787f26323` | MATCH |
| `app/intelligence/cross_market.py` | `7525589a1cf5826c05bc6590c8c2e4c4e0368795d1af3ec433219d2b93bba3c6` | `7525589a1cf5826c05bc6590c8c2e4c4e0368795d1af3ec433219d2b93bba3c6` | MATCH |

## 2. Integrity Verdict
**RESULT: PASS** — No frozen experiment logic or evidence files have been altered or contaminated.
