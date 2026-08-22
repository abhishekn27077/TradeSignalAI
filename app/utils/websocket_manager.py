import json

from fastapi import WebSocket

from app.logs.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            logger.info(f"Client {client_id} connected via WebSocket")
            await self.send_personal_message(
                json.dumps({"event": "connected", "client_id": client_id}), client_id
            )
        except Exception as e:
            logger.warning(f"WebSocket connect failed for {client_id}: {e}")

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        for topic, clients in self.subscriptions.items():
            clients.discard(client_id)
        logger.info(f"Client {client_id} disconnected")

    async def subscribe(self, client_id: str, topic: str):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(client_id)

    async def unsubscribe(self, client_id: str, topic: str):
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(client_id)

    async def broadcast(self, message: str, topic: str | None = None):
        if topic:
            targets = self.subscriptions.get(topic, set())
            disconnected = []
            for client_id in targets:
                ws = self.active_connections.get(client_id)
                if ws:
                    try:
                        await ws.send_text(message)
                    except Exception:
                        disconnected.append(client_id)
                else:
                    disconnected.append(client_id)
            for cid in disconnected:
                self.disconnect(cid)
        else:
            disconnected = []
            for client_id, ws in list(self.active_connections.items()):
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(client_id)
            for cid in disconnected:
                self.disconnect(cid)

    @property
    def is_connected(self) -> bool:
        return len(self.active_connections) > 0

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


ws_manager = ConnectionManager()