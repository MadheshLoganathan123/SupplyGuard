"""
Endpoint registry — used by `app.api.router` to import all API endpoint modules.
"""

from app.api.endpoints import agents, auth, dashboard, drivers, farmers, incidents, inventory, network, shipments, stores

__all__ = [
    "agents",
    "auth",
    "dashboard",
    "drivers",
    "farmers",
    "incidents",
    "inventory",
    "network",
    "shipments",
    "stores",
]
