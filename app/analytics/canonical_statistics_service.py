"""
app/analytics/canonical_statistics_service.py
=============================================
Authoritative Single Source of Truth (SSOT) Statistics Service for TradeSignalAI-v3 (Phase 70).

Reconciles all performance, win rate, expectancy, Wilson 95% confidence intervals,
and profit factor statistics across Dashboard, Terminal, History, and Performance screens
directly from SQLite database records without hardcoded numbers or discrepancies.
"""

from __future__ import annotations
import math
import sqlite3
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from app.core.canonical_prospective_ledger import (
    canonical_prospective_ledger,
    CanonicalProspectiveLedger,
    CORE_ASSETS,
    SUPPORTED_TIMEFRAMES,
)

logger = logging.getLogger("canonical_statistics_service")


class CanonicalStatisticsService:
    """
    Unified, authoritative mathematical statistics engine for TradeSignalAI.
    """

    def __init__(self, db_path: str = "tradesignal.db", ledger: Optional[CanonicalProspectiveLedger] = None):
        self.db_path = db_path
        if ledger is not None:
            self.ledger = ledger
        elif db_path == "tradesignal.db":
            self.ledger = canonical_prospective_ledger
        else:
            self.ledger = CanonicalProspectiveLedger(db_path=db_path)

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        for candidate in [self.db_path, "trading_fallback.db", "app/database/trading_fallback.db"]:
            if os.path.exists(candidate):
                try:
                    conn = sqlite3.connect(candidate, timeout=30.0, check_same_thread=False)
                    conn.execute("PRAGMA busy_timeout=30000;")
                    return conn
                except Exception:
                    pass
        return None

    def calculate_wilson_ci(self, wins: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculates the Wilson score confidence interval for a binomial proportion.
        """
        if total == 0:
            return 0.0, 0.0

        z = 1.95996 if confidence == 0.95 else 1.64485
        p_hat = wins / total
        denominator = 1 + (z ** 2) / total
        center_adjusted = (p_hat + (z ** 2) / (2 * total)) / denominator
        spread = (z * math.sqrt((p_hat * (1 - p_hat) + (z ** 2) / (4 * total)) / total)) / denominator

        lower = max(0.0, center_adjusted - spread)
        upper = min(1.0, center_adjusted + spread)
        return round(lower * 100, 1), round(upper * 100, 1)

    def get_canonical_performance_summary(
        self,
        date_filter: str = "ALL",
        asset: Optional[str] = None,
        timeframe: Optional[str] = None,
        record_type: Optional[str] = None,
        include_demo: bool = False,
        reference_dt: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculates authoritative single-source-of-truth metrics directly from
        resolved canonical records in canonical_prospective_signal_ledger.
        Excludes demo, test, replay, cancelled, and unresolved records by default (Section 12).
        """
        signals = self.ledger.get_signals_by_filter(
            date_filter=date_filter,
            asset=asset,
            timeframe=timeframe,
            record_type=record_type,
            limit=5000,
            reference_dt=reference_dt,
        )

        # Section 12: Exclude demo, test, replay, cancelled, unresolved unless explicitly included
        if not include_demo:
            signals = [s for s in signals if not s.is_demo and s.record_type not in ("DEMO", "TEST")]

        total_signals = len(signals)
        qualified_signals = [s for s in signals if s.qualification_status == "QUALIFIED"]
        no_trade_signals = [s for s in signals if s.qualification_status != "QUALIFIED"]

        # Only resolved with valid evidence and real outcomes (exclude UNRESOLVED)
        resolved_signals = [
            s for s in signals
            if s.outcome is not None and s.outcome != "UNRESOLVED" and s.signal_status != "CANCELLED"
        ]

        wins = sum(1 for s in resolved_signals if s.outcome == "WON")
        losses = sum(1 for s in resolved_signals if s.outcome == "LOST")
        time_exits = sum(1 for s in resolved_signals if s.outcome == "TIME_EXIT")
        ambiguous = sum(1 for s in resolved_signals if s.outcome == "AMBIGUOUS")
        resolved_count = len(resolved_signals)

        win_rate_pct = round((wins / resolved_count * 100.0), 1) if resolved_count > 0 else 0.0
        ci_lower, ci_upper = self.calculate_wilson_ci(wins, resolved_count)

        r_values = [s.net_r for s in resolved_signals if s.net_r is not None]
        gross_r_values = [s.gross_r for s in resolved_signals if s.gross_r is not None]

        total_net_r = round(sum(r_values), 2)
        total_gross_r = round(sum(gross_r_values), 2)
        expectancy_r = round(total_net_r / resolved_count, 3) if resolved_count > 0 else 0.0
        avg_r = round(total_net_r / resolved_count, 2) if resolved_count > 0 else 0.0

        pos_r = sum(r for r in r_values if r > 0)
        neg_r = abs(sum(r for r in r_values if r < 0))
        profit_factor = round(pos_r / neg_r, 2) if neg_r > 0 else (round(pos_r, 2) if pos_r > 0 else 0.0)

        # Sharpe ratio (truthful: 0.0 when insufficient trades)
        if len(r_values) > 1:
            mean_r = sum(r_values) / len(r_values)
            variance = sum((r - mean_r) ** 2 for r in r_values) / (len(r_values) - 1)
            std_r = math.sqrt(variance) if variance > 0 else 0.01
            sharpe = round((mean_r / std_r) * math.sqrt(min(252, resolved_count)), 2)
        else:
            sharpe = 0.0

        # Chronological sorting for equity curve, drawdown, streaks, and holding times
        sorted_resolved = sorted(resolved_signals, key=lambda s: s.resolved_at or s.created_at)

        # Section 13: Drawdown Validation (Peak-to-Trough equity decline)
        running_peak_r = 0.0
        max_dd_r = 0.0
        cum_r = 0.0
        equity_curve = []
        initial_capital = 100000.0
        current_capital = initial_capital
        peak_capital = initial_capital
        max_capital_dd_pct = 0.0

        # Streaks
        current_win_streak = 0
        current_loss_streak = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        # Holding duration
        holding_seconds_list = []

        for idx, s in enumerate(sorted_resolved, start=1):
            r = s.net_r if s.net_r is not None else 0.0
            cum_r += r
            trade_pnl = (initial_capital * 0.01) * r
            current_capital += trade_pnl

            # Streaks
            if r > 0:
                current_win_streak += 1
                current_loss_streak = 0
                if current_win_streak > max_consecutive_wins:
                    max_consecutive_wins = current_win_streak
            elif r < 0:
                current_loss_streak += 1
                current_win_streak = 0
                if current_loss_streak > max_consecutive_losses:
                    max_consecutive_losses = current_loss_streak

            # Holding time
            if s.actual_entry_time and s.actual_exit_time:
                try:
                    t_in = datetime.fromisoformat(s.actual_entry_time.replace("Z", "+00:00"))
                    t_out = datetime.fromisoformat(s.actual_exit_time.replace("Z", "+00:00"))
                    dur = abs((t_out - t_in).total_seconds())
                    holding_seconds_list.append(dur)
                except Exception:
                    pass

            # R-based drawdown
            if cum_r > running_peak_r:
                running_peak_r = cum_r
            dd_r = running_peak_r - cum_r
            if dd_r > max_dd_r:
                max_dd_r = dd_r

            # Capital % drawdown
            if current_capital > peak_capital:
                peak_capital = current_capital
            dd_capital_pct = ((peak_capital - current_capital) / peak_capital) * 100.0 if peak_capital > 0 else 0.0
            if dd_capital_pct > max_capital_dd_pct:
                max_capital_dd_pct = dd_capital_pct

            equity_curve.append({
                "trade_number": idx,
                "signal_id": s.signal_id,
                "asset": s.asset,
                "timeframe": s.timeframe,
                "outcome": s.outcome,
                "realized_r": r,
                "cumulative_r": round(cum_r, 2),
                "virtual_equity": round(current_capital, 2),
                "timestamp": s.resolved_at or s.created_at,
            })

        avg_holding_sec = sum(holding_seconds_list) / len(holding_seconds_list) if holding_seconds_list else 14400.0
        avg_holding_hrs = round(avg_holding_sec / 3600.0, 1)

        # Phase 79: Explicit Sample Methodology Tiers (Part H)
        if resolved_count < 15:
            sample_status = "INSUFFICIENT SAMPLE"
            is_sample_supported = False
        elif resolved_count < 30:
            sample_status = "LIMITED SAMPLE"
            is_sample_supported = False
        else:
            sample_status = "SUPPORTED SAMPLE"
            is_sample_supported = True

        min_required_n = 15
        sample_methodology = {
            "status": sample_status,
            "sample_n": resolved_count,
            "min_required_n": min_required_n,
            "supported_threshold_n": 30,
            "confidence_interval_method": "Wilson Score 95% Confidence Interval",
            "eligibility_rules": "Only genuine LIVE, canonical, evidence-backed, resolved signals are eligible. Unresolved, demo, synthetic, and replay records are excluded.",
            "tier_definitions": {
                "INSUFFICIENT SAMPLE": "N < 15: Empirical sample too small for statistical inference.",
                "LIMITED SAMPLE": "15 <= N < 30: Preliminary sample; wide confidence interval.",
                "SUPPORTED SAMPLE": "N >= 30: Sufficient sample size for standard parametric analysis.",
            },
        }

        return {
            "success": True,
            "date_filter": date_filter,
            "sample_status": sample_status,
            "sample_n": resolved_count,
            "min_required_n": min_required_n,
            "is_sample_supported": is_sample_supported,
            "sample_methodology": sample_methodology,
            "sample_size_tooltip": "Sample size classification only. It does not indicate future profitability or predictive accuracy.",
            "total_signals": total_signals,
            "total_qualified": len(qualified_signals),
            "total_no_trade": len(no_trade_signals),
            "resolved_count": resolved_count,
            "wins": wins,
            "losses": losses,
            "time_exits": time_exits,
            "ambiguous": ambiguous,
            "win_rate_pct": win_rate_pct,
            "wilson_95_ci": [ci_lower, ci_upper],
            "wilson_ci_lower_pct": ci_lower,
            "wilson_ci_upper_pct": ci_upper,
            "total_net_r": total_net_r,
            "total_gross_r": total_gross_r,
            "expectancy_r": expectancy_r,
            "avg_r": avg_r,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "max_drawdown_r": round(max_dd_r, 2),
            "max_drawdown_pct": round(max_capital_dd_pct, 2),
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "avg_holding_hours": avg_holding_hrs,
            "initial_capital": initial_capital,
            "current_capital": round(current_capital, 2),
            "equity_curve": equity_curve,
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Authoritative summary for the main Dashboard and System Health.
        Reconciles signal counts, today's actionable windows, and overall performance.
        """
        all_stats = self.get_canonical_performance_summary(date_filter="ALL")
        today_windows = self.ledger.get_today_time_windows()
        today_signals = self.ledger.get_signals_by_filter(date_filter="TODAY", live_only=True)

        today_qualified = sum(w["qualified_count"] for w in today_windows)
        today_no_trade = sum(w["no_trade_count"] for w in today_windows)

        return {
            "success": True,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "signals": {
                "total_prospective": all_stats["total_signals"],
                "today_total": len(today_signals),
                "today_actionable_windows": len(today_windows),
                "today_qualified": today_qualified,
                "today_no_trade": today_no_trade,
            },
            "performance": {
                "resolved_trades": all_stats["resolved_count"],
                "wins": all_stats["wins"],
                "losses": all_stats["losses"],
                "win_rate_pct": all_stats["win_rate_pct"],
                "wilson_ci": all_stats["wilson_95_ci"],
                "total_net_r": all_stats["total_net_r"],
                "avg_r": all_stats["avg_r"],
                "profit_factor": all_stats["profit_factor"],
                "expectancy_r": all_stats["expectancy_r"],
                "max_drawdown_pct": all_stats["max_drawdown_pct"],
                "max_drawdown_r": all_stats["max_drawdown_r"],
                "max_consecutive_wins": all_stats["max_consecutive_wins"],
                "max_consecutive_losses": all_stats["max_consecutive_losses"],
                "sample_status": all_stats["sample_status"],
                "sample_n": all_stats["sample_n"],
                "min_required_n": all_stats["min_required_n"],
            },
            "paper_portfolio": {
                "initial_capital": all_stats["initial_capital"],
                "current_equity": all_stats["current_capital"],
                "total_realized_r": all_stats["total_net_r"],
                "execution_mode": "DEMO / PAPER",
                "real_money_enabled": False,
            },
        }

    def get_performance_by_asset(self, date_filter: str = "ALL", min_sample_req: int = 15) -> List[Dict[str, Any]]:
        """
        Returns performance breakdown per core asset with Phase 77 sample size labels.
        """
        result = []
        for asset in CORE_ASSETS:
            stats = self.get_canonical_performance_summary(date_filter=date_filter, asset=asset)
            n_resolved = stats["resolved_count"]
            if n_resolved < min_sample_req:
                sample_label = f"LIMITED SAMPLE (N = {n_resolved})"
                is_sufficient = False
            else:
                sample_label = f"SAMPLE-SUPPORTED (N = {n_resolved})"
                is_sufficient = True

            result.append({
                "asset": asset,
                "total_signals": stats["total_signals"],
                "resolved_signals": n_resolved,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "win_rate_pct": stats["win_rate_pct"] if n_resolved > 0 else 0.0,
                "total_net_r": stats["total_net_r"],
                "profit_factor": stats["profit_factor"],
                "expectancy_r": stats["expectancy_r"],
                "sample_size": n_resolved,
                "min_required_n": min_sample_req,
                "sample_status": sample_label,
                "is_sufficient": is_sufficient,
            })
        result.sort(key=lambda x: x["total_net_r"], reverse=True)
        return result

    def get_performance_by_timeframe(self, date_filter: str = "ALL", min_sample_req: int = 15) -> List[Dict[str, Any]]:
        """
        Returns performance breakdown per timeframe with Phase 77 sample size labels.
        """
        result = []
        for tf in SUPPORTED_TIMEFRAMES:
            stats = self.get_canonical_performance_summary(date_filter=date_filter, timeframe=tf)
            n_resolved = stats["resolved_count"]
            if n_resolved < min_sample_req:
                sample_label = f"LIMITED SAMPLE (N = {n_resolved})"
                is_sufficient = False
            else:
                sample_label = f"SAMPLE-SUPPORTED (N = {n_resolved})"
                is_sufficient = True

            result.append({
                "timeframe": tf,
                "total_signals": stats["total_signals"],
                "resolved_signals": n_resolved,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "win_rate_pct": stats["win_rate_pct"] if n_resolved > 0 else 0.0,
                "total_net_r": stats["total_net_r"],
                "profit_factor": stats["profit_factor"],
                "expectancy_r": stats["expectancy_r"],
                "sample_size": n_resolved,
                "min_required_n": min_sample_req,
                "sample_status": sample_label,
                "is_sufficient": is_sufficient,
            })
        result.sort(key=lambda x: x["total_net_r"], reverse=True)
        return result


# Global Singleton Instance
canonical_statistics_service = CanonicalStatisticsService()

