"""
SupplyGuard API — entry point.

Run locally:
    uvicorn main:app --reload --port 8000

Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.database.session import engine
from app.database.base import Base

# ── OpenAPI tag metadata (shown as sections in /docs) ─────────────────────────
TAGS_METADATA = [
    {
        "name": "Farmers",
        "description": (
            "Agricultural supply-side nodes — farms, greenhouses, hydroponic units. "
            "Manage registration, geo-location, and AI agent assignments."
        ),
    },
    {
        "name": "Stores",
        "description": (
            "Retail, wholesale, cooperative, and emergency hub distribution points. "
            "Track active status, sector, and manager assignments."
        ),
    },
    {
        "name": "Inventory",
        "description": (
            "Stock levels across all supply nodes (farms, stores, pantries). "
            "Supports low-stock alerts via `low_stock_only` filter."
        ),
    },
    {
        "name": "Drivers",
        "description": (
            "Last-mile and mid-mile delivery fleet — motorcycles, cargo bikes, "
            "vans, trucks, drones, and aerial units. Includes live GPS and utilization tracking."
        ),
    },
    {
        "name": "Shipments",
        "description": (
            "Individual shipment records. "
            "Track status from `pending` through `in_transit`, `rerouted`, to `delivered`."
        ),
    },
    {
        "name": "Agents",
        "description": "AI logistics agents — Logistics, Sourcing, Recipient, and Core AI types.",
    },
    {
        "name": "Incidents",
        "description": (
            "Supply chain disruption events — floods, strikes, road closures. "
            "Severity levels: low → medium → high → critical."
        ),
    },
    {
        "name": "Network",
        "description": "Real-time network telemetry snapshot for the dashboard.",
    },
    {
        "name": "health",
        "description": "Server liveness check.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — DB tables managed by Alembic migrations."""
    # Note: Skipping table creation here to avoid greenlet dependency issues.
    # Use Alembic migrations to manage schema: alembic upgrade head
    yield
    try:
        await engine.dispose()
    except Exception:
        pass  # Gracefully handle disposal errors


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "## SupplyGuard API\n\n"
        "Crisis-response logistics monitoring platform powered by agentic AI.\n\n"
        "### Key capabilities\n"
        "- **Supply nodes** — register and monitor farms, stores, and pantries\n"
        "- **Inventory** — real-time stock levels with low-stock alerts\n"
        "- **Fleet** — track drivers, vehicles, and live GPS positions\n"
        "- **Shipments** — end-to-end delivery tracking with reroute support\n"
        "- **AI Agents** — autonomous logistics, sourcing, and recipient agents\n"
        "- **Incidents** — disruption detection and mitigation tracking\n\n"
        "Base URL: `/api/v1`"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    contact={
        "name": "SupplyGuard Team",
        "url": "https://github.com/your-org/supplyguard",
    },
    license_info={
        "name": "MIT",
    },
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"], summary="Server health check")
async def health_check():
    """Returns `ok` when the server is running."""
    return {"status": "ok", "version": settings.APP_VERSION}
