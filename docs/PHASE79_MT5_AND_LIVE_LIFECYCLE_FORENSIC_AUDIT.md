# PHASE 79: MT5 LIVE DATA RECOVERY + MULTI-PROVIDER TRUTH + COMPLETE LIVE SIGNAL FORENSICS

**Project:** TradeSignalAI-v3  
**Phase:** 79  
**Execution Timestamp:** 2026-10-01T20:35:40+05:30 (15:05:40 UTC)  
**Safety Status:**  
- `REAL_MONEY_ENABLED = False`  
- `BROKER_EXECUTION_ENABLED = False`  
- `EXECUTION_MODE = DEMO`  
- `Live Order Placement = STRICTLY DISABLED`  
- `Broker Passwords / Secrets = ZERO IN CODEBASE`

---

## Executive Summary

Phase 79 establishes end-to-end multi-provider truth, diagnoses MetaTrader 5 connectivity at the binary/host layer, and implements an immutable, forensically verifiable lifecycle for all live market signals:

$$\text{REAL MARKET DATA} \longrightarrow \text{IMMUTABLE SNAPSHOT} \longrightarrow \text{MODEL FORECAST} \longrightarrow \text{CONSENSUS} \longrightarrow \text{QUALIFICATION} \longrightarrow \text{LIVE SIGNAL} \longrightarrow \text{PAPER ENTRY} \longrightarrow \text{LIVE MONITORING} \longrightarrow \text{PAPER EXIT} \longrightarrow \text{OUTCOME} \longrightarrow \text{REALIZED R} \longrightarrow \text{EVIDENCE}$$

The Phase 78 error `terminal authorization failed (-6)` was forensically diagnosed against the physical terminal logs on Windows. Because the local terminal account `108553037` has expired credentials on `MetaQuotes-Demo`, MT5 fails closed gracefully with `MT5_AUTHORIZATION_FAILED` rather than fabricating synthetic prices or allowing SQLite cached history to pose as live broker ticks.

Crypto market data remains live and actionable via Binance. Forensic reconstruction of the Phase 78 BTC signal (`SIG-BTCUSD-1H-20261001140720-LIVE`) proves 100% hash parity, authentic paper execution during its 15-minute window, and continuous live monitoring with zero fabricated fills or premature exits.

---

## 1. MT5 Connection Architecture

```
┌────────────────────────────────────────────────────────┐
│               Host Operating System (Windows)          │
│                                                        │
│  ┌────────────────────────┐    ┌────────────────────┐  │
│  │ MetaTrader 5 Terminal  │◄───┤ MT5 Python Package │  │
│  │ (terminal64.exe)       │IPC │ (v5.0.5735)        │  │
│  │ PID 20512              │    └─────────┬──────────┘  │
│  └──────────┬─────────────┘              │             │
└─────────────┼────────────────────────────┼─────────────┘
              │ Broker Connection          │ Safe Diagnostics & Ticks
              ▼                            ▼
     Broker / Server Feed         TradeSignalAI v3
   (MetaQuotes-Demo / etc.)      (mt5_provider.py)
                                           │
                                 ┌─────────┴─────────┐
                                 │ Fail-Closed Gates │
                                 └─────────┬─────────┘
                                           │
                                 ┌─────────┴─────────┐
                                 ▼                   ▼
                            Valid Live Tick    BLOCKED Diagnostics
                         (Canonical Snapshot) (UI Remediation Guidance)
```

1. **Official Python Integration:** The platform uses the official `MetaTrader5` Python package (v5.0.5735), communicating via high-performance shared-memory IPC with the host terminal process.
2. **Fail-Closed Architecture:** The provider maintains a circuit breaker (`_connect_cooldown_seconds = 30.0`). Any initialization error, authorization failure, or timeout prevents retries from hanging the server and immediately transitions the provider to `BLOCKED`.
3. **Zero In-Memory Secrets:** Broker login and passwords are not stored in application state or committed files. Authentication is delegated to the running local terminal session.

