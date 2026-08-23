# PHASE 52 — HORIZON FORENSICS

---

## §52.30 — Horizon Forensics

| Horizon | N Signals | N Realized | Wins | Losses | WR | PF | Expectancy | Brier | WR 95% CI | Sample Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---:|
| H1 | 64 | 24 | 15 | 9 | 62.50% | 1.76 | +0.32R | 0.188 | [40.6%, 81.2%] | `INSUFFICIENT` (N<30) |
| H4 | 38 | 12 | 8 | 4 | 66.67% | 1.94 | +0.48R | 0.174 | [34.9%, 90.1%] | `INSUFFICIENT` (N<30) |
| Swing | 16 | 4 | 2 | 2 | 50.00% | 1.55 | +0.14R | 0.220 | [6.8%, 93.2%] | `INSUFFICIENT` (N<30) |
| Daily | 10 | 2 | 1 | 1 | 50.00% | 1.50 | +0.10R | 0.240 | [1.3%, 98.7%] | `INSUFFICIENT` (N<30) |

> [!CAUTION]
> **ALL four horizons have N_realized < 30**, placing every horizon in `INSUFFICIENT_SAMPLE` territory individually. The H4 "best horizon" claim is based on only 12 trades — the 95% CI for H4 win rate spans [34.9%, 90.1%], which is essentially uninformative.

### Key Findings

1. **H1** has the most trades (24) but still below the N=30 threshold
2. **H4** shows the strongest point estimates but with the widest CI due to small N
3. **Swing and Daily** have extremely small samples (4 and 2 trades) — no statistical conclusion possible
4. **Horizon ranking H4 > H1 > Swing > Daily** is a point estimate only; all CIs overlap heavily

**Classification:** All individual horizon claims are `INSUFFICIENT_SAMPLE`. The aggregate system across all horizons (N=42) is the only defensible unit of analysis.
