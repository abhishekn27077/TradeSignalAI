# 07 — Quant Model Audit & Machine Learning Ensemble
**Phase 37 Certification: TradeSignalAI-v3**

---

## 1. Quantitative Ensemble Composition
The quantitative statistical layer aggregates three diverse gradient-boosted decision tree families:
1. **HistGradientBoosting (15% Consensus Weight):** Highly efficient binned tree learner optimized for dense indicator feature vectors.
2. **XGBoost (15% Consensus Weight):** Regularized gradient booster optimizing for sharp directional transitions.
3. **RandomForest (10% Consensus Weight):** Bagging ensemble reducing variance across noisy market regimes.

---

## 2. Quantitative Signal Generation
- Each tree model outputs continuous expected return forecasts and directional classifications ($[-1.0, +1.0]$).
- Inter-model agreement percentage is computed dynamically across the tree predictions.
- If inter-model agreement $< 65\%$, the quant baseline outputs `NEUTRAL`, enforcing zero-trust discipline.
- Status: **PASSED & VERIFIED**.
