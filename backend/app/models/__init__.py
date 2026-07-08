"""
ORM model registry — import order matters for FK resolution.
"""

from app.models.user import User
from app.models.farmer import Farmer
from app.models.driver import Driver
from app.models.store import Store
from app.models.inventory import Inventory
from app.models.shipment import Shipment
from app.models.agent import Agent
from app.models.incident import Incident
from app.models.agent_log import AgentLog
from app.models.telemetry import TelemetryMessage
from app.models.intervention import Intervention
from app.models.supply_node import SupplyNode
from app.models.projection import Projection
from app.models.heuristic import Heuristic
from app.models.agent_performance import AgentPerformance
from app.models.export_job import ExportJob
from app.models.reroute_job import RerouteJob
from app.models.notification import Notification

__all__ = [
    "User",
    "Farmer",
    "Driver",
    "Store",
    "Inventory",
    "Shipment",
    "Agent",
    "Incident",
    "AgentLog",
    "TelemetryMessage",
    "Intervention",
    "SupplyNode",
    "Projection",
    "Heuristic",
    "AgentPerformance",
    "ExportJob",
    "RerouteJob",
    "Notification",
]
