"""
Root API router — registers all versioned sub-routers.
"""

from fastapi import APIRouter

from app.api.endpoints import (
    agents,
    auth,
    drivers,
    farmers,
    incidents,
    inventory,
    network,
    shipments,
    stores,
)

api_router = APIRouter()

# ── Supply-side nodes ─────────────────────────────────────────────────────────
api_router.include_router(farmers.router,   prefix="/farmers",   tags=["Farmers"])
api_router.include_router(stores.router,    prefix="/stores",    tags=["Stores"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])

# ── Logistics fleet ───────────────────────────────────────────────────────────
api_router.include_router(drivers.router,   prefix="/drivers",   tags=["Drivers"])
api_router.include_router(shipments.router, prefix="/shipments", tags=["Shipments"])

# ── Monitoring & intelligence ─────────────────────────────────────────────────
api_router.include_router(auth.router,     prefix="/auth",      tags=["Auth"])
api_router.include_router(agents.router,    prefix="/agents",    tags=["Agents"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(network.router,   prefix="/network",   tags=["Network"])
