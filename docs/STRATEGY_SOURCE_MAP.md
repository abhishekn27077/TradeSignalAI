# Phase 51 Strategy Source & Subsystem Architecture Map

**System:** TradeSignalAI-v3 Market Intelligence & Quantitative Strategy Platform  
**Purpose:** End-to-End Traceability Matrix from Research Concept to Production Frontend Component

---

## Complete Subsystem Traceability Matrix

| Research Concept / TradingView Source | TradeSignalAI Implementation Subsystem | Python Backend Module Path | Pytest Unit / Integration Test Module | REST API Endpoint | Frontend Dashboard Component |
|:---|:---|:---|:---|:---|:---|
| **Market Structure (LuxAlgo / Joy_Bangla)** | SwingDetector, BOS/CHoCH Engine, MSB & Structure Strength | `app/Strategies/Structure/` (`swing.py`, `bos_choch.py`, `msb.py`, `strength.py`) | `tests/test_phase51_structure.py` | `GET /api/v1/analysis/structure/{asset}` | `frontend/src/components/analysis/StructurePanel.tsx` |
| **Order Blocks (LuxAlgo / Smart Money)** | Order Block Lifecycle (Bullish, Bearish, Breaker, Mitigation) | `app/Strategies/SmartMoney/OrderBlocks/` (`order_block_engine.py`) | `tests/test_phase51_order_blocks.py` | `GET /api/v1/analysis/smart-money/{asset}` | `frontend/src/components/analysis/OrderBlockPanel.tsx` |
| **Fair Value Gaps (FVG)** | Bullish/Bearish FVG, ATR Normalization & Mitigation Tracking | `app/Strategies/SmartMoney/FVG/` (`fvg_engine.py`) | `tests/test_phase51_fvg.py` | `GET /api/v1/analysis/smart-money/{asset}` | `frontend/src/components/analysis/FVGPanel.tsx` |
| **Liquidity & Sweeps (SMC / TFO)** | Equal Highs/Lows, Prior Day/Week/Month High/Low, Sweep Detector | `app/Strategies/SmartMoney/Liquidity/` (`liquidity_engine.py`, `sweep_detector.py`) | `tests/test_phase51_liquidity.py` | `GET /api/v1/analysis/liquidity/{asset}` | `frontend/src/components/analysis/LiquidityPanel.tsx` |
| **Premium & Discount Ranges** | Active Dealing Range & 50% Equilibrium Engine | `app/Strategies/SmartMoney/PremiumDiscount/` (`range_engine.py`) | `tests/test_phase51_premium_discount.py` | `GET /api/v1/analysis/smart-money/{asset}` | `frontend/src/components/analysis/DealingRangePanel.tsx` |
| **ICT Killzones & Sessions (TFO / yusin99)** | Asia, London, NY AM/PM Killzones & Volatility Profiling | `app/Strategies/Session/` (`session_engine.py`) | `tests/test_phase51_sessions.py` | `GET /api/v1/analysis/sessions/{asset}` | `frontend/src/components/analysis/SessionPanel.tsx` |
| **SMT & Correlation Divergence** | Cross-Pair Divergence (e.g. XAUUSD vs DXY, EURUSD vs DXY) | `app/Strategies/Correlation/` (`smt_engine.py`, `correlation_engine.py`) | `tests/test_phase51_smt.py` | `GET /api/v1/analysis/correlation/{asset}` | `frontend/src/components/analysis/SMTPanel.tsx` |
| **Technical Evidence (SuperTrend / UT Bot / MACD+SMA)** | Structured Indicator Evidence (ADX, ATR, RSI, SuperTrend, UT Bot, VWAP) | `app/Strategies/Technical/` (`technical_evidence_engine.py`, `indicators.py`) | `tests/test_phase51_technical_evidence.py` | `GET /api/v1/analysis/technical/{asset}` | `frontend/src/components/analysis/TechnicalEvidencePanel.tsx` |
| **Market Regime Engine** | Multi-Factor Regime Classification (Trend, Range, Breakout, Volatility) | `app/Strategies/Regime/` (`regime_classifier.py`) | `tests/test_phase51_regime.py` | `GET /api/v1/analysis/regime/{asset}` | `frontend/src/components/analysis/RegimeBadge.tsx` |
| **Multi-Timeframe Hierarchy** | HTF Bias, MTF Structure, LTF Entry Confirmation | `app/Strategies/MTF/` (`mtf_engine.py`) | `tests/test_phase51_mtf.py` | `GET /api/v1/analysis/multi-timeframe/{asset}` | `frontend/src/components/analysis/MTFMatrix.tsx` |
| **Strategy Router** | Regime-Specific Strategy Dispatcher (Trending, Ranging, Breakout, SMC) | `app/Strategies/Router/` (`strategy_router.py`) | `tests/test_phase51_strategy_router.py` | `GET /api/v1/analysis/strategies/{asset}` | `frontend/src/components/analysis/StrategyRouterPanel.tsx` |
| **Confluence Scoring Engine** | Multi-Factor Dynamic Weighted Confluence (0-100) | `app/Strategies/Confluence/` (`confluence_engine.py`) | `tests/test_phase51_confluence.py` | `GET /api/v1/analysis/confluence/{asset}` | `frontend/src/components/analysis/ConfluenceGauge.tsx` |
| **Signal Explanation Engine** | Structured "Why / Risk / Invalidation" Evidence Tree | `app/Strategies/Explanation/` (`explanation_engine.py`) | `tests/test_phase51_explanation.py` | `GET /api/v1/analysis/explanation/{signal_id}` | `frontend/src/components/signals/SignalExplanationCard.tsx` |
| **Walk-Forward & Backtesting** | Realistic Backtester (Spread, Slippage, Latency), Ablation & Monte Carlo | `app/Strategies/Backtesting/` (`engine.py`, `walk_forward.py`, `ablation.py`, `monte_carlo.py`) | `tests/test_phase51_backtesting.py` | `GET /api/v1/analysis/performance/{asset}` | `frontend/src/components/analysis/PerformanceMatrix.tsx` |
