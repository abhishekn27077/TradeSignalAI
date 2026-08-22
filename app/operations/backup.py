from typing import Any


class BackupManager:
    def trigger_backup(self) -> dict[str, Any]:
        """
        Simulate a database and config backup.
        """
        return {
            "status": "success",
            "message": "Database and Configuration backup completed successfully.",
            "backup_id": "bkp_20260729_1745",
            "size_mb": 450
        }

    def get_history(self) -> list:
        return [
            {"id": "bkp_20260728_0000", "status": "success", "size_mb": 448},
            {"id": "bkp_20260729_0000", "status": "success", "size_mb": 450},
        ]

backup_manager = BackupManager()
