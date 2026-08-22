from app.utils.event_bus import event_bus


class NotificationCenter:
    async def send_alert(self, level: str, title: str, message: str) -> None:
        """
        Send system alert via EventBus.
        """
        payload = {
            "level": level,
            "title": title,
            "message": message
        }
        await event_bus.publish("SystemAlert", payload)

notification_center = NotificationCenter()