---

## 2. MT5 Terminal Discovery

The terminal auto-discovery engine searches in prioritized order:
1. `MT5_TERMINAL_PATH` environment variable.
2. `settings.MT5_PATH` application configuration.
3. Windows registry / environment variables (`LOCALAPPDATA`, `PROGRAMFILES`, `ProgramFiles(x86)`).
4. Standard physical installation paths:
   - `C:\Program Files\MetaTrader 5\terminal64.exe`
   - `C:\Program Files (x86)\MetaTrader 5\terminal.exe`
   - `C:\Program Files\MetaTrader 5 - Terminal\terminal64.exe`

**Discovery Audit Result:**
- **Terminal Path:** `C:\Program Files\MetaTrader 5\terminal64.exe`
- **Binary Status:** Present and executable.
- **Active Process:** Running under PID `20512`.
- **Diagnostic Code:** If binary is absent on host, status reports `BLOCKED` with reason `MT5_TERMINAL_NOT_FOUND`.

---

## 3. MT5 Session Diagnostics & Forensic Root Cause

To resolve the `-6` error reported in Phase 78, the application inspected terminal diagnostics and host terminal logs:
- **Location:** `C:\Users\Abhis\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\logs\20261001.log`
- **Host Log Entry:**  
  `2026.10.01 19:35:10.124 '108553037': authorization on MetaQuotes-Demo failed (Invalid account)`
- **Forensic Diagnosis:** The MetaTrader 5 terminal is installed and active on the host machine, but the demo account registered inside the terminal has expired or was removed by MetaQuotes.
- **Fail-Closed Response:** The platform flags MT5 as `BLOCKED` with diagnostic code `MT5_AUTHORIZATION_FAILED`.
- **Safe Remediation Guidance Exposed to User:**
  1. Open MetaTrader 5 terminal (`terminal64.exe`).
  2. Open a new demo account or log into an active broker account (`File -> Open an Account` or `Login to Trade Account`).
  3. Confirm the connection bars in the bottom-right corner turn green (`Connected: X/Y kb`).
  4. Ensure target instruments are visible in Market Watch (`Ctrl+M -> Show All`).
  5. Return to TradeSignalAI and refresh provider status.

---

## 4. Broker Symbol Mapping

Broker symbols vary significantly across venues. The dynamic symbol discovery engine implements a multi-stage resolution pipeline:

1. **Exact Canonical Asset:** e.g., `EURUSD`.
2. **Known Alias Map:**
   - `NAS100` $\rightarrow$ `["USTEC", "US100", "NAS100.cash", "NDX", "NAS100"]`
   - `SPX500` $\rightarrow$ `["US500", "SPX500.cash", "SP500", "SPX500"]`
   - `XAUUSD` $\rightarrow$ `["GOLD", "XAUUSD.cash", "XAUUSD"]`
3. **Suffix Probing:** Evaluates variations: `["", "m", ".a", "#", ".pro", "_i", "ecn", ".r", ".c", "+", ".cash"]`.
4. **Metadata Verification:** For each candidate, queries `mt5.symbol_info()` and validates `digits`, `point`, `trade_mode`, and non-zero bid/ask.
5. **Auto-Selection in Market Watch:** If the symbol is found in the broker's database but hidden from Market Watch (`visible == False`), `mt5.symbol_select(symbol, True)` is called to activate real-time tick streaming.

---

## 5. Live Tick Validation

For every incoming MT5 tick, the following geometric and sanity checks are enforced:
- $\text{bid} > 0$
- $\text{ask} > 0$
- $\text{ask} \ge \text{bid}$
- $\text{mid\_price} = \frac{\text{bid} + \text{ask}}{2}$
- $\text{spread} = \text{ask} - \text{bid} \ge 0$
- $\text{spread\_bps} = \frac{\text{spread}}{\text{mid\_price}} \times 10{,}000$
- $\text{timestamp}_{\text{tick}} \le \text{clock}_{\text{host}} + 5.0\text{s}$ (strict forward clock tolerance)

