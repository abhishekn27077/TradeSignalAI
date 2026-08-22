import asyncio
from app.strategies.manager import strategy_manager
from app.strategies.plugins.registry import strategy_registry
import os
import json
from datetime import datetime

ARTIFACT_DIR = r"C:\Users\Abhis\.gemini\antigravity-ide\brain\d1f3a00e-4c5b-494d-8d0b-14018e87107f"
REPORT_FILE = os.path.join(ARTIFACT_DIR, "strategy_engine_certification.md")

async def test_strategies():
    print("Testing Strategy Engine...")
    report = ["# Strategy Engine Certification\n"]
    
    # 1. Initialize Strategies
    try:
        strategy_manager.initialize_strategies()
        report.append("## 1. Initialization and Plugin Loading\n✅ PASS: Strategy Manager initialized successfully.\n")
    except Exception as e:
        report.append(f"## 1. Initialization and Plugin Loading\n❌ FAIL: Strategy Manager failed to initialize. Error: {e}\n")
        
    strategies = strategy_manager._strategies
    report.append(f"Loaded {len(strategies)} strategies:\n")
    for s_name, instance in strategies.items():
        report.append(f"- **{s_name}**: (Status: {instance.status}, Priority: {instance.priority}, Weight: {instance.weight})\n")
    report.append("\n")

    # 2. Configuration & Parameter Validation
    report.append("## 2. Parameter Validation\n")
    validation_failures = 0
    for s_name, instance in strategies.items():
        try:
            cfg = instance.metadata
            assert cfg.name == s_name, f"Name mismatch: {cfg.name} != {s_name}"
            assert cfg.status is not None, "Missing status"
            assert isinstance(cfg.priority, int), "Priority is not integer"
            assert isinstance(cfg.weight, float) or isinstance(cfg.weight, int), "Weight is not numeric"
        except AssertionError as ae:
            validation_failures += 1
            report.append(f"- ❌ {s_name}: {ae}\n")
        except Exception as e:
            validation_failures += 1
            report.append(f"- ❌ {s_name}: Exception during validation: {e}\n")
            
    if validation_failures == 0:
        report.append("✅ PASS: All loaded strategies passed parameter validation.\n\n")

    # 3. Calculation Loops & Exception Handling
    report.append("## 3. Data Dependencies & Calculation Loops\n")
    from app.market_data.providers.manager import market_provider_manager
    rates = await market_provider_manager.get_rates("BTC-USD", "1m", count=100)
    
    if not rates:
        report.append("❌ FAIL: Could not fetch rates for testing calculation loops.\n")
    else:
        calc_errors = 0
        import pandas as pd
        df = pd.DataFrame([r.dict() if hasattr(r, 'dict') else r for r in rates])
        for s_name, instance in strategies.items():
            if not instance.instance:
                continue
            try:
                signal = instance.instance.analyze("BTC-USD", df)
                if signal:
                    report.append(f"- ✅ {s_name}: analyze() returned signal ({signal.direction.name}).\n")
                else:
                    report.append(f"- ✅ {s_name}: analyze() returned None (expected if no signal conditions met).\n")
            except Exception as e:
                calc_errors += 1
                report.append(f"- ❌ {s_name}: Exception during analyze(): {e}\n")
                
        if calc_errors == 0:
            report.append("\n✅ PASS: All strategy calculation loops handled execution successfully without unhandled exceptions.\n\n")

    # Write Report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"Strategy Engine Certification complete. Wrote to {REPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(test_strategies())
