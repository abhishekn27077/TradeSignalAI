# PHASE 36 — LIVE TRUTH CERTIFICATION
## TradeSignalAI-v3 | Zero-Trust Frontend ↔ Backend Data Flow

**Certification Date:** 2026-08-19  
**Status:** ✅ CERTIFIED — All defects remediated. 139 tests passing. Zero synthetic fallbacks.

---

## PRINCIPLE

> Every value shown in the React Dashboard must be traceable to the actual Backend / API / WebSocket / Database pipeline.  
> If data is unavailable, the UI **must** explicitly show `UNAVAILABLE`, `DATA_UNAVAILABLE`, `INSUFFICIENT_DATA`, `NO_VERIFIED_NEWS`, or `NO_VALID_SETUP`.

---

## DEFECTS IDENTIFIED AND REMEDIATED

### [DEFECT-36-01] Hardcoded Historical Accuracy in Frontend
| | |
|---|---|
| **File** | `frontend/src/pages/TradingDashboard.tsx` |
| **Before** | `val.historical_accuracy ? '...' : '85.4%'` |
| **After** | `(val.historical_accuracy != null && val.historical_accuracy > 0) ? '...' : 'UNAVAILABLE'` |
| **Impact** | Dashboard was always showing `85.4%` accuracy even when no real historical data existed |

### [DEFECT-36-02] Synthetic Confidence Zero Default in Frontend  
| | |
|---|---|
| **File** | `frontend/src/pages/TradingDashboard.tsx` |
| **Before** | `const confidence = pred.confidence ?? sig.confidence ?? 0;` |
| **After** | `const confidence = pred.confidence ?? sig.confidence ?? null;` |
| **Impact** | When confidence was missing, dashboard showed `0%` instead of `UNAVAILABLE` |

### [DEFECT-36-03] Fabricated Agent Confidence `?? 50` — initializeAgents
| | |
|---|---|
| **File** | `frontend/src/store/useAppStore.ts` |
| **Before** | `confidence: a.confidence ?? 50` (in `initializeAgents`) |
| **After** | `confidence: a.confidence ?? null` |
| **Impact** | All AI agents displayed `50%` confidence when backend returned no data |

### [DEFECT-36-04] Fabricated Agent Confidence `?? 50` — refreshAgents
| | |
|---|---|
| **File** | `frontend/src/store/useAppStore.ts` |
| **Before** | `confidence: a.confidence ?? 50` (in `refreshAgents`) |
| **After** | `confidence: a.confidence ?? null` |
| **Impact** | Same as above — both init paths were affected |

### [DEFECT-36-05] Fabricated Signal Strength `?? 50` — mapSignal
| | |
|---|---|
| **File** | `frontend/src/store/useAppStore.ts` |
| **Before** | `strength: ... (s.strength ?? s.score ?? 50)` |
| **After** | `strength: ... (s.strength ?? s.score ?? null)` |
| **Impact** | Signal cards displayed `50` strength bars when pipeline had not computed strength |

### [DEFECT-36-06] Injected Fake XAI Reasoning Text
| | |
|---|---|
| **File** | `frontend/src/pages/TradingDashboard.tsx` |
| **Before** | `val.xai_reasoning || 'AI models detected strong directional probability aligned with market regime.'` |
| **After** | `val.xai_reasoning || val.reasoning || sig.reasoning || sig.ai_explanation || 'UNAVAILABLE'` |
| **Impact** | Dashboard always showed a fake explanation when backend XAI was missing |

### [DEFECT-36-07] Fake `PENDING` Signal Status
| | |
|---|---|
| **File** | `frontend/src/pages/TradingDashboard.tsx` |
| **Before** | `sig.status ?? 'PENDING'` |
| **After** | `sig.status ?? sig.signal_state ?? 'UNAVAILABLE'` |
| **Impact** | Missing status silently showed `PENDING` instead of truth |

### [DEFECT-36-08] Wrong SQL Filter in `/history` Endpoint
| | |
|---|---|
| **File** | `app/api/v1/signals.py` |
| **Before** | `status.in_(["WIN", "LOSS", "BREAKEVEN", "EXPIRED", "INVALIDATED", "AMBIGUOUS"])` |
| **After** | `signal_state.in_(["TP_HIT", "SL_HIT", "TIME_EXIT", "EXPIRED", "AMBIGUOUS", "COMPLETED"])` |
| **Impact** | `/history` endpoint returned **zero records** because `WIN`, `LOSS`, `BREAKEVEN` do not exist in the `signal_state` enum — the correct column is `signal_state` with canonical state names |

### [DEFECT-36-09] Deterministic Fake AI Consensus Models
| | |
|---|---|
| **File** | `app/api/v1/signals.py` — `/ai-consensus` endpoint |
| **Before** | Used MD5 hash of `signal_id` to generate 6 fabricated model votes with fake confidence ±15% variations |
| **After** | Returns only real `model_trace` and `intelligence_snapshot` from DB + `data_availability: REAL|UNAVAILABLE` |
| **Impact** | The AI Consensus view was entirely synthetic — no real model data was ever shown |

