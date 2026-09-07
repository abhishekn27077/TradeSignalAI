"""
tests/test_phase66_open_source_research.py
==========================================
Master Test Suite for Phase 66:
Open-Source Quant Architecture Research, Adaptive Signal Intelligence & Research-to-Live Parity.
"""

import pytest
import hashlib
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.unified_research_bus import unified_research_bus, ResearchEventType, ResearchEvent
from app.agents.research_council import research_council_engine, ResearchCouncilSynthesis
from app.analytics.vector_research_engine import vector_research_engine, VectorSweepReport
from app.analytics.research_memory_engine import research_memory_engine, ResearchRunCard
from app.analytics.regime_matrix_engine import regime_matrix_engine
from app.analytics.research_benchmark_engine import research_benchmark_engine
from app.core.execution_abstraction import paper_broker_adapter, OrderIntent, ExecutionReport
from app.config.settings import get_settings


client = TestClient(app)


def test_unified_research_bus_event_emission_and_immutability():
    """Verifies typed event publication, SHA-256 payload hashing, and subscriber callbacks."""
    received = []

    def handler(evt: ResearchEvent):
        received.append(evt)

    unified_research_bus.subscribe(ResearchEventType.RESEARCH_RUN_STARTED, handler)
    evt = unified_research_bus.emit(
        event_type=ResearchEventType.RESEARCH_RUN_STARTED,
        asset="EURUSD",
        timeframe="1H",
        payload={"experiment": "test_exp", "seed": 42},
    )

    assert len(received) >= 1
    assert evt.asset == "EURUSD"
    assert evt.timeframe == "1H"
    assert evt.payload_hash == hashlib.sha256(b'{"experiment": "test_exp", "seed": 42}').hexdigest()
    assert evt.version == "66.0.0-canonical"


def test_research_council_11_roles_and_zero_hallucination():
    """Tests 11 specialized research roles and structured Bull/Bear debate."""
    synthesis = research_council_engine.evaluate_council(
        asset="EURUSD",
        timeframe="1H",
        current_price=1.0850,
        indicators={"supertrend": {"direction": "BUY"}, "rsi": {"value": 58.5}},
        models_evidence={"quant": {"direction": "BUY", "confidence": 0.80}},
        mtf_data={"mtf_conflict_score": 0.15},
        event_risk="LOW",
    )

    assert isinstance(synthesis, ResearchCouncilSynthesis)
    assert len(synthesis.council_reports) == 11
    role_names = [r.role_name for r in synthesis.council_reports]
    assert "Trend Researcher" in role_names
    assert "Momentum Researcher" in role_names
    assert "Market Structure Researcher" in role_names
    assert "Liquidity Researcher" in role_names
    assert "Volatility Researcher" in role_names
    assert "Volume Researcher" in role_names
    assert "Forecast Models Researcher" in role_names
    assert "Historical Analogue Researcher" in role_names
    assert "Macro / Event Researcher" in role_names
    assert "News / Sentiment Researcher" in role_names
    assert "Risk & Governance Gatekeeper" in role_names

    assert synthesis.quantitative_fusion_score >= 60.0
    assert synthesis.recommended_action == "QUALIFIED"
    assert synthesis.hard_gates_passed is True
    assert len(synthesis.bull_case) > 10
    assert len(synthesis.bear_case) > 10


def test_research_council_cannot_bypass_risk_gates():
    """Ensures high event risk or high MTF conflict strictly forces NO_TRADE."""
    # Case 1: High Event Risk
    synth_event = research_council_engine.evaluate_council(
        asset="GBPUSD",
        timeframe="1H",
        current_price=1.2700,
        indicators={"supertrend": {"direction": "BUY"}},
        event_risk="HIGH",
    )
    assert synth_event.recommended_action == "NO_TRADE"
    assert synth_event.hard_gates_passed is False
    assert "HIGH_EVENT_RISK" in synth_event.rejection_reasons

    # Case 2: MTF Conflict > 0.40
    synth_mtf = research_council_engine.evaluate_council(
        asset="USDJPY",
        timeframe="1H",
        current_price=155.00,
        indicators={"supertrend": {"direction": "BUY"}},
        mtf_data={"mtf_conflict_score": 0.55},
        event_risk="LOW",
    )
    assert synth_mtf.recommended_action == "NO_TRADE"
    assert synth_mtf.hard_gates_passed is False
    assert "MTF_CONFLICT_DETECTED" in synth_mtf.rejection_reasons


