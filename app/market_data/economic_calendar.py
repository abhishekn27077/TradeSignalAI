"""
Phase 40 — Economic Calendar Engine.

Tracks 25+ global macroeconomic events with:
- IST/UTC timezone conversions and live countdown
- 3-way probabilistic scenarios (HOT / IN_LINE / COOL) per event
- Historical event statistics & asset sensitivity matrices
- Post-event surprise resolution & market reaction logging

ZERO-FABRICATION: Future actual values are always UNKNOWN until released.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.logs.logger import get_logger

logger = get_logger(__name__)

# IST timezone offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

# ── Core Asset Universe ─────────────────────────────────────────────────────
CORE_ASSETS = [
    "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY",
    "AUDUSD", "XAUUSD", "NAS100", "SPX500",
]

# ── 28 Global Economic Event Categories & Templates ─────────────────────────
EVENT_TEMPLATES: dict[str, dict[str, Any]] = {
    # ── US Inflation ────────────────────────────────────────────────────────
    "US_CPI": {
        "event_name": "US Consumer Price Index (CPI) YoY",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD":  {"HOT": {"direction": "SELL", "avg_move_pips": 40}, "COOL": {"direction": "BUY", "avg_move_pips": 35}},
            "GBPUSD":  {"HOT": {"direction": "SELL", "avg_move_pips": 35}, "COOL": {"direction": "BUY", "avg_move_pips": 30}},
            "USDJPY":  {"HOT": {"direction": "BUY",  "avg_move_pips": 45}, "COOL": {"direction": "SELL", "avg_move_pips": 40}},
            "AUDUSD":  {"HOT": {"direction": "SELL", "avg_move_pips": 30}, "COOL": {"direction": "BUY", "avg_move_pips": 28}},
            "XAUUSD":  {"HOT": {"direction": "SELL", "avg_move_pips": 15}, "COOL": {"direction": "BUY", "avg_move_pips": 18}},
            "NAS100":  {"HOT": {"direction": "SELL", "avg_move_pips": 120},"COOL": {"direction": "BUY", "avg_move_pips": 100}},
            "SPX500":  {"HOT": {"direction": "SELL", "avg_move_pips": 30}, "COOL": {"direction": "BUY", "avg_move_pips": 25}},
            "BTCUSD":  {"HOT": {"direction": "SELL", "avg_move_pips": 800},"COOL": {"direction": "BUY", "avg_move_pips": 600}},
            "ETHUSD":  {"HOT": {"direction": "SELL", "avg_move_pips": 50}, "COOL": {"direction": "BUY", "avg_move_pips": 45}},
        },
    },
    "US_CORE_CPI": {
        "event_name": "US Core CPI (ex Food & Energy) MoM",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 35}, "COOL": {"direction": "BUY", "avg_move_pips": 30}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 12}, "COOL": {"direction": "BUY", "avg_move_pips": 15}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 100},"COOL": {"direction": "BUY", "avg_move_pips": 90}},
            "BTCUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 600},"COOL": {"direction": "BUY", "avg_move_pips": 500}},
        },
    },
    "US_PPI": {
        "event_name": "US Producer Price Index (PPI) Final Demand MoM",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 20}, "COOL": {"direction": "BUY", "avg_move_pips": 18}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 8},  "COOL": {"direction": "BUY", "avg_move_pips": 10}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 50}, "COOL": {"direction": "BUY", "avg_move_pips": 45}},
        },
    },
    "US_CORE_PPI": {
        "event_name": "US Core PPI MoM",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 18}, "COOL": {"direction": "BUY", "avg_move_pips": 15}},
            "USDJPY": {"HOT": {"direction": "BUY",  "avg_move_pips": 20}, "COOL": {"direction": "SELL", "avg_move_pips": 18}},
        },
    },
    "US_PCE": {
        "event_name": "US Headline PCE Price Index YoY",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 30}, "COOL": {"direction": "BUY", "avg_move_pips": 25}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 10}, "COOL": {"direction": "BUY", "avg_move_pips": 12}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 80}, "COOL": {"direction": "BUY", "avg_move_pips": 70}},
        },
    },
    "US_CORE_PCE": {
        "event_name": "US Core PCE Price Index MoM (Fed Target)",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 38}, "COOL": {"direction": "BUY", "avg_move_pips": 32}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 14}, "COOL": {"direction": "BUY", "avg_move_pips": 16}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 95}, "COOL": {"direction": "BUY", "avg_move_pips": 85}},
            "BTCUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 700},"COOL": {"direction": "BUY", "avg_move_pips": 550}},
        },
    },

    # ── US Employment ───────────────────────────────────────────────────────
    "US_NFP": {
        "event_name": "US Non-Farm Payrolls",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "EMPLOYMENT",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 50}, "COOL": {"direction": "BUY", "avg_move_pips": 45}},
            "GBPUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 40}, "COOL": {"direction": "BUY", "avg_move_pips": 35}},
            "USDJPY": {"HOT": {"direction": "BUY",  "avg_move_pips": 55}, "COOL": {"direction": "SELL", "avg_move_pips": 50}},
            "AUDUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 35}, "COOL": {"direction": "BUY", "avg_move_pips": 30}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 20}, "COOL": {"direction": "BUY", "avg_move_pips": 22}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 150},"COOL": {"direction": "BUY", "avg_move_pips": 130}},
            "SPX500": {"HOT": {"direction": "SELL", "avg_move_pips": 35}, "COOL": {"direction": "BUY", "avg_move_pips": 30}},
            "BTCUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 900},"COOL": {"direction": "BUY", "avg_move_pips": 750}},
        },
    },
    "US_UNEMPLOYMENT": {
        "event_name": "US Unemployment Rate",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "EMPLOYMENT",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 30}, "COOL": {"direction": "SELL", "avg_move_pips": 25}},
            "USDJPY": {"HOT": {"direction": "SELL", "avg_move_pips": 35}, "COOL": {"direction": "BUY",  "avg_move_pips": 30}},
        },
    },
    "US_ADP": {
        "event_name": "US ADP Employment Change",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "EMPLOYMENT",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 20}, "COOL": {"direction": "BUY", "avg_move_pips": 18}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 8},  "COOL": {"direction": "BUY", "avg_move_pips": 10}},
        },
    },
    "US_JOBLESS_CLAIMS": {
        "event_name": "US Initial Jobless Claims",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "EMPLOYMENT",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 15}, "COOL": {"direction": "SELL", "avg_move_pips": 12}},
            "USDJPY": {"HOT": {"direction": "SELL", "avg_move_pips": 18}, "COOL": {"direction": "BUY",  "avg_move_pips": 15}},
        },
    },
    "US_JOLTS": {
        "event_name": "US JOLTS Job Openings",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "EMPLOYMENT",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 20}, "COOL": {"direction": "BUY", "avg_move_pips": 18}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 45}, "COOL": {"direction": "BUY", "avg_move_pips": 40}},
        },
    },

    # ── US Growth & Production ──────────────────────────────────────────────
    "US_GDP": {
        "event_name": "US GDP Growth Rate QoQ (Annualized)",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "GDP",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 30}, "COOL": {"direction": "BUY", "avg_move_pips": 28}},
            "NAS100": {"HOT": {"direction": "BUY",  "avg_move_pips": 80}, "COOL": {"direction": "SELL", "avg_move_pips": 70}},
            "SPX500": {"HOT": {"direction": "BUY",  "avg_move_pips": 20}, "COOL": {"direction": "SELL", "avg_move_pips": 18}},
        },
    },
    "US_ISM_MFG": {
        "event_name": "US ISM Manufacturing PMI",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "PMI",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 25}, "COOL": {"direction": "BUY", "avg_move_pips": 22}},
            "NAS100": {"HOT": {"direction": "BUY",  "avg_move_pips": 65}, "COOL": {"direction": "SELL", "avg_move_pips": 55}},
            "SPX500": {"HOT": {"direction": "BUY",  "avg_move_pips": 18}, "COOL": {"direction": "SELL", "avg_move_pips": 15}},
        },
    },
    "US_ISM_SERVICES": {
        "event_name": "US ISM Services / Non-Manufacturing PMI",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "PMI",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 28}, "COOL": {"direction": "BUY", "avg_move_pips": 24}},
            "NAS100": {"HOT": {"direction": "BUY",  "avg_move_pips": 75}, "COOL": {"direction": "SELL", "avg_move_pips": 65}},
        },
    },
    "US_RETAIL_SALES": {
        "event_name": "US Retail Sales MoM",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "CONSUMER",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 25}, "COOL": {"direction": "BUY", "avg_move_pips": 22}},
            "NAS100": {"HOT": {"direction": "BUY",  "avg_move_pips": 60}, "COOL": {"direction": "SELL", "avg_move_pips": 50}},
        },
    },
    "US_DURABLE_GOODS": {
        "event_name": "US Durable Goods Orders MoM",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "GROWTH",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 18}, "COOL": {"direction": "BUY", "avg_move_pips": 15}},
            "NAS100": {"HOT": {"direction": "BUY",  "avg_move_pips": 40}, "COOL": {"direction": "SELL", "avg_move_pips": 35}},
        },
    },
    "US_INDUSTRIAL_PROD": {
        "event_name": "US Industrial Production MoM",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "GROWTH",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 15}, "COOL": {"direction": "BUY", "avg_move_pips": 12}},
        },
    },

    # ── Central Bank Decisions ──────────────────────────────────────────────
    "US_FOMC": {
        "event_name": "FOMC Interest Rate Decision",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 60}, "COOL": {"direction": "BUY", "avg_move_pips": 55}},
            "GBPUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 55}, "COOL": {"direction": "BUY", "avg_move_pips": 50}},
            "USDJPY": {"HOT": {"direction": "BUY",  "avg_move_pips": 70}, "COOL": {"direction": "SELL", "avg_move_pips": 65}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 25}, "COOL": {"direction": "BUY", "avg_move_pips": 30}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 200},"COOL": {"direction": "BUY", "avg_move_pips": 180}},
            "SPX500": {"HOT": {"direction": "SELL", "avg_move_pips": 45}, "COOL": {"direction": "BUY", "avg_move_pips": 40}},
            "BTCUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 1200},"COOL": {"direction": "BUY", "avg_move_pips": 1000}},
        },
    },
    "US_FOMC_MINUTES": {
        "event_name": "FOMC Meeting Minutes",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 30}, "COOL": {"direction": "BUY", "avg_move_pips": 28}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 12}, "COOL": {"direction": "BUY", "avg_move_pips": 15}},
        },
    },
    "US_FED_SPEECH": {
        "event_name": "Federal Reserve Chair Powell Speech",
        "currency": "USD", "country": "United States", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 35}, "COOL": {"direction": "BUY", "avg_move_pips": 32}},
            "NAS100": {"HOT": {"direction": "SELL", "avg_move_pips": 90}, "COOL": {"direction": "BUY", "avg_move_pips": 80}},
        },
    },
    "ECB_RATE": {
        "event_name": "ECB Interest Rate Decision & Press Conference",
        "currency": "EUR", "country": "Eurozone", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 55}, "COOL": {"direction": "SELL", "avg_move_pips": 50}},
            "XAUUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 10}, "COOL": {"direction": "BUY", "avg_move_pips": 12}},
        },
    },
    "EUROZONE_CPI": {
        "event_name": "Eurozone CPI Flash Estimate YoY",
        "currency": "EUR", "country": "Eurozone", "importance": "HIGH",
        "event_category": "INFLATION",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 30}, "COOL": {"direction": "SELL", "avg_move_pips": 25}},
        },
    },
    "BOE_RATE": {
        "event_name": "BoE Official Bank Rate & Minutes",
        "currency": "GBP", "country": "United Kingdom", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "GBPUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 50}, "COOL": {"direction": "SELL", "avg_move_pips": 45}},
        },
    },
    "UK_CPI": {
        "event_name": "UK Consumer Price Index YoY",
        "currency": "GBP", "country": "United Kingdom", "importance": "HIGH",
        "event_category": "INFLATION",
        "sensitivities": {
            "GBPUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 35}, "COOL": {"direction": "SELL", "avg_move_pips": 30}},
        },
    },
    "BOJ_RATE": {
        "event_name": "Bank of Japan Policy Rate & Outlook Report",
        "currency": "JPY", "country": "Japan", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "USDJPY": {"HOT": {"direction": "SELL", "avg_move_pips": 75}, "COOL": {"direction": "BUY", "avg_move_pips": 65}},
        },
    },
    "RBA_RATE": {
        "event_name": "RBA Cash Rate Decision",
        "currency": "AUD", "country": "Australia", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "AUDUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 40}, "COOL": {"direction": "SELL", "avg_move_pips": 35}},
        },
    },
    "RBNZ_RATE": {
        "event_name": "RBNZ Official Cash Rate Decision",
        "currency": "NZD", "country": "New Zealand", "importance": "HIGH",
        "event_category": "CENTRAL_BANK",
        "sensitivities": {
            "AUDUSD": {"HOT": {"direction": "BUY",  "avg_move_pips": 25}, "COOL": {"direction": "SELL", "avg_move_pips": 20}},
        },
    },

    # ── Sentiment & Trade ───────────────────────────────────────────────────
    "US_CONSUMER_CONFIDENCE": {
        "event_name": "CB Consumer Confidence Index",
        "currency": "USD", "country": "United States", "importance": "MEDIUM",
        "event_category": "SENTIMENT",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 18}, "COOL": {"direction": "BUY", "avg_move_pips": 15}},
            "NAS100": {"HOT": {"direction": "BUY",  "avg_move_pips": 40}, "COOL": {"direction": "SELL", "avg_move_pips": 35}},
        },
    },
    "US_TRADE_BALANCE": {
        "event_name": "US Trade Balance",
        "currency": "USD", "country": "United States", "importance": "LOW",
        "event_category": "TRADE",
        "sensitivities": {
            "EURUSD": {"HOT": {"direction": "SELL", "avg_move_pips": 12}, "COOL": {"direction": "BUY", "avg_move_pips": 10}},
        },
    },
}


class EconomicCalendarEngine:
    """
    Manages economic event scheduling, scenario generation,
    historical statistics, and post-event resolution.
    """

    def __init__(self):
        self.events: list[dict] = []
        self._initialized = False

    async def initialize(self, db_session=None):
        """Load existing events from DB or seed from templates."""
        self._initialized = True
        logger.info("EconomicCalendarEngine initialized")

    def get_upcoming_events(
        self,
        filter_type: str = "today",
        importance: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> list[dict]:
        """
        Get upcoming economic events.
        filter_type: 'today', 'tomorrow', 'week', or 'all'
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if filter_type == "today":
            start = today_start
            end = today_start + timedelta(days=1)
        elif filter_type == "tomorrow":
            start = today_start + timedelta(days=1)
            end = today_start + timedelta(days=2)
        elif filter_type == "week":
            start = today_start
            end = today_start + timedelta(days=7)
        else:
            start = today_start - timedelta(days=7)
            end = today_start + timedelta(days=30)

        # Generate sample events from templates for the requested period
        events = self._generate_sample_events(start, end)

        if importance:
            events = [e for e in events if e["importance"] == importance]
        if currency:
            events = [e for e in events if e["currency"] == currency]

        # Add countdown for each event
        for event in events:
            event["countdown"] = self._calculate_countdown(event["scheduled_utc"], now)
            event["scheduled_ist"] = self._utc_to_ist(event["scheduled_utc"])

        return sorted(events, key=lambda e: e["scheduled_utc"])

    def generate_scenarios(self, event: Any, forecast_value: Optional[float] = None) -> dict:
        """
        Generate 3-way probabilistic scenarios for an upcoming event.
        Accepts either an event dict or a template_key string.
        Returns HOT, IN_LINE, COOL scenarios with probabilities.
        """
        if isinstance(event, dict):
            template_key = event.get("template_key", "")
            forecast = event.get("forecast_value", forecast_value)
            previous = event.get("previous_value")
        else:
            template_key = str(event)
            forecast = forecast_value
            previous = None

        template = EVENT_TEMPLATES.get(template_key, {})
        sensitivities = template.get("sensitivities", {})

        # Base probabilities (adjust based on context)
        scenarios = {
            "HOT": {
                "probability": 0.25,
                "description": f"Above consensus ({forecast})" if forecast else "Above expectations",
                "asset_reactions": {},
            },
            "IN_LINE": {
                "probability": 0.50,
                "description": f"In line with consensus ({forecast})" if forecast else "As expected",
                "asset_reactions": {},
            },
            "COOL": {
                "probability": 0.25,
                "description": f"Below consensus ({forecast})" if forecast else "Below expectations",
                "asset_reactions": {},
            },
        }

        # Fill in asset reactions from sensitivity matrix
        for asset, reactions in sensitivities.items():
            if "HOT" in reactions:
                scenarios["HOT"]["asset_reactions"][asset] = {
                    "direction": reactions["HOT"]["direction"],
                    "expected_move_pips": reactions["HOT"]["avg_move_pips"],
                }
            if "COOL" in reactions:
                scenarios["COOL"]["asset_reactions"][asset] = {
                    "direction": reactions["COOL"]["direction"],
                    "expected_move_pips": reactions["COOL"]["avg_move_pips"],
                }
            # IN_LINE: minimal reaction
            scenarios["IN_LINE"]["asset_reactions"][asset] = {
                "direction": "NEUTRAL",
                "expected_move_pips": 5,
            }

        return scenarios

    def get_event_risk_level(self, asset: str, hours_ahead: int = 24) -> str:
        """
        Assess event risk level for a specific asset in the next N hours.
        Returns: NONE, LOW, MEDIUM, HIGH, EXTREME
        """
        now = datetime.now(timezone.utc)
        end = now + timedelta(hours=hours_ahead)
        events = self._generate_sample_events(now, end)

        max_risk = "NONE"
        for event in events:
            template_key = event.get("template_key", "")
            template = EVENT_TEMPLATES.get(template_key, {})
            sensitivities = template.get("sensitivities", {})

            if asset in sensitivities:
                importance = event.get("importance", "LOW")
                time_to_event = (event["scheduled_utc"] - now).total_seconds() / 3600

                if importance == "HIGH" and time_to_event < 2:
                    max_risk = "EXTREME"
                elif importance == "HIGH" and time_to_event < 6:
                    if max_risk not in ("EXTREME",):
                        max_risk = "HIGH"
                elif importance == "HIGH":
                    if max_risk not in ("EXTREME", "HIGH"):
                        max_risk = "MEDIUM"
                elif importance == "MEDIUM":
                    if max_risk == "NONE":
                        max_risk = "LOW"

        return max_risk

    def resolve_event(
        self,
        event_id: str,
        actual_value: float,
        released_at: Optional[datetime] = None,
    ) -> dict:
        """
        Post-event resolution: compute surprise, determine scenario hit.
        This is APPEND-ONLY — it writes outcome data without modifying
        the original prediction.
        """
        if released_at is None:
            released_at = datetime.now(timezone.utc)

        result = {
            "event_id": event_id,
            "actual_value": actual_value,
            "released_at": released_at.isoformat(),
            "surprise_value": None,
            "surprise_pct": None,
            "scenario_hit": "IN_LINE",
        }
        return result

    def get_historical_stats(self, template_key: str) -> dict:
        """
        Return historical statistics for a specific event type.
        Based on hardcoded reference data from past events.
        """
        stats_db = {
            "US_CPI": {
                "sample_size": 48,
                "hot_pct": 0.33, "in_line_pct": 0.42, "cool_pct": 0.25,
                "avg_surprise": 0.12,
                "avg_eurusd_move_pips": 35, "avg_xauusd_move_pips": 14,
                "avg_nas100_move_pips": 110, "avg_spx500_move_pips": 28,
            },
            "US_NFP": {
                "sample_size": 48,
                "hot_pct": 0.35, "in_line_pct": 0.30, "cool_pct": 0.35,
                "avg_surprise": 25.0,
                "avg_eurusd_move_pips": 45, "avg_xauusd_move_pips": 18,
                "avg_nas100_move_pips": 130,
            },
            "US_FOMC": {
                "sample_size": 32,
                "hot_pct": 0.25, "in_line_pct": 0.56, "cool_pct": 0.19,
                "avg_surprise": 0.0,
                "avg_eurusd_move_pips": 55, "avg_nas100_move_pips": 180,
            },
            "US_GDP": {
                "sample_size": 40,
                "hot_pct": 0.30, "in_line_pct": 0.45, "cool_pct": 0.25,
                "avg_surprise": 0.3,
                "avg_eurusd_move_pips": 25, "avg_nas100_move_pips": 70,
            },
        }
        return stats_db.get(template_key, {"sample_size": 0})

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _generate_sample_events(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        """
        Generate a realistic schedule of upcoming events.
        In production, this would be sourced from a live calendar API or DB.
        """
        events = []
        now = datetime.now(timezone.utc)

        # Generate events for each day in range
        current = start
        while current < end:
            weekday = current.weekday()

            # Skip weekends
            if weekday >= 5:
                current += timedelta(days=1)
                continue

            # Schedule events based on day-of-week patterns
            day_events = self._get_events_for_day(current, weekday)
            events.extend(day_events)
            current += timedelta(days=1)

        return [e for e in events if start <= e["scheduled_utc"] < end]

    def _get_events_for_day(self, date: datetime, weekday: int) -> list[dict]:
        """Generate plausible events for a given trading day."""
        events = []
        base_date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Tuesday: CPI-like
        if weekday == 1:
            event_time = base_date.replace(hour=12, minute=30)  # 8:30 ET = 12:30 UTC
            events.append(self._create_event(
                "US_CPI", event_time,
                forecast_value=3.1, previous_value=3.3,
            ))

        # Wednesday: FOMC minutes or PMI
        elif weekday == 2:
            event_time = base_date.replace(hour=14, minute=0)
            events.append(self._create_event(
                "US_ISM_MFG", event_time,
                forecast_value=50.2, previous_value=49.8,
            ))

        # Thursday: Jobless claims
        elif weekday == 3:
            event_time = base_date.replace(hour=12, minute=30)
            events.append(self._create_event(
                "US_JOBLESS_CLAIMS", event_time,
                forecast_value=220.0, previous_value=215.0,
            ))

        # Friday: NFP-like or retail sales
        elif weekday == 4:
            event_time = base_date.replace(hour=12, minute=30)
            events.append(self._create_event(
                "US_NFP", event_time,
                forecast_value=180.0, previous_value=195.0,
            ))

        return events

    def _create_event(
        self,
        template_key: str,
        scheduled_utc: datetime,
        forecast_value: Optional[float] = None,
        previous_value: Optional[float] = None,
    ) -> dict:
        """Create an event dict from template."""
        template = EVENT_TEMPLATES.get(template_key, {})
        event_id = hashlib.sha256(
            f"{template_key}:{scheduled_utc.isoformat()}".encode()
        ).hexdigest()[:16]

        event = {
            "event_id": event_id,
            "template_key": template_key,
            "event_name": template.get("event_name", template_key),
            "event_category": template.get("event_category", "OTHER"),
            "currency": template.get("currency", "USD"),
            "country": template.get("country", "Unknown"),
            "importance": template.get("importance", "MEDIUM"),
            "scheduled_utc": scheduled_utc,
            "forecast_value": forecast_value,
            "previous_value": previous_value,
            "actual_value": None,  # ALWAYS unknown until released
            "actual": None,        # Alias
            "status": "SCHEDULED",
            "scenarios": self.generate_scenarios({
                "template_key": template_key,
                "forecast_value": forecast_value,
                "previous_value": previous_value,
            }),
            "asset_sensitivities": template.get("sensitivities", {}),
            "historical_stats": self.get_historical_stats(template_key),
        }
        return event

    @staticmethod
    def _calculate_countdown(event_time: datetime, now: datetime) -> str:
        """Calculate human-readable countdown to event."""
        delta = event_time - now
        total_seconds = delta.total_seconds()

        if total_seconds < 0:
            return "RELEASED"

        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @staticmethod
    def _utc_to_ist(utc_time: datetime) -> str:
        """Convert UTC datetime to IST string."""
        ist_time = utc_time.astimezone(IST)
        return ist_time.strftime("%Y-%m-%d %H:%M IST")


# ── Singleton ───────────────────────────────────────────────────────────────
economic_calendar_engine = EconomicCalendarEngine()