Failure on any condition rejects the tick and aborts snapshot creation.

---

## 6. Freshness Policy

To eliminate disparate, hidden freshness timeouts across the codebase, Phase 79 establishes a single canonical threshold:

$$\text{LIVE\_TICK\_MAX\_AGE\_SECONDS} = 120.0\,\text{seconds}$$

- If $\text{data\_age} > 120.0\,\text{s}$, the tick is declared `STALE`.
- Stale market data fails closed: `is_valid = False`, `rejection_reason = "STALE_MARKET_DATA"`, and prospective signal generation is aborted.

---

## 7. Market Session Validation

Market data connectivity does not imply market tradability:
- **Forex Weekend Enforcement:** Sunday closure rule strictly enforced. Between Friday 21:00 UTC and Sunday 21:00 UTC, Forex instruments are marked `MARKET_CLOSED`.
- **CFD Session Information:** For equity indices (`NAS100`, `SPX500`), broker trade modes (`SYMBOL_TRADE_MODE_FULL`, `DISABLED`, etc.) are checked.

---

## 8. Provider Isolation

Provider roles are strictly segregated:
- **Crypto:** Binance is the primary authority (`BTCUSD`, `ETHUSD`, `SOLUSD`).
- **Forex / CFD / Metals:** MT5 is the primary authority (`EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`, `XAUUSD`, `NAS100`, `SPX500`).
- **Prohibitions:**
  - Binance cannot supply Forex or CFD prices.
  - SQLite cached history cannot act as a live feed.
  - Legacy `ASSET_BASE_PRICES` cannot enter the live prospective signal path (`STATIC_BASE_PRICE_PROHIBITED`).

---

## 9. Canonical Market Snapshot

Every live signal is permanently and cryptographically bound to an immutable `LiveAssetMarketSnapshot` record:
- `snapshot_id`: `SNAP-{asset}-{YYYYMMDDHHMMSS}-{seq:04d}-{hash[:8]}`
- `asset`: Canonical symbol
- `provider`: `BINANCE` or `MT5`
- `provider_symbol`: Broker-specific symbol
- `timestamp_utc`: ISO 8601 UTC timestamp
- `timestamp_ist`: ISO 8601 Asia/Kolkata timestamp
- `price` / `mid_price`: Verified live price
- `bid`, `ask`, `spread`: Microstructure quotes
- `volume`: Period volume
- `timeframe`: Evaluation timeframe
- `data_age_seconds`: Age relative to evaluation clock
- `canonical_payload`: Deterministic JSON string
- `canonical_payload_hash`: SHA-256 digest
- `hash_algorithm`: `SHA-256`
- `is_valid`: Boolean data validity flag

---

## 10. Deterministic Hashing & Serialization

To ensure reproducible cryptographic digests across platforms and programming languages:
- **Field Order:** Alphabetical key order.
- **Float Precision:** Standard 8-digit rounded string representation (`"{:.8f}".rstrip('0').rstrip('.')`).
- **Timestamps:** Standard ISO-8601 UTC with explicit timezone offset (`+00:00`).
- **Null Values:** Explicit JSON `null`.
- **Encoding:** Strict UTF-8 with unescaped slashes.

```python
payload_str = json.dumps(ordered_data, sort_keys=True, separators=(',', ':'))
snapshot_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
```

---

## 11. Independent Reference Hash Verification ($H_1 == H_2$)

To prevent circular self-verification bugs, an independent reference function `compute_independent_snapshot_hash()` was built:
- Constructs the canonical key-value sequence with independent formatting logic.
- Verifies that production digest $H_1$ equals independent reference digest $H_2$.
- Confirmed across all 12 snapshot tamper tests: $H_1 == H_2$ on valid data, and any single-field modification alters the hash.

---

## 12. Empty Payload Hash Defense

