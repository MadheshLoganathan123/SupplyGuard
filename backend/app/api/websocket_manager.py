"""
WebSocket Manager — Manages WebSocket connections and broadcasting for real-time updates.
"""

import json
import logging
from typing import Any, Callable

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {
            "dashboard": [],
            "shipments": [],
        }
        self.callbacks: dict[str, list[Callable]] = {
            "dashboard": [],
            "shipments": [],
        }

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"Client connected to {channel}. Total: {len(self.active_connections[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a disconnected client."""
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            logger.info(f"Client disconnected from {channel}. Total: {len(self.active_connections[channel])}")

    async def broadcast(self, channel: str, data: dict[str, Any]) -> None:
        """Broadcast a message to all clients on a channel."""
        if channel not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws, channel)

    async def send_personal(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"Error sending personal message: {e}")

    def register_callback(self, channel: str, callback: Callable) -> None:
        """Register a callback to be invoked when messages arrive."""
        if channel not in self.callbacks:
            self.callbacks[channel] = []
        self.callbacks[channel].append(callback)

    async def invoke_callbacks(self, channel: str, data: dict[str, Any]) -> None:
        """Invoke all registered callbacks for a channel."""
        if channel in self.callbacks:
            for callback in self.callbacks[channel]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.exception(f"Error invoking callback: {e}")


# Global connection manager instance
manager = ConnectionManager()
