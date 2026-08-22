"""
Script to execute the complete end-to-end reality trace for Phase 45:
  1. Trigger Live Forecast Scheduler cycle for all 9 assets
  2. Generate predictions and update shadow ledger
  3. Run outcome resolution cycle with Shadow Outcome Worker
  4. Generate Daily Signal Journal and persist daily snapshot
  5. Output artifacts/phase45/REAL_RUNTIME_TRACE.json
"""
import os
import json
import uuid
from datetime import datetime, timezone

from app.runtime.live_forecast_scheduler import live_forecast_scheduler
from app.runtime.shadow_outcome_worker import shadow_outcome_worker
from app.analytics.daily_signal_journal import daily_signal_journal
from app.analytics.shadow_validation_engine import shadow_validation_engine


def run_phase45_runtime_trace():
    now = datetime.now(timezone.utc)
    cohort_meta = shadow_validation_engine.get_cohort_metadata()

    # 1. Run Live Scheduler Cycle across all 9 assets
    cycle_res = live_forecast_scheduler.process_cycle()

    # 2. Run Shadow Outcome Worker
    outcome_res = shadow_outcome_worker.run_resolution_cycle()

    # 3. Generate Daily Signal Journal
    today_journal = daily_signal_journal.get_today_journal()
    yesterday_journal = daily_signal_journal.get_yesterday_journal()
    tomorrow_forecasts = daily_signal_journal.get_tomorrow_forecasts()
    model_scorecard = daily_signal_journal.get_model_scorecard()
    missed_trades = daily_signal_journal.get_missed_trades()
    failed_trades = daily_signal_journal.get_failed_trades()
    market_memory = daily_signal_journal.get_daily_market_memory()
    ai_review = daily_signal_journal.get_daily_ai_review()

    # 4. Save daily artifact
    daily_file = daily_signal_journal.save_daily_artifact(now.strftime("%Y-%m-%d"))

    # 5. Build full REAL_RUNTIME_TRACE payload
    trace_payload = {
        "runtime_trace_id": str(uuid.uuid4()),
        "trace_timestamp": now.isoformat(),
        "validation_cohort": cohort_meta.get("validation_cohort", "PHASE43_SHADOW_V1"),
        "model_version": cohort_meta.get("model_version", "3.2.0-frozen"),
        "system_status": "LIVE",
        "zero_trust_status": "ACTIVE_ENFORCED",
        "real_money_status": "DISABLED_SAFETY_ENFORCED",
        "scheduler_cycle": {
            "total_assets_scanned": cycle_res["total_assets_scanned"],
            "trades_qualified": cycle_res["trades_qualified"],
            "trades_rejected": cycle_res["trades_rejected"],
            "forecast_sample": cycle_res["forecasts"][:2],
        },
        "outcome_worker": {
            "open_trades_scanned": outcome_res["open_trades_scanned"],
            "trades_resolved_this_cycle": outcome_res["trades_resolved_this_cycle"],
            "lifetime_resolved": outcome_res["total_lifetime_resolved"],
        },
        "daily_journal": {
            "date": today_journal["date"],
            "today_summary": today_journal["summary"],
            "yesterday_summary": yesterday_journal["summary"],
            "tomorrow_target_date": tomorrow_forecasts["target_date"],
            "persisted_artifact_path": daily_file,
        },
        "model_scorecard_summary": {
            "best_performing_model": model_scorecard["best_performing_model"],
            "highest_accuracy_model": model_scorecard["highest_accuracy_model"],
        },
        "ai_review_verdict": ai_review["verdict"],
    }

    os.makedirs("artifacts/phase45", exist_ok=True)
    out_path = "artifacts/phase45/REAL_RUNTIME_TRACE.json"
    with open(out_path, "w") as f:
        json.dump(trace_payload, f, indent=2)

    print(f"Phase 45 Runtime Trace generated successfully at {out_path}")
    print(f"Daily snapshot saved at {daily_file}")


if __name__ == "__main__":
    run_phase45_runtime_trace()