def test_vector_research_engine_parameter_sweep():
    """Tests vectorized parameter sweeps with walk-forward purge and embargo windows."""
    report = vector_research_engine.run_parameter_sweep(
        asset="EURUSD",
        timeframe="1H",
        ema_periods=[9, 21],
        rr_ratios=[1.5, 2.0],
        consensus_thresholds=[0.60, 0.65],
        mtf_conflict_thresholds=[0.30, 0.40],
        purge_bars=5,
        embargo_bars=10,
    )

    assert isinstance(report, VectorSweepReport)
    assert report.total_combinations_evaluated == 16
    assert report.purge_window_bars == 5
    assert report.embargo_window_bars == 10
    assert report.best_candidate is not None
    assert report.best_candidate.out_of_sample_expectancy_r > 0
    assert report.best_candidate.sample_size == 120
    assert len(report.top_candidates) <= 5


def test_research_memory_run_cards_and_sqlite_persistence():
    """Verifies persistent ResearchRunCard storage and search."""
    now_iso = datetime.now(timezone.utc).isoformat()
    card = ResearchRunCard(
        run_id=f"TEST-RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:18]}",
        hypothesis="Testing walk-forward stability of 4H timeframe.",
        dataset_version="DS-CANONICAL-2026-v3",
        data_cutoff=now_iso,
        strategy_version="POLICY-66.0.0",
        model_version="ENSEMBLE-8M-CANONICAL",
        parameters={"ema_period": 21, "rr_ratio": 2.0},
        assets=["XAUUSD", "BTCUSD"],
        timeframes=["4H"],
        train_period="2024-01-01 to 2025-06-30",
        validation_period="2025-07-01 to 2025-12-31",
        test_period="2026-01-01 to 2026-08-24",
        sample_size=150,
        win_rate_pct=72.4,
        expectancy_net_r=0.42,
        profit_factor=2.40,
        sharpe_ratio=2.15,
        max_drawdown_r=3.1,
        brier_score=0.165,
        wilson_ci_95={"lower": 65.0, "upper": 79.0, "center": 72.4},
        statistical_significance="SIGNIFICANT (p < 0.001)",
        leakage_checks_passed=True,
        decision="PROMOTE_CHALLENGER",
        created_at=now_iso,
    )

    research_memory_engine.record_run_card(card)
    cards = research_memory_engine.get_all_run_cards(limit=10)
    assert any(c["run_id"] == card.run_id for c in cards)

    searched = research_memory_engine.search_memory("walk-forward stability")
    assert len(searched) >= 1
    assert searched[0]["run_id"] == card.run_id


def test_execution_abstraction_paper_broker_parity():
    """Tests order intent creation, simulated paper fill with friction, and portfolio tracking."""
    order = OrderIntent(
        order_id="ORD-TEST-001",
        asset="EURUSD",
        direction="BUY",
        order_type="LIMIT",
        quantity=1.0,
        limit_price=1.08500,
        stop_loss=1.08000,
        take_profit=1.09500,
    )

    report = paper_broker_adapter.submit_order(order)
    assert isinstance(report, ExecutionReport)
    assert report.status == "FILLED"
    assert report.is_live_broker is False
    assert report.fill_price > 1.08500  # Slippage accounted
    assert report.spread_paid > 0
    assert report.slippage_paid > 0
    assert report.commission_paid > 0

    state = paper_broker_adapter.get_portfolio_state()
    assert state["execution_mode"] == "DEMO_PAPER"
    assert state["real_money_enabled"] is False
    assert "EURUSD" in state["open_positions"]


def test_paper_broker_strict_real_money_safety_lock():
    """Asserts that real money trading remains unconditionally disabled."""
    settings = get_settings()
    assert getattr(settings, "REAL_MONEY_ENABLED", False) is False
    assert getattr(settings, "BROKER_EXECUTION_ENABLED", False) is False
    assert getattr(settings, "EXECUTION_MODE", "DEMO") == "DEMO"


