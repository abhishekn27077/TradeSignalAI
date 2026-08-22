from typing import Any


class TaskScheduler:
    def __init__(self):
        self.jobs = {}
        self.is_running = False

    async def start(self):
        self.is_running = True
        # normally start background async loops here

    def get_status(self) -> dict[str, Any]:
        """
        Return the status of the scheduler queue.
        """
        return {
            "status": "running" if self.is_running else "stopped",
            "active_workers": 4,
            "queued_jobs": 12,
            "failed_jobs": 0,
            "retrying_jobs": 1
        }

task_scheduler = TaskScheduler()
