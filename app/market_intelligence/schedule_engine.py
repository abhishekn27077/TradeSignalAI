import asyncio
from datetime import datetime, timedelta, timezone

from app.logs.logger import get_logger

logger = get_logger(__name__)

class ScheduleEngine:
    """
    Manages the Trade Schedule Center and H4 Session Planner.
    Calculates next H4 candle times and broadcasts countdowns.
    """
    
    def __init__(self):
        self._task = None
        self._running = False
        self._h4_hours = [0, 4, 8, 12, 16, 20] # IST hours

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Schedule Engine started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Schedule Engine stopped")

    def _get_ist_time(self):
        # Python 3.9+ ZoneInfo is better, using UTC + 5:30 for simplicity here if zoneinfo is not imported
        # but standard datetime is fine if we just want offset.
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(ist_offset)
        
    def _get_next_h4_time(self, current_time):
        """Finds the next H4 boundary (0,4,8,12,16,20) for the given IST time"""
        next_hour = None
        for h in self._h4_hours:
            if current_time.hour < h:
                next_hour = h
                break
                
        if next_hour is None:
            # Next day 00:00
            target = current_time + timedelta(days=1)
            target = target.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target = current_time.replace(hour=next_hour, minute=0, second=0, microsecond=0)
            
        return target

    def get_schedule_status(self):
        now_ist = self._get_ist_time()
        next_h4 = self._get_next_h4_time(now_ist)
        diff = next_h4 - now_ist
        seconds_left = int(diff.total_seconds())
        
        return {
            "current_time_ist": now_ist.isoformat(),
            "next_h4_time_ist": next_h4.isoformat(),
            "countdown_seconds": seconds_left
        }

    async def _run_loop(self):
        import json

        from app.utils.websocket_manager import ws_manager
        
        while self._running:
            try:
                status = self.get_schedule_status()
                message = json.dumps({"event": "schedule_tick", "data": status})
                await ws_manager.broadcast(message, topic="schedule")
            except Exception as e:
                logger.error(f"Error in Schedule Engine loop: {e}")
            
            await asyncio.sleep(1) # tick every second for UI countdown

schedule_engine = ScheduleEngine()
