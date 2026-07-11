import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, investigation_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(investigation_id, set()).add(ws)
        logger.debug("WebSocket connected for investigation %s", investigation_id)

    def disconnect(self, investigation_id: str, ws: WebSocket) -> None:
        self._connections.get(investigation_id, set()).discard(ws)
        if not self._connections.get(investigation_id):
            self._connections.pop(investigation_id, None)
        logger.debug("WebSocket disconnected for investigation %s", investigation_id)

    async def broadcast(self, investigation_id: str, message: dict[str, Any]) -> None:
        connections = self._connections.get(investigation_id, set())
        if not connections:
            return
        payload = json.dumps(message)
        stale = set()
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning("WebSocket send error: %s", e)
                stale.add(ws)
        for ws in stale:
            self.disconnect(investigation_id, ws)


ws_manager = WebSocketManager()
