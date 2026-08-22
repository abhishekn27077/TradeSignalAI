import json
from datetime import datetime
from typing import Any


class QualificationReporter:
    def __init__(self, manager):
        self.manager = manager

    def generate_report(self) -> dict[str, Any]:
        metrics = self.manager.metrics
        
        # Calculate Scores
        trades = metrics.get("trades_completed", 0)
        signals = metrics.get("signals_generated", 0)
        
        # Integration Score: Did signals convert to trades, did trades log to journal/memory?
        integration_score = 0
        if signals > 0:
            trade_ratio = min(100, (trades / signals) * 100)
            journal_ratio = min(100, (metrics.get("journal_entries", 0) / max(1, trades)) * 100)
            memory_ratio = min(100, (metrics.get("memory_records", 0) / max(1, trades)) * 100)
            integration_score = (trade_ratio + journal_ratio + memory_ratio) / 3
            
        # Reliability Score: Were there many rejected orders?
        orders_filled = metrics.get("orders_filled", 0)
        orders_total = orders_filled + metrics.get("orders_rejected", 0)
        reliability_score = (orders_filled / orders_total * 100) if orders_total > 0 else 100
        
        # Performance Score: Latencies
        ws_lat = metrics.get("ws_latency_ms", 0)
        api_lat = metrics.get("api_latency_ms", 0)
        perf_score = max(0, 100 - (ws_lat / 10) - (api_lat / 10))
        
        # Overall
        overall_score = (integration_score + reliability_score + perf_score) / 3
        
        passed = overall_score >= 80 and trades > 0
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.manager.active_mode,
            "overall_score": round(overall_score, 2),
            "integration_score": round(integration_score, 2),
            "reliability_score": round(reliability_score, 2),
            "performance_score": round(perf_score, 2),
            "status": "PASS" if passed else "FAIL",
            "metrics": metrics,
            "warnings": [],
            "failed_components": []
        }
        
        if metrics.get("orders_rejected", 0) > 0:
            report["warnings"].append(f"{metrics['orders_rejected']} orders were rejected.")
            
        if metrics.get("cpu_percent", 0) > 80:
            report["warnings"].append("High CPU usage detected.")
            
        if not passed:
            report["failed_components"].append("Integration Pipeline")
            
        # Save to file
        report_path = f"qualification_report_{int(datetime.utcnow().timestamp())}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4)
            
        return report

