"""
app/core/signal_validator.py
============================
Phase 10: Canonical 11-Point Signal Validity Contract.

Enforces Fail-Closed Zero-Trust Signal Validation before ANY signal can be generated or journaled:
1. Asset exists in Asset Registry
2. Primary provider available
3. Primary data fresh
4. Timestamp valid (not from the future, not expired)
5. Timeframe correct and supported
6. Venue correct for asset class
7. Market session OPEN
8. Strategy conditions satisfied
9. Risk rules satisfied (RR >= 1.5, valid SL, valid TP)
10. No duplicate signal identity
11. Paper execution ONLY (Real money strictly locked out)

If ANY condition fails, the signal MUST BE REJECTED (NO SIGNAL).
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

from app.config.settings import get_settings
from app.core.asset_registry import canonical_asset_registry, CanonicalAsset
from app.core.market_session import MarketSessionService
from app.market_data.freshness_service import DataFreshnessService, FreshnessStatus

logger = logging.getLogger("signal_validator")


class SignalRejectionReason(str, Enum):
    UNREGISTERED_ASSET = "UNREGISTERED_ASSET"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    DATA_STALE = "DATA_STALE"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    TIMEFRAME_MISMATCH = "TIMEFRAME_MISMATCH"
    VENUE_MISMATCH = "VENUE_MISMATCH"
    MARKET_CLOSED = "MARKET_CLOSED"
    STRATEGY_CONDITIONS_UNMET = "STRATEGY_CONDITIONS_UNMET"
    RISK_REJECTED = "RISK_REJECTED"
    INVALID_PRICE = "INVALID_PRICE"
    INVALID_STOP_LOSS = "INVALID_STOP_LOSS"
    INVALID_TAKE_PROFIT = "INVALID_TAKE_PROFIT"
    DUPLICATE_SIGNAL = "DUPLICATE_SIGNAL"
    REAL_MONEY_FORBIDDEN = "REAL_MONEY_FORBIDDEN"


@dataclass(frozen=True)
class SignalValidationResult:
    is_valid: bool
    rejection_reason: Optional[SignalRejectionReason]
    rejection_detail: Optional[str]
    checks: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "rejection_reason": self.rejection_reason.value if self.rejection_reason else None,
            "rejection_detail": self.rejection_detail,
            "checks": self.checks,
        }


class CanonicalSignalValidator:
    """
    Enforces the 11-point signal validity contract.
    """

    @classmethod
    def validate_pre_flight(
        cls,
        asset_symbol: str,
        timeframe: str,
        current_price: Optional[float],
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        direction: Optional[str] = "BUY",
        source_timestamp: Optional[datetime] = None,
        provider_name: Optional[str] = None,
        venue: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> SignalValidationResult:
        """
        Validates whether a candidate trade setup is eligible to become an actionable signal.
        """
        now = reference_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        settings = get_settings()
        checks: Dict[str, Dict[str, Any]] = {}

        # Check 11: Paper Execution Lockout (Phase 18)
        real_money_attempt = getattr(settings, "REAL_MONEY_ENABLED", False) or getattr(settings, "BROKER_EXECUTION_ENABLED", False)
        checks["paper_execution_only"] = {
            "required": "PAPER_ONLY",
            "passed": not real_money_attempt,
        }
        if real_money_attempt:
            return SignalValidationResult(
                is_valid=False,
                rejection_reason=SignalRejectionReason.REAL_MONEY_FORBIDDEN,
                rejection_detail="Real-money execution is strictly locked out. System operates in paper-only mode.",
                checks=checks,
            )

        # Check 1: Asset exists in Asset Registry
        resolved = canonical_asset_registry.resolve(asset_symbol)
        checks["asset_registry"] = {
            "required": "REGISTERED",
            "actual": asset_symbol,
            "passed": resolved is not None,
        }
        if not resolved:
            return SignalValidationResult(
                is_valid=False,
                rejection_reason=SignalRejectionReason.UNREGISTERED_ASSET,
                rejection_detail=f"Asset '{asset_symbol}' is not present in Canonical Asset Registry.",
                checks=checks,
            )

        asset, _ = resolved

        # Check 5: Timeframe correct and supported
        is_tf_supported = canonical_asset_registry.validate_timeframe(asset.canonical_symbol, timeframe)
        checks["timeframe_supported"] = {
            "required": list(asset.supported_timeframes),
            "actual": timeframe,
            "passed": is_tf_supported,
        }
        if not is_tf_supported:
            return SignalValidationResult(
                is_valid=False,
                rejection_reason=SignalRejectionReason.TIMEFRAME_MISMATCH,
                rejection_detail=f"Timeframe '{timeframe}' is not supported for {asset.canonical_symbol}.",
                checks=checks,
            )

        # Check 6: Venue correct
        expected_venue = asset.venue
        venue_passed = (venue is None) or (venue.upper() == expected_venue.upper())
        checks["venue_check"] = {
            "required": expected_venue,
            "actual": venue or expected_venue,
            "passed": venue_passed,
        }
        if not venue_passed:
            return SignalValidationResult(
                is_valid=False,
                rejection_reason=SignalRejectionReason.VENUE_MISMATCH,
                rejection_detail=f"Venue '{venue}' does not match canonical venue '{expected_venue}' for {asset.canonical_symbol}.",
                checks=checks,
            )

        # Check 7: Market session OPEN (CRITICAL RULE 3 & Phase 9)
        session_status = MarketSessionService.get_market_status(asset.canonical_symbol, now)
        is_open = session_status.get("is_market_open", False)
        checks["market_session"] = {
            "required": "OPEN",
            "actual": "OPEN" if is_open else "CLOSED",
            "current_session": session_status.get("current_session", "CLOSED"),
            "passed": is_open,
        }
        if not is_open:
            logger.info(
                f"[SESSION] symbol={asset.canonical_symbol} state=CLOSED decision=BLOCK reason={session_status.get('reason')}"
            )
            return SignalValidationResult(
                is_valid=False,
                rejection_reason=SignalRejectionReason.MARKET_CLOSED,
                rejection_detail=f"Market for {asset.canonical_symbol} is CLOSED ({session_status.get('reason')}). No signals permitted.",
                checks=checks,
            )

        # Check 2 & 4: Primary provider price available and valid
        if current_price is None or current_price <= 0.0:
            checks["price_validity"] = {"required": ">0", "actual": current_price, "passed": False}
            return SignalValidationResult(
                is_valid=False,
                rejection_reason=SignalRejectionReason.INVALID_PRICE,
                rejection_detail=f"Market price for {asset.canonical_symbol} is missing or non-positive.",
                checks=checks,
            )
        checks["price_validity"] = {"required": ">0", "actual": current_price, "passed": True}

        # Check 3: Data Freshness Check (Phase 8)
        if source_timestamp is not None:
            freshness = DataFreshnessService.evaluate_tick_freshness(
                source_timestamp=source_timestamp,
                received_timestamp=now,
                asset_class=asset.asset_class.value,
                reference_time=now,
            )
            checks["data_freshness"] = {
                "required": "FRESH",
                "actual": freshness.status.value,
                "data_age_ms": freshness.data_age_ms,
                "passed": freshness.is_actionable,
            }
            if not freshness.is_actionable:
                logger.info(
                    f"[SIGNAL] symbol={asset.canonical_symbol} decision=REJECTED reason=DATA_STALE age_ms={round(freshness.data_age_ms)}"
                )
                return SignalValidationResult(
                    is_valid=False,
                    rejection_reason=SignalRejectionReason.DATA_STALE,
                    rejection_detail=f"Data is {freshness.status.value} (age {round(freshness.data_age_ms)}ms > limit).",
                    checks=checks,
                )

        # Check 9: Risk rules (SL, TP, Risk-Reward)
        if direction in ("BUY", "SELL") and stop_loss is not None and take_profit is not None:
            if direction == "BUY":
                if stop_loss >= current_price:
                    checks["sl_validity"] = {"required": "SL < entry", "actual": f"SL={stop_loss}, Entry={current_price}", "passed": False}
                    return SignalValidationResult(
                        is_valid=False,
                        rejection_reason=SignalRejectionReason.INVALID_STOP_LOSS,
                        rejection_detail=f"BUY stop loss ({stop_loss}) must be below entry price ({current_price}).",
                        checks=checks,
                    )
                if take_profit <= current_price:
                    checks["tp_validity"] = {"required": "TP > entry", "actual": f"TP={take_profit}, Entry={current_price}", "passed": False}
                    return SignalValidationResult(
                        is_valid=False,
                        rejection_reason=SignalRejectionReason.INVALID_TAKE_PROFIT,
                        rejection_detail=f"BUY take profit ({take_profit}) must be above entry price ({current_price}).",
                        checks=checks,
                    )
                risk = current_price - stop_loss
                reward = take_profit - current_price
            else:  # SELL
                if stop_loss <= current_price:
                    checks["sl_validity"] = {"required": "SL > entry", "actual": f"SL={stop_loss}, Entry={current_price}", "passed": False}
                    return SignalValidationResult(
                        is_valid=False,
                        rejection_reason=SignalRejectionReason.INVALID_STOP_LOSS,
                        rejection_detail=f"SELL stop loss ({stop_loss}) must be above entry price ({current_price}).",
                        checks=checks,
                    )
                if take_profit >= current_price:
                    checks["tp_validity"] = {"required": "TP < entry", "actual": f"TP={take_profit}, Entry={current_price}", "passed": False}
                    return SignalValidationResult(
                        is_valid=False,
                        rejection_reason=SignalRejectionReason.INVALID_TAKE_PROFIT,
                        rejection_detail=f"SELL take profit ({take_profit}) must be below entry price ({current_price}).",
                        checks=checks,
                    )
                risk = stop_loss - current_price
                reward = current_price - take_profit

            rr = reward / risk if risk > 0 else 0.0
            checks["risk_reward"] = {"required": ">= 1.5", "actual": round(rr, 2), "passed": rr >= 1.5}
            if rr < 1.5:
                return SignalValidationResult(
                    is_valid=False,
                    rejection_reason=SignalRejectionReason.RISK_REJECTED,
                    rejection_detail=f"Risk/reward ratio ({round(rr, 2)}) is below the required 1.5 minimum.",
                    checks=checks,
                )

        # All gates passed!
        return SignalValidationResult(
            is_valid=True,
            rejection_reason=None,
            rejection_detail=None,
            checks=checks,
        )


signal_validator = CanonicalSignalValidator()
canonical_signal_validator = CanonicalSignalValidator()
