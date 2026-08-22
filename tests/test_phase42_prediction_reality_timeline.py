"""
Phase 42 — Test Suite for Prediction Reality Scorecards & Forecast Timelines.

Verifies:
  - Today's Prediction Score, 7D Score, 30D Score
  - Asset-by-asset and Model-by-model accuracy scorecards
  - Non-destructive news catalyst version updates (V1 -> V2)
  - Chronological forecast evolution timeline retrieval
"""
import pytest
from app.analytics.prediction_reality_engine import prediction_reality_engine
from app.analytics.forecast_timeline_engine import forecast_timeline_engine, CORE_ASSETS


class TestPredictionRealityAndTimeline:
    def test_prediction_reality_scorecards(self):
        res = prediction_reality_engine.get_scorecards()
        assert "today_prediction_score" in res
        assert 0 <= res["today_prediction_score"] <= 100

        assert "score_7d_rolling" in res
        assert "score_30d_rolling" in res
        assert "overall_grade" in res

        # Verify asset scorecards
        assert "asset_scores" in res
        for asset in CORE_ASSETS:
            assert asset in res["asset_scores"]
            score_info = res["asset_scores"][asset]
            assert "score" in score_info
            assert "directional_accuracy_pct" in score_info
            assert "brier_score" in score_info
            assert "resolved_forecasts" in score_info

        # Verify model scores
        assert "model_scores" in res
        assert "Quant Baseline" in res["model_scores"]
        assert "Full Consensus Ensemble" in res["model_scores"]
        assert res["model_scores"]["Full Consensus Ensemble"]["accuracy_pct"] > res["model_scores"]["Quant Baseline"]["accuracy_pct"]

    def test_forecast_timeline_retrieval(self):
        for asset in ["EURUSD", "BTCUSD", "XAUUSD"]:
            timeline = forecast_timeline_engine.get_forecast_timeline(asset)
            assert timeline["asset"] == asset
            assert "events" in timeline
            assert len(timeline["events"]) >= 3

            for ev in timeline["events"]:
                assert "timestamp" in ev
                assert "event_type" in ev
                assert "title" in ev

    def test_news_catalyst_version_spawn(self):
        old_fc = {
            "forecast_id": "FS-EURUSD-20260820-v1",
            "direction": "NEUTRAL",
            "confidence": 0.50,
        }
        news_cat = {
            "id": "news-12345",
            "headline": "Fed Signals Pause as Inflation Moderates",
            "sentiment_score": 0.55,
        }
        new_fc = {
            "direction": "BUY",
            "confidence": 0.74,
            "is_trade_signal_qualified": True,
        }

        ver_rec = forecast_timeline_engine.record_news_catalyst_update(
            asset="EURUSD",
            news_catalyst=news_cat,
            old_forecast=old_fc,
            new_forecast=new_fc,
        )

        assert ver_rec["asset"] == "EURUSD"
        assert ver_rec["catalyst_type"] == "NEWS_CATALYST"
        assert ver_rec["old_forecast_direction"] == "NEUTRAL"
        assert ver_rec["new_forecast_direction"] == "BUY"
        assert ver_rec["new_forecast_confidence"] == 0.74
        assert "input_hash" in ver_rec
        assert len(ver_rec["input_hash"]) == 64

        # Verify timeline received the event
        tl = forecast_timeline_engine.get_forecast_timeline("EURUSD")
        assert any(e.get("input_hash") == ver_rec["input_hash"] for e in tl["events"])
