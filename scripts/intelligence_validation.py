import asyncio
import sys
import os

# Set up path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def validate_intelligence():
    print("================================================")
    print("STARTING FINAL INTELLIGENCE VALIDATION")
    print("================================================\n")

    # ---------------------------------------------------------
    # SECTION 1: BACKGROUND TASKS
    # ---------------------------------------------------------
    print("SECTION 1 — BACKEND AUDIT")
    try:
        from app.orchestration.scheduler import task_scheduler
        status = task_scheduler.get_status()
        print(f"Scheduler Status: {status}")
        
        # Look for the internal queue
        print("Active Background Processes:")
        if hasattr(task_scheduler, 'tasks'):
            for task_id, t in task_scheduler.tasks.items():
                print(f"- {task_id}: {t.get('status', 'Unknown')}")
        else:
            print("WARNING: Task Scheduler has no internal 'tasks' dictionary.")
    except Exception as e:
        print(f"FAIL: Could not query Background Scheduler: {e}")
    print("-------------------------------------------------\n")

    # ---------------------------------------------------------
    # SECTION 2 & 5 & 6 & 7: FORECAST ENGINE & KRONOS & LEARNING
    # ---------------------------------------------------------
    print("SECTION 2, 6, 7 — FORECAST ENGINE, KRONOS, LEARNING AUDIT")
    try:
        from app.analytics.models.kronos.adapter import KronosAdapter
        import pandas as pd
        import numpy as np
        
        print("Instantiating Kronos Model...")
        kronos = KronosAdapter()
        
        print("\nChecking Kronos Logic (Mock vs Genuine):")
        # Generate dummy market data to see if prediction relies on actual weights
        dummy_df = pd.DataFrame({
            "timestamp": pd.date_range("2026-08-01", periods=10, freq="1min"),
            "open": np.random.rand(10) * 1000,
            "high": np.random.rand(10) * 1000,
            "low": np.random.rand(10) * 1000,
            "close": np.random.rand(10) * 1000,
            "volume": np.random.rand(10) * 100,
        }).set_index("timestamp")
        
        print(f"Input DF Shape: {dummy_df.shape}")
        pred = kronos.predict(dummy_df, pred_len=5)
        print(f"Prediction Result Shape: {pred.shape}")
        
        # Check historical learning engine
        from app.learning.learning_engine import LearningEngine
        le = LearningEngine(db_session=None)
        
        print("\nChecking Historical Learning Engine:")
        if not hasattr(le, "db") or not hasattr(le, "evaluate_predictions"):
            print("FAIL: Historical Learning Engine is missing core methods.")
        else:
            import inspect
            source = inspect.getsource(le.evaluate_predictions)
            if "pass" in source or len(source.strip().split("\n")) < 15:
                print("FAIL: LearningEngine.evaluate_predictions() is an empty stub!")
                print(source)
                
    except Exception as e:
        print(f"FAIL: Error testing analytical components: {e}")
    print("-------------------------------------------------\n")

    # ---------------------------------------------------------
    # SECTION 12: PAPER TRADING SIMULATION
    # ---------------------------------------------------------
    print("SECTION 12 — PAPER TRADING AUDIT")
    print("Checking for Paper Trading Simulation capabilities...")
    try:
        from app.execution.paper.order_manager import paper_order_manager
        print("Paper order manager found. Checking track record capabilities...")
        if not hasattr(paper_order_manager, "calculate_sharpe") and not hasattr(paper_order_manager, "get_performance_metrics"):
            print("FAIL: Paper trading lacks Sharpe/Drawdown/Expectancy tracking.")
    except Exception as e:
        print(f"FAIL: Paper trading check error: {e}")
    print("-------------------------------------------------\n")
    print("INTELLIGENCE VALIDATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(validate_intelligence())
