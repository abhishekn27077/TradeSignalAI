from datetime import datetime
from typing import Any


class AuditTrail:
    def __init__(self):
        self.logs: list[dict[str, Any]] = []

    def log_action(self, action_type: str, user: str, details: str) -> None:
        """
        Record a structured audit trail action.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action_type,
            "user": user,
            "details": details
        }
        self.logs.append(entry)
        # Stub: normally write to db

    def get_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.logs[-limit:]

audit_trail = AuditTrail()
# Pre-seed some logs for the UI
audit_trail.log_action("Forecast Created", "System", "Kronos generated H4 BTCUSD forecast")
audit_trail.log_action("Decision Approved", "Admin", "Approved trade #4829")
audit_trail.log_action("Configuration Changed", "Admin", "Updated risk limit to 2%")
