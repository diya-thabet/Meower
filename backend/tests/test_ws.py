import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket

from app.ws.manager import ws_manager


@pytest.fixture(autouse=True)
def clear_connections():
    ws_manager._connections = {}


@pytest.mark.anyio
class TestWebSocketManager:
    async def test_connect_and_disconnect(self):
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()

        await ws_manager.connect("inv-1", mock_ws)
        assert "inv-1" in ws_manager._connections
        assert mock_ws in ws_manager._connections["inv-1"]

        ws_manager.disconnect("inv-1", mock_ws)
        assert "inv-1" not in ws_manager._connections

    async def test_multiple_connections(self):
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()

        await ws_manager.connect("inv-1", mock_ws1)
        await ws_manager.connect("inv-1", mock_ws2)
        assert len(ws_manager._connections["inv-1"]) == 2

        ws_manager.disconnect("inv-1", mock_ws1)
        assert mock_ws2 in ws_manager._connections["inv-1"]

    async def test_disconnect_unknown_investigation(self):
        mock_ws = MagicMock(spec=WebSocket)
        ws_manager.disconnect("nonexistent", mock_ws)

    async def test_disconnect_unknown_ws(self):
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        await ws_manager.connect("inv-1", mock_ws)
        other_ws = MagicMock(spec=WebSocket)
        ws_manager.disconnect("inv-1", other_ws)
        assert mock_ws in ws_manager._connections["inv-1"]

    async def test_broadcast(self):
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()
        await ws_manager.connect("inv-1", mock_ws)

        await ws_manager.broadcast("inv-1", {"type": "status", "status": "running"})
        mock_ws.send_text.assert_awaited_once_with('{"type": "status", "status": "running"}')

    async def test_broadcast_no_connections(self):
        await ws_manager.broadcast("nonexistent", {"type": "status", "status": "done"})

    async def test_broadcast_stale_connection_removed(self):
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        await ws_manager.connect("inv-1", mock_ws)

        await ws_manager.broadcast("inv-1", {"type": "status", "status": "done"})
        assert "inv-1" not in ws_manager._connections

    async def test_broadcast_partial_failure(self):
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock(side_effect=Exception("Closed"))

        await ws_manager.connect("inv-1", mock_ws1)
        await ws_manager.connect("inv-1", mock_ws2)

        await ws_manager.broadcast("inv-1", {"type": "status", "status": "done"})
        mock_ws1.send_text.assert_awaited_once()
        assert "inv-1" in ws_manager._connections
        assert mock_ws1 in ws_manager._connections["inv-1"]

    async def test_connect_accept_called(self):
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        await ws_manager.connect("inv-1", mock_ws)
        mock_ws.accept.assert_awaited_once()

    async def test_connect_existing_investigation_appends(self):
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()

        await ws_manager.connect("inv-1", mock_ws1)
        await ws_manager.connect("inv-1", mock_ws2)

        assert len(ws_manager._connections["inv-1"]) == 2

    async def test_broadcast_multiple_receivers(self):
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        await ws_manager.connect("inv-1", mock_ws1)
        await ws_manager.connect("inv-1", mock_ws2)

        await ws_manager.broadcast("inv-1", {"type": "test", "data": "hello"})
        mock_ws1.send_text.assert_awaited_once()
        mock_ws2.send_text.assert_awaited_once()
