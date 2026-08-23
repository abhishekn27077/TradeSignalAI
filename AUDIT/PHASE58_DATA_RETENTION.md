# PHASE 58 — DATA RETENTION, STORAGE TIERING & ARCHIVAL POLICY

**Audit Phase:** Phase 58 — Safe Long-Horizon Archival  
**Date (UTC):** 2026-08-23T15:15:00Z  
**Configuration Hash:** `79a4f8e12b79310d`  

---

## 1. 3-Tier Storage Architecture

| Tier | Age Range | Storage Location | Data Maintained | Eviction Policy |
|:---|:---|:---|:---|:---|
| **HOT DATA** | 0–90 Days | In-Memory & Operational DB | Live signals, active orders, recent performance caches | Promoted to Warm at 90 days |
| **WARM DATA** | 90–180 Days | Local Durable Storage | Full signal snapshots, realized trades, counterfactuals | Promoted to Cold at 180 days |
| **COLD ARCHIVE** | 180+ Days | Compressed Archive Volumes | Permanent immutable SHA256 manifests & datasets | **NEVER DELETED** (10+ Year Retention) |

---

## 2. Inviolable Retention Invariants

1. **Zero Raw Evidence Deletion:** Raw signal records, realized trade ledgers, counterfactual stores, and cryptographic hash chains are **PERMANENTLY PRESERVED**.
2. **Restricted Deletion Scope:** Only transient caches (intermediate Monte Carlo arrays, debug logs, temp charts, stale response caches) may be purged.
3. **Safety Default:** Archival manager defaults to `DRY_RUN = True`.