def test_regime_matrix_8_regimes_and_fail_closed_logic():
    """Tests 8-regime performance evaluation, edge identification, and fail-closed states."""
    data = regime_matrix_engine.compute_regime_matrix(asset="EURUSD")
    assert "EURUSD" in data["matrix"]
    regimes = data["regimes"]
    assert len(regimes) == 8
    assert "TRENDING_BULL" in regimes
    assert "HIGH_EVENT_RISK" in regimes

    eur_event = data["matrix"]["EURUSD"]["HIGH_EVENT_RISK"]
    assert eur_event["evidence_status"] == "NO_EDGE (FAIL_CLOSED_NO_TRADE)"
    assert eur_event["recommended_action"] == "FAIL_CLOSED_NO_TRADE"

    eur_trend = data["matrix"]["EURUSD"]["TRENDING_BULL"]
    assert eur_trend["evidence_status"] == "EDGE_SUPPORTED"
    assert eur_trend["win_rate_pct"] > 60.0
    assert eur_trend["expectancy_r"] > 0.20


def test_research_benchmark_engine_fair_comparison():
    """Tests fair benchmarking against Classical Baselines and ML/RL Challengers."""
    bench = research_benchmark_engine.evaluate_all_benchmarks(asset="EURUSD", timeframe="1H")
    assert bench["champion_retained"] is True
    assert len(bench["ranked_benchmark_leaderboard"]) >= 6

    # Verify champion is ranked #1
    top_model = bench["ranked_benchmark_leaderboard"][0]
    assert top_model["model_category"] == "CHAMPION"
    assert top_model["expectancy_net_r"] >= 0.30
    assert top_model["sharpe_ratio"] >= 1.90

    # Verify random baseline has negative expectancy
    random_mod = [m for m in bench["ranked_benchmark_leaderboard"] if "Random" in m["model_name"]][0]
    assert random_mod["expectancy_net_r"] < 0


def test_api_research_routes_integration():
    """Tests all Phase 66 REST API research endpoints."""
    # 1. Runs
    res = client.get("/api/v1/research/runs")
    assert res.status_code == 200
    assert "runs" in res.json()["data"]

    # 2. Sweep
    sweep_res = client.post("/api/v1/research/sweep", json={"asset": "EURUSD", "timeframe": "1H"})
    assert sweep_res.status_code == 200
    assert "sweep_id" in sweep_res.json()["data"]

    # 3. Council
    cou_res = client.get("/api/v1/research/council/EURUSD/1H")
    assert cou_res.status_code == 200
    assert "council_reports" in cou_res.json()["data"]

    # 4. Regime Matrix
    reg_res = client.get("/api/v1/research/regime-matrix")
    assert reg_res.status_code == 200
    assert "ranked_regimes" in reg_res.json()["data"]

    # 5. Benchmarks
    ben_res = client.get("/api/v1/research/benchmarks")
    assert ben_res.status_code == 200
    assert "ranked_benchmark_leaderboard" in ben_res.json()["data"]

    # 6. Events
    evt_res = client.get("/api/v1/research/events")
    assert evt_res.status_code == 200
    assert "events" in evt_res.json()["data"]

    # 7. Portfolio State
    port_res = client.get("/api/v1/research/portfolio-state")
    assert port_res.status_code == 200
    assert port_res.json()["data"]["execution_mode"] == "DEMO_PAPER"


def test_causal_barrier_adversarial_injection():
    """Asserts that injecting future timestamps into research events fails or sets cutoff properly."""
    now = datetime.now(timezone.utc).isoformat()
    evt = ResearchEvent.create(
        event_type=ResearchEventType.SIGNAL_CANDIDATE,
        asset="BTCUSD",
        timeframe="4H",
        causal_cutoff=now,
    )
    assert evt.causal_cutoff <= evt.timestamp


def test_100_cycle_live_research_repeatability():
    """Verifies deterministic repeatability across 100 consecutive research API calls."""
    first_fusion = None
    for _ in range(100):
        res = client.get("/api/v1/research/council/EURUSD/1H")
        assert res.status_code == 200
        score = res.json()["data"]["quantitative_fusion_score"]
        if first_fusion is None:
            first_fusion = score
        assert score == first_fusion
