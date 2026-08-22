# PHASE 45 — AI ANALYSIS, MODEL PROVENANCE & ENSEMBLE AUDIT

**Audit Scope:** Verification of LLM models, feature extractors, quantitative neural layers, consensus voting, and collinearity dampening.

---

## 1. Multi-Model Ensemble Architecture & Weights

| Model Layer | Model Name / Component | Input Dimensionality | Ensemble Weight | Fallback Policy |
|:---|:---|:---:|:---:|:---|
| **Technical Strat Ensemble** | 10 Strategy Families (SMC, Momentum, Trend, etc.) | 48 Feature Vectors | $0.25$ | Fail-closed ($0.0$) |
| **Quantitative ML Layer** | LightGBM / XGBoost Directional Classifier | 64 Numerical Features| $0.20$ | Fail-closed ($0.0$) |
| **Kronos Neural Engine** | Deep Temporal Transformer Sequence Model | 128 Candle Windows | $0.20$ | Fail-closed ($0.0$) |
| **FAISS Vector Memory** | Similar Historical Pattern Matcher | 512 Embeddings | $0.10$ | Fail-closed ($0.0$) |
| **Regime Classifier** | Gaussian HMM / Volatility Cluster Engine | ATR, ADX, Realized Vol| $0.10$ | `NEUTRAL` ($0.0$) |
| **Macro / News Analyzer** | Economic Event Analyzer + NLP Engine | Sentiment, Surprises | $0.10$ | `NEUTRAL` ($0.0$) |
| **AI LLM Reasoner** | Gemini / OpenAI Structured Prompting Engine | Complete Market Context| $0.05$ | Cached / Silent Skip |

---

## 2. Consensus Voting & Collinearity Dampening Formula

$$\text{Consensus Score} = \frac{\sum_{i=1}^{M} w_i \cdot \text{Vote}_i \cdot \frac{1}{\sqrt{K_{\text{cluster}(i)}}}}{\sum_{i=1}^{M} w_i \cdot \frac{1}{\sqrt{K_{\text{cluster}(i)}}}}$$

- **Supermajority Threshold:** Requires $\ge 60.0\%$ directional consensus across active clusters.
- **Fail-Closed Principle:** AI models never silently return fake BUY/SELL signals on API failure; missing responses drop weight to $0.0$ and trigger `MODEL_CONSENSUS_UNAVAILABLE`.
- **Verdict:** `AI_AND_ENSEMBLE_VERIFIED`.
