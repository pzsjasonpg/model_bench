"""WebSocket connection manager for real-time log streaming."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections grouped by test_run_id."""

    def __init__(self):
        # test_run_id -> list of active WebSocket connections
        self._connections: Dict[int, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, test_run_id: int, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            if test_run_id not in self._connections:
                self._connections[test_run_id] = []
            self._connections[test_run_id].append(ws)

    async def disconnect(self, test_run_id: int, ws: WebSocket):
        async with self._lock:
            if test_run_id in self._connections:
                try:
                    self._connections[test_run_id].remove(ws)
                except ValueError:
                    pass
                if not self._connections[test_run_id]:
                    del self._connections[test_run_id]

    async def broadcast(self, test_run_id: int, message: Dict[str, Any]):
        """Send a JSON message to all clients listening for a test run."""
        async with self._lock:
            conns = list(self._connections.get(test_run_id, []))

        payload = json.dumps(message, ensure_ascii=False)
        dead = []
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    try:
                        self._connections.get(test_run_id, []).remove(ws)
                    except ValueError:
                        pass

    async def broadcast_log(self, test_run_id: int, subtask_id: int, line: str, timestamp: str):
        await self.broadcast(test_run_id, {
            "type": "log",
            "subtask_id": subtask_id,
            "line": line,
            "timestamp": timestamp,
        })

    async def broadcast_status(self, test_run_id: int, subtask_id: int, status: str, result: Dict[str, Any] = None):
        msg: Dict[str, Any] = {
            "type": "status",
            "subtask_id": subtask_id,
            "status": status,
        }
        if result is not None:
            msg["result"] = result
        await self.broadcast(test_run_id, msg)

    async def broadcast_done(self, test_run_id: int):
        await self.broadcast(test_run_id, {"type": "done"})


# Singleton instance
ws_manager = ConnectionManager()
