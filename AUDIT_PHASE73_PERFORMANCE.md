# Phase 73/74 Audit: System Performance, Latency & Throughput (Phase 23)

**Audit Date**: 2026-09-26  
**Auditor**: Independent Zero-Trust Forensic Auditor  
**Status**: **SYNTHETIC BENCHMARKING (CLAIMED 183.3ms P95 vs ACTUAL ~3,000ms P95)**

---

## 1. Executive Summary

Previous documentation (`docs/PHASE72_LATENCY_REPORT.md`) claimed an SLA of **183.3 ms P95** and **206.5 ms Max** for the full end-to-end pipeline (from candle ingestion to SQLite WAL persistence).

Forensic investigation reveals:
1. The claimed 183.3 ms P95 is derived directly from an **8-element hardcoded list** in `app/runtime/latency_monitor.py:40`.
2. Actual empirical execution of the canonical signal pipeline (`app/services/canonical_signal_service.py`) on real historical candle data takes **1,186.60 ms P50** and **3,015.52 ms P95**—approximately **16.4 times slower** than documented.
3. The Kronos transformer inference latency claimed to be 130 ms runs in CPU fallback mode (since no CUDA GPU is active in standard environment), requiring up to 1,500 ms per batch.

---

## 2. Forensic Code Evidence

File: [`app/runtime/latency_monitor.py`](file:///d:/trading%20Bots/FinalTrade/TradeSignalAI-v3/app/runtime/latency_monitor.py#L34-L41)

```python
    def __init__(self):
        self._samples: Dict[str, List[float]] = {
            "data_ingestion": [8.2, 9.1, 10.5, 12.0, 15.2, 8.8, 9.4, 11.2],
            "feature_calculation": [12.4, 14.1, 15.8, 18.2, 22.0, 13.5, 14.9, 16.5],
            "kronos_inference": [125.0, 130.5, 133.2, 142.0, 155.0, 128.4, 131.0, 136.5],
            "consensus_scoring": [4.1, 4.5, 5.2, 6.0, 7.8, 4.3, 4.8, 5.5],
            "sqlite_persistence": [3.2, 3.8, 4.5, 5.1, 6.5, 3.5, 4.0, 4.9],
            "e2e_total": [152.9, 162.0, 169.2, 183.3, 206.5, 158.5, 164.1, 174.6],
        }
```

When `calculate_percentiles()` is called, it performs numpy percentiles over these 8 static numbers and writes the markdown report claiming SLA compliance:
```python
lines.append("Full end-to-end signal generation from candle arrival to SQLite WAL commit executes in under **200ms P95**")
```

---

## 3. Real Empirical Measurements vs Documentation Claims

| Pipeline Metric | Documented Claim (`PHASE72_LATENCY_REPORT.md`) | Forensic Reality (Local Run on Live Data) | Discrepancy Factor |
|---|---|---|---|
| **Data Ingestion** | 10.5 ms | ~25 ms (SQLite read + Pandas DataFrame conversion) | ~2.4x |
| **Feature Calculation** | 15.8 ms | ~140 ms (SuperTrend, Bollinger, MACD, RSI, SMC) | ~8.8x |
| **Kronos Inference** | 133.2 ms | ~1,200 ms (CPU PyTorch evaluation) | ~9.0x |
| **Consensus / Risk** | 5.2 ms | ~12 ms | ~2.3x |
| **Persistence (WAL)** | 4.5 ms | ~15 ms | ~3.3x |
| **End-to-End P50** | ~160.0 ms | **1,186.60 ms** | **~7.4x slower** |
| **End-to-End P95** | **183.3 ms** | **3,015.52 ms** | **~16.4x slower** |

---

## 4. Throughput & Scalability Assessment

1. **Candle Cadence Feasibility**:
   - For **1-hour** and **15-minute** timeframes, an end-to-end latency of ~3 seconds is acceptable (candles arrive once every 900–3,600 seconds).
   - For **1-minute** timeframes across multiple assets (e.g., 20 simultaneous pairs), sequential CPU inference would create backpressure ($20 \times 3\text{s} = 60\text{s}$), consuming the entire candle window.
2. **Concurrency Limitations**:
   - SQLite WAL supports multiple readers and one writer. In heavy multi-symbol scanning, the single-writer lock can cause queue contention.
3. **Database Bloat**:
   - The primary database (`tradesignal.db`) is currently 42 MB with 251,000 candles and 42,000 canonical ledger records. Querying without indexed timestamp ranges exhibits linear scan slowdowns.

---

## 5. Verdict & Recommendations

| Item | Finding | Status |
|---|---|---|
| **Latency Documentation** | Fabricated via 8-element static float arrays | **FAIL** |
| **Higher Timeframe Viability (15m, 1h)** | Sufficient throughput (~3s latency) | **PASS** |
| **1-Minute Multi-Asset Viability** | Insufficient CPU throughput without batching/GPU | **WARNING** |

### Corrective Action:
1. Remove pre-populated float arrays from `LatencyMonitor`; populate samples only from active runtime telemetry timers.
2. Implement batched model inference for multi-asset scans to reduce per-candle inference overhead.
3. Add indexed queries on `(asset, timeframe, timestamp)` across all tables.
