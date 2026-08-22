"""
Phase 40 — Economic Calendar & News Intelligence Tests.

Tests:
  1. Economic calendar event generation and filtering
  2. 3-way scenario generation (HOT / IN_LINE / COOL)
  3. Asset sensitivity matrices
  4. Event risk level assessment
  5. Historical statistics
  6. News classification and sentiment scoring
  7. Asset-keyword mapping
  8. Macro context building
"""
import pytest
from datetime import datetime, timedelta, timezone


class TestEconomicCalendar:
    """Tests for the Economic Calendar Engine."""

    @pytest.fixture
    def engine(self):
        from app.market_data.economic_calendar import EconomicCalendarEngine
        return EconomicCalendarEngine()

    def test_get_upcoming_events_today(self, engine):
        """Should return events for today."""
        events = engine.get_upcoming_events("today")
        assert isinstance(events, list)
        # All events should have required fields
        for event in events:
            assert "event_id" in event
            assert "event_name" in event
            assert "currency" in event
            assert "importance" in event
            assert "scheduled_utc" in event
            assert "countdown" in event
            assert "scheduled_ist" in event

    def test_get_upcoming_events_tomorrow(self, engine):
        """Should return events for tomorrow."""
        events = engine.get_upcoming_events("tomorrow")
        assert isinstance(events, list)

    def test_get_upcoming_events_week(self, engine):
        """Should return events for next 7 days."""
        events = engine.get_upcoming_events("week")
        assert isinstance(events, list)
        # Week should have more events than a single day
        today = engine.get_upcoming_events("today")
        # At minimum, week >= today
        assert len(events) >= len(today)

    def test_importance_filter(self, engine):
        """Should filter by importance level."""
        high = engine.get_upcoming_events("week", importance="HIGH")
        for event in high:
            assert event["importance"] == "HIGH"

    def test_currency_filter(self, engine):
        """Should filter by currency."""
        usd = engine.get_upcoming_events("week", currency="USD")
        for event in usd:
            assert event["currency"] == "USD"

    def test_scenario_generation(self, engine):
        """Scenarios should have HOT, IN_LINE, COOL keys."""
        event = {
            "template_key": "US_CPI",
            "forecast_value": 3.1,
            "previous_value": 3.3,
        }
        scenarios = engine.generate_scenarios(event)

        assert "HOT" in scenarios
        assert "IN_LINE" in scenarios
        assert "COOL" in scenarios

        # Each scenario should have probability and asset_reactions
        for key in ["HOT", "IN_LINE", "COOL"]:
            assert "probability" in scenarios[key]
            assert "asset_reactions" in scenarios[key]
            assert 0 <= scenarios[key]["probability"] <= 1

        # Probabilities should sum to ~1.0
        total_prob = sum(scenarios[k]["probability"] for k in ["HOT", "IN_LINE", "COOL"])
        assert abs(total_prob - 1.0) < 0.01

    def test_hot_scenario_has_asset_reactions(self, engine):
        """HOT scenario for CPI should include EURUSD, XAUUSD, NAS100 reactions."""
        event = {"template_key": "US_CPI", "forecast_value": 3.1, "previous_value": 3.3}
        scenarios = engine.generate_scenarios(event)

        hot_reactions = scenarios["HOT"]["asset_reactions"]
        assert "EURUSD" in hot_reactions
        assert hot_reactions["EURUSD"]["direction"] in ("BUY", "SELL")
        assert hot_reactions["EURUSD"]["expected_move_pips"] > 0

    def test_event_risk_level(self, engine):
        """Risk level should be a valid string."""
        valid_levels = {"NONE", "LOW", "MEDIUM", "HIGH", "EXTREME"}
        for asset in ["EURUSD", "BTCUSD", "XAUUSD"]:
            risk = engine.get_event_risk_level(asset, hours_ahead=24)
            assert risk in valid_levels, f"Invalid risk level '{risk}' for {asset}"

    def test_historical_stats(self, engine):
        """Should return historical stats for known event types."""
        stats = engine.get_historical_stats("US_CPI")
        assert stats["sample_size"] > 0
        assert "hot_pct" in stats
        assert "in_line_pct" in stats
        assert "cool_pct" in stats

    def test_unknown_event_stats(self, engine):
        """Unknown event type should return empty stats."""
        stats = engine.get_historical_stats("UNKNOWN_EVENT")
        assert stats.get("sample_size", 0) == 0

    def test_countdown_calculation(self, engine):
        """Countdown should be a string."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=5)
        countdown = engine._calculate_countdown(future, now)
        assert isinstance(countdown, str)
        assert "h" in countdown

        past = now - timedelta(hours=1)
        countdown_past = engine._calculate_countdown(past, now)
        assert countdown_past == "RELEASED"

    def test_utc_to_ist(self, engine):
        """UTC to IST conversion should add 5:30."""
        utc_time = datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc)
        ist_str = engine._utc_to_ist(utc_time)
        assert "IST" in ist_str
        assert "17:30" in ist_str  # 12:00 UTC = 17:30 IST

    def test_future_actual_always_none(self, engine):
        """Future events should NEVER have actual values (zero fabrication)."""
        events = engine.get_upcoming_events("tomorrow")
        for event in events:
            assert event.get("actual_value") is None, \
                f"Future event has actual value: {event['event_name']}"


class TestNewsIntelligence:
    """Tests for the News Intelligence Engine."""

    @pytest.fixture
    def engine(self):
        from app.news.intelligence import NewsIntelligenceEngine
        return NewsIntelligenceEngine()

    def test_process_article_returns_enriched(self, engine):
        """Processing an article should return all enriched fields."""
        article = {
            "title": "Fed raises interest rates by 25 basis points",
            "body": "The Federal Reserve raised rates amid inflation concerns.",
            "source": "reuters",
            "url": "https://example.com",
        }
        result = engine.process_article(article)

        assert "category" in result
        assert "sentiment_score" in result
        assert "sentiment_label" in result
        assert "affected_assets" in result
        assert "importance" in result
        assert "is_market_moving" in result

    def test_category_classification(self, engine):
        """Central bank news should be classified correctly."""
        article = {"title": "FOMC decides to hold interest rates steady"}
        result = engine.process_article(article)
        assert result["category"] == "CENTRAL_BANK"

    def test_inflation_classification(self, engine):
        """Inflation news should be classified as INFLATION."""
        article = {"title": "US CPI rises more than expected, inflation concerns grow"}
        result = engine.process_article(article)
        assert result["category"] == "INFLATION"

    def test_sentiment_positive(self, engine):
        """Positive news should have positive sentiment."""
        article = {"title": "Markets surge as rally continues, strong gains across the board"}
        result = engine.process_article(article)
        assert result["sentiment_score"] > 0

    def test_sentiment_negative(self, engine):
        """Negative news should have negative sentiment."""
        article = {"title": "Markets crash as fear grips Wall Street, plunge in stocks"}
        result = engine.process_article(article)
        assert result["sentiment_score"] < 0

    def test_sentiment_range(self, engine):
        """Sentiment score should be between -1 and 1."""
        articles = [
            {"title": "Everything surges"},
            {"title": "Everything crashes"},
            {"title": "Normal trading day"},
        ]
        for article in articles:
            result = engine.process_article(article)
            assert -1.0 <= result["sentiment_score"] <= 1.0

    def test_asset_mapping_gold(self, engine):
        """Gold-related news should map to XAUUSD."""
        article = {"title": "Gold prices surge to new highs"}
        result = engine.process_article(article)
        assert "XAUUSD" in result["affected_assets"]

    def test_asset_mapping_bitcoin(self, engine):
        """Bitcoin news should map to BTCUSD."""
        article = {"title": "Bitcoin rallies past 100K"}
        result = engine.process_article(article)
        assert "BTCUSD" in result["affected_assets"]

    def test_asset_mapping_fed(self, engine):
        """Fed news should map to multiple USD pairs."""
        article = {"title": "Fed raises rates, dollar strengthens"}
        result = engine.process_article(article)
        assert "EURUSD" in result["affected_assets"]
        assert "USDJPY" in result["affected_assets"]

    def test_deduplication(self, engine):
        """Batch processing should deduplicate identical titles."""
        articles = [
            {"title": "Market news today"},
            {"title": "Market news today"},
            {"title": "Different article"},
        ]
        results = engine.process_batch(articles)
        assert len(results) == 2  # Deduplicated

    def test_market_moving_detection(self, engine):
        """Market-moving news should be flagged."""
        article = {"title": "BREAKING: FOMC emergency rate cut"}
        result = engine.process_article(article)
        assert result["is_market_moving"] is True

    def test_asset_sentiment_aggregation(self, engine):
        """Should aggregate sentiment for a specific asset."""
        articles = [
            {"title": "Gold surges on safe haven demand", "affected_assets": ["XAUUSD"]},
            {"title": "Gold rally continues", "affected_assets": ["XAUUSD"]},
        ]
        processed = [engine.process_article(a) for a in articles]
        sentiment = engine.get_asset_sentiment(processed, "XAUUSD")

        assert sentiment["asset"] == "XAUUSD"
        assert sentiment["article_count"] == 2
        assert "sentiment_score" in sentiment

    def test_macro_context(self, engine):
        """Should build macro context from processed articles."""
        articles = [
            {"title": "Fed raises rates"},
            {"title": "Markets surge on optimism"},
        ]
        processed = engine.process_batch(articles)
        context = engine.get_macro_context(processed)

        assert "overall_sentiment" in context
        assert "overall_mood" in context
        assert context["overall_mood"] in ("RISK_ON", "RISK_OFF", "MIXED")
        assert "total_articles" in context