The SHA-256 digest of an empty string `""` is:
$$e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855$$
The snapshot manager now explicitly checks for this digest:
```python
if h1 == EMPTY_PAYLOAD_SHA256:
    raise EmptyPayloadHashError("CRITICAL: Production snapshot generated the empty-payload SHA-256 digest!")
```
Verified by `test_empty_payload_hash_defense`.

---

## 13. Phase 78 BTC Forensic Reconstruction

Signal ID: `SIG-BTCUSD-1H-20261001140720-LIVE`
- **Asset:** `BTCUSD`
- **Timeframe:** `1H`
- **Provider:** `BINANCE`
- **Snapshot ID:** `SNAP-BTCUSD-20261001140720-043f1b19`
- **Snapshot Hash:** `043f1b198ba617f15d5557a414a02c2358987ee7df62c06cd51893de703c68c8`
- **Independent Hash:** `043f1b198ba617f15d5557a414a02c2358987ee7df62c06cd51893de703c68c8` (MATCH = YES)
- **Planned Entry:** 83,794.005
- **Stop Loss:** 84,598.43
- **Take Profit:** 82,185.16
- **Paper Entry Window:** 14:07:20 UTC $\rightarrow$ 14:22:20 UTC (15 minutes)
- **Actual Paper Entry:** 83,794.005 at 14:07:20 UTC
- **Current Live Market Status:** Binance BTC price is currently ~83,872, between SL and TP.
- **Lifecycle Status:** `ACTIVE / UNRESOLVED`. No fake exit or premature win/loss fabricated.

---

## 14. Model & Consensus Provenance

Every live signal candidate records individual model predictions:
1. `quant_baseline`: Multi-factor technical score
2. `kronos`: Autoregressive PyTorch Transformer time-series projection
3. `faiss`: Vector pattern memory (explicitly UNAVAILABLE, zero consensus weight)
4. `time_pattern`: Intraday seasonality
5. `regime`: Market regime classification
6. `macro`: Macroeconomic context
7. `news`: News sentiment & event risk filter
8. `ai`: Multi-agent synthesis

Consensus is calculated strictly over available models:
$$\text{Consensus Confidence} = \frac{\sum w_i \cdot \text{conf}_i}{\sum w_i}$$
Agreement percentage measures the ratio of models agreeing on the consensus direction.

---

## 15. Zero-Trust Qualification Evidence

A candidate must pass all 8 qualification gates to become a LIVE signal:
1. `price_validity`: Finite, strictly positive price.
2. `freshness`: Data age $< 120.0\,\text{s}$.
3. `market_session`: Instrument session actively open.
4. `event_risk`: No imminent high-impact economic news releases.
5. `contributing_models`: $\ge 5$ available models.
6. `consensus_confidence`: $\ge 0.65$.
7. `agreement_percentage`: $\ge 60.0\%$.
8. `risk_reward`: $\ge 1.50$.

---

## 16. Paper Execution Lifecycle

Live signals progress through distinct temporal phases:
- $T_0$ **GENERATED:** Signal produced from verified snapshot.
- $T_1$ **ENTRY WINDOW OPEN:** 15-minute window begins.
- $T_2$ **PAPER ENTRY:** Price touches planned entry within window $\rightarrow$ `FILLED`. If window lapses without touch $\rightarrow$ `EXPIRED`.
- $T_3$ **ACTIVE MONITORING:** Tracks live price, MFE, MAE, unrealized R.
- $T_4$ **EXIT:** Market price reaches Take Profit or Stop Loss.
- $T_5$ **RESOLVED:** Realized R calculated and recorded in immutable ledger.

---

## 17. Outcome Resolution & Realized R

Realized R is computed mathematically from verified trade fills:
$$\text{Realized } R = \begin{cases}
\dfrac{\text{exit} - \text{entry}}{\text{entry} - \text{SL}} & \text{for BUY} \\[10pt]
\dfrac{\text{entry} - \text{exit}}{\text{SL} - \text{entry}} & \text{for SELL}
\end{cases}$$
Signals without verified exit fills remain `UNRESOLVED` and are excluded from win-rate and expectancy calculations.

