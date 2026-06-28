"""
WebSocket Endpoints — Real-time updates for dashboard and shipments.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.websocket_manager import manager
from app.services.dashboard_service import DashboardService
from app.services.shipment_service import ShipmentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for dashboard real-time updates.
    
    Broadcasts:
    - Agent status updates
    - Shipment status changes
    - Incident alerts
    - Dashboard metrics (live ticker)
    """
    await manager.connect(websocket, "dashboard")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "ping":
                    # Keep-alive check
                    await manager.send_personal(websocket, {"type": "pong"})
                elif action == "request_update":
                    # Client requests current dashboard state
                    await manager.send_personal(
                        websocket,
                        {"type": "dashboard_state", "message": "requesting fresh state"},
                    )
                else:
                    logger.warning(f"Unknown action: {action}")
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on dashboard WebSocket")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.exception(f"Error in dashboard WebSocket: {e}")
        manager.disconnect(websocket, "dashboard")


@router.websocket("/ws/shipments")
async def websocket_shipments(websocket: WebSocket):
    """
    WebSocket endpoint for shipment real-time updates.
    
    Broadcasts:
    - Shipment status changes
    - Route updates
    - Driver location updates
    - ETA changes
    """
    await manager.connect(websocket, "shipments")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "ping":
                    # Keep-alive check
                    await manager.send_personal(websocket, {"type": "pong"})
                elif action == "subscribe_shipment":
                    # Subscribe to specific shipment updates
                    shipment_id = message.get("shipment_id")
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "subscribed",
                            "shipment_id": shipment_id,
                            "message": f"Subscribed to shipment {shipment_id}",
                        },
                    )
                elif action == "request_update":
                    # Request current shipment data
                    await manager.send_personal(
                        websocket,
                        {"type": "shipments_state", "message": "requesting fresh state"},
                    )
                else:
                    logger.warning(f"Unknown action: {action}")
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on shipments WebSocket")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "shipments")
        logger.info("Shipments WebSocket disconnected")
    except Exception as e:
        logger.exception(f"Error in shipments WebSocket: {e}")
        manager.disconnect(websocket, "shipments")


# Utility functions for broadcasting updates from other endpoints

async def broadcast_dashboard_update(update: dict[str, Any]) -> None:
    """Broadcast a dashboard update to all connected dashboard clients."""
    message = {
        "type": "dashboard_update",
        "data": update,
    }
    await manager.broadcast("dashboard", message)


async def broadcast_shipment_update(shipment_id: str, update: dict[str, Any]) -> None:
    """Broadcast a shipment update to all connected shipment clients."""
    message = {
        "type": "shipment_update",
        "shipment_id": shipment_id,
        "data": update,
    }
    await manager.broadcast("shipments", message)


async def broadcast_incident_alert(incident: dict[str, Any]) -> None:
    """Broadcast an incident alert to dashboard clients."""
    message = {
        "type": "incident_alert",
        "severity": incident.get("severity", "normal"),
        "data": incident,
    }
    await manager.broadcast("dashboard", message)


async def broadcast_agent_action(agent_action: dict[str, Any]) -> None:
    """Broadcast an agent action to dashboard clients."""
    message = {
        "type": "agent_action",
        "data": agent_action,
    }
    await manager.broadcast("dashboard", message)
