"""
Root API router — registers all versioned sub-routers.
"""

from fastapi import APIRouter

from app.api.endpoints import (
    agents,
    auth,
    dashboard,
    drivers,
    farmers,
    heuristics,
    incidents,
    inventory,
    network,
    nodes,
    profiles,
    projections,
    reports,
    routing,
    shipments,
    stores,
    websocket,
)

api_router = APIRouter()

# ── Supply-side nodes ─────────────────────────────────────────────────────────
api_router.include_router(farmers.router,   prefix="/farmers",   tags=["Farmers"])
api_router.include_router(stores.router,    prefix="/stores",    tags=["Stores"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])

# ── Logistics fleet ───────────────────────────────────────────────────────────
api_router.include_router(drivers.router,   prefix="/drivers",   tags=["Drivers"])
api_router.include_router(shipments.router, prefix="/shipments", tags=["Shipments"])
api_router.include_router(routing.router,   prefix="/routing",   tags=["Routing"])

# ── Auth & user profiles ──────────────────────────────────────────────────────
api_router.include_router(auth.router,      prefix="/auth",      tags=["Auth"])
api_router.include_router(profiles.router,                       tags=["Profiles"])  # has its own /profiles prefix

# ── Monitoring & intelligence ─────────────────────────────────────────────────
api_router.include_router(agents.router,    prefix="/agents",    tags=["Agents"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(network.router,   prefix="/network",   tags=["Network"])
api_router.include_router(nodes.router,     prefix="/nodes",     tags=["Nodes"])
api_router.include_router(projections.router, prefix="/projections", tags=["Projections"])
api_router.include_router(heuristics.router, prefix="/heuristics", tags=["Heuristics"])
api_router.include_router(reports.router,   prefix="/reports",   tags=["Reports"])

# ── Real-time updates ─────────────────────────────────────────────────────────
api_router.include_router(websocket.router, tags=["WebSocket"])


# ── Dashboard (mounts at root so /dashboard/metrics, /agent-logs, etc. work) ─
api_router.include_router(dashboard.router, prefix="",           tags=["Dashboard"])