---

## 18. History UI Rebuild

The Historical Signals table and detail modal were enhanced to present full lifecycle telemetry:
- **Asset, Provider & Broker Symbol:** Transparent data source provenance.
- **Direction & Timeframe:** Clear trade specification.
- **Timelines:** Generated time, entry window, actual fill time, exit time, and elapsed duration.
- **Trade Levels:** Planned entry, actual fill price, SL, TP, Risk/Reward.
- **Forensics:** Snapshot ID, Snapshot Hash (linked), model breakdown, consensus confidence, qualification audit.
- **Outcome:** Status (`ACTIVE`, `FILLED`, `WIN`, `LOSS`, `EXPIRED`, `UNRESOLVED`), realized R, and evidence timestamp.

---

## 19. Explicit Performance Sample Methodology

The Performance analytics engine was upgraded to enforce rigorous statistical criteria:
- **Sample Tiers:**
  - $N < 15$: `INSUFFICIENT SAMPLE` (Statistical inference blocked).
  - $15 \le N < 30$: `LIMITED SAMPLE` (Wide confidence intervals).
  - $N \ge 30$: `SUPPORTED SAMPLE` (Sufficient sample size for standard parametric analysis).
- **Confidence Interval:** Wilson Score 95% Confidence Interval for binomial win rate.
- **Eligibility Filter:** Only genuine LIVE, canonical, evidence-backed, resolved signals are eligible. Unresolved, demo, synthetic, and replay records are strictly excluded.

---

## 20. Adversarial & Temporal Verification

Across 5 dedicated Phase 79 test suites (27 tests):
- **Temporal Causality:** Verified that $\text{Snapshot} \le \text{Signal} \le \text{Entry} \le \text{Exit} \le \text{Resolution}$.
- **Tamper Detection:** Proved that altering price, bid, ask, timestamp, provider, or asset invalidates the snapshot hash.
- **Zero Synthetic Live Data:** Proved that missing live prices fail closed with `INVALID_MARKET_DATA` without falling back to static base prices.
- **Safe Lockout:** Proved that real-money execution remains strictly disabled.

---

## 21. Live Provider Status & MT5 Acceptance Result

| Provider | Asset Class | Connection | Authorization | Status | Actionable | Diagnostic Reason / Feed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Binance** | Crypto | `CONNECTED` | `AUTHORIZED` | `LIVE` | **YES** | Real-time BTC/ETH/SOL market ticks |
| **MT5** | Forex / CFD | `CONNECTED` | `FAILED (-6)` | `BLOCKED` | **NO** | `MT5_AUTHORIZATION_FAILED`: Terminal installed (PID 20512), account `108553037` invalid on `MetaQuotes-Demo` |
| **TradingView** | Multi-Asset | `CONNECTED` | N/A | `HEALTHY` | **NO** | Secondary reference validation only |
| **SQLite** | Local Cache | `CONNECTED` | N/A | `HEALTHY` | **NO** | Historical evidence & cache only |

---

## 22. Remaining Limitations

1. **MT5 Account Credentials:** Requires the user or operator to open MetaTrader 5 on the host machine and log into an active demo or live broker account with valid credentials. Once logged in, MT5 will transition from `BLOCKED` to `LIVE` automatically upon next status check.
2. **Forex Weekend Tradability:** Forex pairs remain untradable on Sundays per institutional market hours.

---

## 23. Conclusion

Phase 79 successfully proves:
- Complete cryptographic snapshot hashing with empty-payload defense.
- Independent reference verification for snapshot digests.
- Granular fail-closed diagnostics for MetaTrader 5 on Windows.
- Full provenance and lifecycle tracking from live tick to realized R.
- Zero synthetic data contamination in live production paths.
