import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """
    A lightweight background task scheduler for cron-like jobs or simple intervals.
    Can be replaced with APScheduler or Celery in the future.
    """
    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False

    def add_interval_job(self, func: Callable[..., Awaitable[None]], seconds: int):
        """Add a job to run every X seconds."""
        async def _wrapper():
            while self._running:
                try:
                    await func()
                except Exception as e:
                    logger.error(f"Error in background job {func.__name__}: {e}", exc_info=True)
                await asyncio.sleep(seconds)
                
        if self._running:
            task = asyncio.create_task(_wrapper())
            self._tasks.append(task)
        else:
            # Note: Need to store and start when start() is called, 
            # but for this placeholder we'll just log
            logger.info(f"Job {func.__name__} added. Call start() to begin.")

    def start(self):
        """Start the scheduler."""
        self._running = True
        logger.info("BackgroundScheduler started.")

    def stop(self):
        """Stop the scheduler and cancel all running tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("BackgroundScheduler stopped.")

# Global singleton scheduler
scheduler = BackgroundScheduler()
