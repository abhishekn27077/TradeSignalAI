# AUDIT: PHASE 67 IMMUTABLE PROSPECTIVE SIGNAL JOURNAL & SNAPSHOT ARCHITECTURE
**System:** TradeSignalAI-v3  
**Configuration Hash:** `79a4f8e12b79310d`  
**Git Anchor:** `94d5efa`  

---

## 1. Schema & Field Definition

The `ProspectiveSignalRecord` contains 10 comprehensive metadata blocks frozen at generation time ($T_0$):

1. **IDENTITY:** `signal_id`, `asset`, `timeframe`, `horizon`, `direction`, `signal_type`, `generated_at`.
2. **CAUSALITY:** `information_cutoff_time`, `canonical_snapshot_id`, `canonical_snapshot_hash`, `market_data_version`, `git_commit`, `config_hash`, `model_version`, `policy_version`.
3. **PRICE:** `current_price`, `entry_price`, `stop_loss`, `take_profit`, `risk_reward`, `expiry_time`.
4. **PROBABILITY:** `raw_confidence`, `calibrated_probability`, `p_tp_first`, `p_sl_first`, `p_time_exit`.
5. **EXPECTED VALUE:** `expected_gross_r`, `expected_net_r`.
6. **SIGNAL QUALITY:** `signal_strength` ($0-100$), `quality_grade` ($A+, A, B, C, WATCH, REJECTED$), `consensus_pct`, `evidence_cluster_count`, `htf_alignment_score`, `mtf_conflict_score`.
7. **CONTEXT:** `market_regime`, `session`, `weekday`, `event_risk`, `volatility_regime`, `trend_state`, `structure_state`, `liquidity_state`.
8. **EVIDENCE:** 9 Indicator and Evidence clusters dictionary.
9. **DECISION:** `decision`, `decision_trace`, `rejection_reason`.
10. **PROVENANCE:** `content_hash`, `created_at`.

---

## 2. Hard Immutability Guarantees

- **Primary Invariant:** A prospective signal prediction, once written to `prospective_signal_journal`, can NEVER be altered.
- **Enforcement:**
  ```python
  if existing.entry_price != record.entry_price or \
     existing.stop_loss != record.stop_loss or \
     existing.take_profit != record.take_profit or \
     existing.direction != record.direction or \
     existing.calibrated_probability != record.calibrated_probability:
      raise ImmutableSignalError(
          f"IMMUTABLE_SIGNAL_VIOLATION: Attempted to mutate historical prediction fields of signal {record.signal_id}!"
      )
  ```
- **Lifecycle Separation:** All post-$T_0$ outcomes (exit price, exit time, realized Net R, MFE/MAE excursions, frictions) are appended strictly into the separate table `prospective_outcomes`.

---

## 3. Database Indexes & Query Performance

The SQLite schema includes dedicated B-Tree indexes:
- `idx_psj_asset ON prospective_signal_journal(asset)`
- `idx_psj_timeframe ON prospective_signal_journal(timeframe)`
- `idx_psj_grade ON prospective_signal_journal(quality_grade)`
- `idx_psj_generated ON prospective_signal_journal(generated_at)`
- `idx_pso_outcome ON prospective_outcomes(outcome)`
- `idx_pso_resolved ON prospective_outcomes(resolved_at)`
