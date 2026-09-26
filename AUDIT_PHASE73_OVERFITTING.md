# Phase 73/74 Audit: Overfitting, Deflated Sharpe & Sensitivity Analysis (Phase 21)

**Audit Date**: 2026-09-26  
**Auditor**: Independent Zero-Trust Forensic Auditor  
**Status**: **SYNTHETIC / FABRICATED AUDIT (CRITICAL FAILURE)**

---

## 1. Executive Summary

Previous documentation (`docs/PHASE72_OVERFITTING_AUDIT.md`) asserted that:
1. An empirical 8-stage component ablation hierarchy proved incremental positive contribution across indicators and machine learning models.
2. Parameter sensitivity testing ($\pm 5\%$, $\pm 10\%$, $\pm 20\%$) demonstrated "ROBUST (No cliff-edge fragility detected)" with a 100% robustness score.
3. Data snooping and lookahead audits found zero violations.

Forensic code inspection of `app/analytics/ablation_engine.py` reveals that:
- **No genuine parameter perturbation or backtesting is executed.**
- Every single method (`run_ablation_benchmark()`, `run_full_component_ablation()`, `run_parameter_sensitivity_test()`, `audit_overfitting()`) returns **hardcoded static dictionaries**.
- No statistical corrections for multiple hypothesis testing (such as Bailey & López de Prado's Deflated Sharpe Ratio, White's Reality Check, or Hansen's Superior Predictive Ability) are actually computed against trade returns.
- The generated `docs/PHASE72_OVERFITTING_AUDIT.md` is a direct serialization of pre-baked constants.

---

## 2. Forensic Code Evidence

File: [`app/analytics/ablation_engine.py`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/analytics/ablation_engine.py#L36-L105)

### A. Synthetic Ablation Table
```python
    def run_ablation_benchmark(self, sample_limit: int = 100) -> Dict[str, Any]:
        ablation_results = [
            {"config_id": "quant_only", "name": "Quant Baseline Only", "win_rate_pct": 52.4, "profit_factor": 1.12, "expectancy_r": 0.05, "contribution_vs_baseline": {"win_rate_delta_pct": 0.0}},
            {"config_id": "quant_kronos", "name": "Quant + Kronos", "win_rate_pct": 58.1, "profit_factor": 1.45, "expectancy_r": 0.16, "contribution_vs_baseline": {"win_rate_delta_pct": 5.7}},
            ...
            {"config_id": "full_consensus", "name": "Full Consensus Ensemble", "win_rate_pct": 66.8, "profit_factor": 1.88, "expectancy_r": 0.35, "contribution_vs_baseline": {"win_rate_delta_pct": 14.4}},
        ]
        return {"status": "SUCCESS", "sample_limit": sample_limit, "ablation_results": ablation_results}
```
*Finding*: The parameter `sample_limit` is accepted but completely ignored; the identical 8 hardcoded rows are returned unconditionally.

### B. Pre-Programmed Sensitivity Perturbations
```python
    def run_parameter_sensitivity_test(self) -> Dict[str, Any]:
        perturbations = [
            {"parameter": "RSI Threshold (50)", "variation": "-20%", "win_rate_pct": 64.1, "net_r": 18.2, "verdict": "ROBUST"},
            {"parameter": "RSI Threshold (50)", "variation": "-10%", "win_rate_pct": 65.5, "net_r": 20.1, "verdict": "ROBUST"},
            {"parameter": "RSI Threshold (50)", "variation": "Baseline (0%)", "win_rate_pct": 66.7, "net_r": 21.5, "verdict": "BASELINE"},
            {"parameter": "RSI Threshold (50)", "variation": "+10%", "win_rate_pct": 65.0, "net_r": 19.8, "verdict": "ROBUST"},
            ...
        ]
        return {
            "robustness_score_pct": 100.0,
            "perturbations": perturbations,
        }
```
*Finding*: No backtest runs. The win rates ($64.1\%, 65.5\%, 66.7\%, 65.0\%, 63.8\%$) are hardcoded floats designed to simulate a smooth, peaked distribution.

### C. Self-Certifying Overfitting Audit
```python
    def audit_overfitting(self) -> Dict[str, Any]:
        results = {
            "audited_at_utc": datetime.now(timezone.utc).isoformat(),
            "hardcoded_asset_magic_numbers_found": 0,
            "date_specific_override_rules_found": 0,
            "lookahead_leakage_violations_found": 0,
            "parameter_sensitivity_verdict": "ROBUST (No cliff-edge fragility detected)",
            "data_snooping_defense": "STRICT_SEPARATION (Training vs Test Folds untouched)",
        }
```
*Finding*: The engine asserts `hardcoded_asset_magic_numbers_found = 0` via a hardcoded literal `0`, while the codebase itself contains `ASSET_BASE_PRICES` (`synthetic.py:16`) and hardcoded indicator outputs (`tradingview_adapter.py:34`).

---

## 3. Multiple Testing & Deflated Sharpe Verification

1. **Multiple Testing Registry (`app/analytics/multiple_testing_registry.py`)**:
   - Contains dataclasses for tracking trial counts ($N$) and computing family-wise error rate (FWER) or Bonferroni adjustments.
   - However, it is decoupled from the strategy backtesting loops. The walk-forward tester (`walk_forward_engine.py`) does not submit evaluated hyperparameter configurations to the registry.
2. **Deflated Sharpe Ratio (DSR)**:
   - DSR requires the variance of trials, skewness, kurtosis, and track record length.
   - Because actual trial returns are not tracked across optimization runs, the reported Sharpe ratios lack statistical deflation.

---

## 4. Verdict & Recommendations

| Item | Finding | Status |
|---|---|---|
| **Ablation Testing** | Pre-written static constants masquerading as empirical backtest output | **FAIL** |
| **Parameter Sensitivity** | Pre-baked table with synthetic $\pm 10\% / \pm 20\%$ outcomes | **FAIL** |
| **Overfitting Defenses** | Self-certifying zero-violation return dictionary | **FAIL** |
| **Deflated Sharpe (DSR)** | Not computed on genuine backtest trial distributions | **FAIL** |

### Corrective Action:
1. Replace static dictionaries in `ablation_engine.py` with an actual backtest loop iterating over historical OHLCV data.
2. Dynamically perturb parameters in strategy configs, re-run backtests, and calculate genuine Sharpe and Drawdown gradients.
3. Compute the Probability of Backtest Overfitting (PBO) and Deflated Sharpe Ratio based on the actual distribution of parameter trials.
