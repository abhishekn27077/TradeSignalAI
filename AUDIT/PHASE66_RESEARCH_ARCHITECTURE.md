# AUDIT: PHASE 66 UNIFIED RESEARCH ARCHITECTURE
**Project:** TradeSignalAI-v3  
**Current Baseline:** Phase 66 Certified  

---

## 1. Unified Research Event Bus

The core research pipeline communicates via the immutable, typed `UnifiedResearchBus` (`app/core/unified_research_bus.py`).

### Key Event Lifecycle:
$$\begin{aligned}
\text{MARKET\_DATA\_RECEIVED} &\longrightarrow \text{INDICATOR\_EVALUATED} \\
&\longrightarrow \text{MODEL\_EVALUATED} \\
&\longrightarrow \text{RESEARCH\_COUNCIL\_DEBATE} \\
&\longrightarrow \text{SIGNAL\_CANDIDATE} \\
&\longrightarrow \text{QUANTITATIVE\_RISK\_GATE} \\
&\longrightarrow \text{SIGNAL\_QUALIFIED} \text{ or } \text{SIGNAL\_REJECTED}
\end{aligned}$$

Every event payload contains:
- `event_id`: Unique cryptographic identifier
- `event_type`: Typed enum
- `causal_cutoff`: Point-in-time barrier timestamp
- `payload_hash`: SHA-256 integrity digest
