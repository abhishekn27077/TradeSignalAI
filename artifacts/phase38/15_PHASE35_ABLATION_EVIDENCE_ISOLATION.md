# Phase 38 Artifact 15: Phase 35 Mode A/B/C Ablation Evidence Isolation

## Experimental Isolation Verification
- **Mode A**: Quant Baseline Only
- **Mode B**: Quant + Kronos Mini
- **Mode C**: Full Ensemble (Quant + Kronos + FAISS + Time Patterns)

## Audit Rules
1. Phase 35 experimental code and evidence records were strictly preserved without modification.
2. Signal History endpoint supports `?ablation_mode=MODE_A|MODE_B|MODE_C` filtering to allow granular statistical auditing across experimental cohorts.
3. Validated by `tests/test_phase38_ablation_evidence.py`.