### [DEFECT-36-10] Datetime Serialization Failure
| | |
|---|---|
| **File** | `app/api/v1/signals.py` — `/today`, `/yesterday`, `/history` endpoints |
| **Before** | `signals.append({c.name: getattr(s, c.name)...})` — raw `datetime` objects in dict |
| **After** | Added `if hasattr(v, 'isoformat'): row[k] = v.isoformat()` for all datetime fields |
| **Impact** | All signal list endpoints would return HTTP 500 if any datetime column was populated |

### [DEFECT-36-11] Hardcoded Confidence in `/predict` Endpoint
| | |
|---|---|
| **File** | `app/api/v1/signals.py` — `/predict/{symbol}` |
| **Before** | `signal = {"direction": "WAIT", "confidence": 0.5}` |
| **After** | `signal = {"direction": "WAIT", "confidence": None}` |
| **Impact** | Prediction endpoint always seeded `0.5` confidence before calling the engine, biasing output |

---

## TEST EVIDENCE

| Suite | Tests | Result |
|-------|-------|--------|
| Phase 36 API Contract (`test_phase36_api_contract.py`) | 17 | ✅ 17 PASSED |
| Phase 35 Ablation (`test_phase35_ablation.py`) | 6 | ✅ 6 PASSED |
| Phase 35 Calibration (`test_phase35_calibration.py`) | 4 | ✅ 4 PASSED |
| Phase 33 Signal Lifecycle (`test_phase33_signal_lifecycle.py`) | — | ✅ PASSED |
| Phase 33 Zero Trust (`test_phase33_zero_trust.py`) | — | ✅ PASSED |
| Phase 33 FAISS (`test_phase33_faiss.py`) | — | ✅ PASSED |
| Phase 33 Outcome (`test_phase33_outcome.py`) | — | ✅ PASSED |
| Phase 33 Risk (`test_phase33_risk.py`) | — | ✅ PASSED |
| Phase 33 Real Price (`test_phase33_real_price.py`) | — | ✅ PASSED |
| Kronos Adapter | — | ✅ PASSED |
| All Other Phase Tests | — | ✅ PASSED |
| **TOTAL** | **139** | **✅ 139 PASSED** |

---

## ZERO-TRUST RULES NOW ENFORCED BY TESTS

The following are enforced permanently by `tests/test_phase36_api_contract.py`:

1. `/history` endpoint **must** filter by `signal_state` (not `status`)
2. `/history` resolved states **must** all be valid `signal_state` enum members
3. `/ai-consensus` endpoint **must not** use MD5 hash to generate fake model votes
4. `/ai-consensus` **must** return `data_availability: REAL|UNAVAILABLE`
5. `signals.py` **must not** contain any hardcoded `85.4%` accuracy string
6. `TradingDashboard.tsx` **must not** contain `'85.4%'` string
7. `TradingDashboard.tsx` **must not** use `?? sig.confidence ?? 0` (zero default)
8. `useAppStore.ts` **must not** use `confidence: a.confidence ?? 50`
9. `useAppStore.ts` **must not** use `?? s.score ?? 50` for signal strength
10. `TradingDashboard.tsx` **must not** inject the fake XAI reasoning sentence
11. `TradingDashboard.tsx` **must not** default status to `'PENDING'`
12. `signals.py` **must** contain datetime ISO serialization (`hasattr(v, 'isoformat')`)
13. `SignalLifecycleModel` **must** have all Phase 33 trace fields
14. `/predict` endpoint **must not** seed `confidence: 0.5` before calling the engine

---

## UNCHANGED PROTECTIONS (PRESERVED)

- ✅ Phase 29 frozen model logic — **NOT MODIFIED**
- ✅ Phase 33 duplicate protection SHA-256 hash — **NOT MODIFIED**
- ✅ Phase 35 ablation tests — **ALL PASS**
- ✅ `formatters.ts` — correctly returns `'Not Available'` for `null`/`undefined` — **NOT MODIFIED**
- ✅ Database schema `SignalLifecycleModel` — **NOT MODIFIED** (read-only audit)

---

## REMAINING KNOWN GAPS (NOT IN SCOPE OF PHASE 36)

> These are data pipeline gaps, not fabrication points. The UI now correctly shows `UNAVAILABLE` for these.

| Field | Gap |
|-------|-----|
| `historical_accuracy` | Populated by Phase 33 FAISS — only non-zero after trades are resolved |
| `model_trace` | Populated by Kronos/Phase 33 — requires live model run |
| `xai_reasoning` | Populated by AI Validation Layer — requires consensus engine run |
| `intelligence_snapshot` | Populated at signal generation — requires active pipeline |

---

*Phase 36 Certification complete. Signed off by automated test suite.*
