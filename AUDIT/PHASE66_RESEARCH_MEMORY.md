# AUDIT: PHASE 66 PERSISTENT RESEARCH MEMORY & RUN CARDS
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 66 Certified  

---

## 1. Structured `ResearchRunCard` Schema

Every quantitative experiment generates an immutable record stored in SQLite table `research_runs`:
- `run_id`: Unique run identifier
- `hypothesis`: Natural language hypothesis being tested
- `dataset_version`: Exact frozen dataset version tag
- `strategy_version`: Git-versioned strategy commit
- `model_version`: Ensemble model weights ID
- `parameters`: JSON dictionary of evaluated parameters
- `sample_size`: Out-of-sample trade count
- `win_rate_pct`: Realized out-of-sample win rate
- `expectancy_net_r`: Friction-adjusted Net R per trade
- `profit_factor`: Gross wins over gross losses
- `sharpe_ratio`: Annualized Sharpe ratio
- `brier_score`: Probability calibration error
- `wilson_ci_95`: 95% binomial confidence bounds
- `decision`: `KEEP_CHAMPION`, `PROMOTE_CHALLENGER`, or `REJECT`
