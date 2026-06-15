# SupplyGuard — Backend API

FastAPI + SQLAlchemy (async) + PostgreSQL backend for the SupplyGuard crisis-response logistics platform.

---

## Folder Structure

```
backend/
├── alembic/                  # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── agents/               # AI agent logic (perceive → decide → act)
│   │   ├── base_agent.py
│   │   ├── logistics_agent.py
│   │   └── sourcing_agent.py
│   ├── api/                  # FastAPI routers & endpoints
│   │   ├── router.py
│   │   └── endpoints/
│   │       ├── agents.py
│   │       ├── incidents.py
│   │       ├── network.py
│   │       └── shipments.py
│   ├── core/
│   │   └── config.py         # pydantic-settings config
│   ├── database/
│   │   ├── base.py           # DeclarativeBase + model imports
│   │   └── session.py        # Async engine + get_db dependency
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── agent.py
│   │   ├── incident.py
│   │   └── shipment.py
│   ├── schemas/              # Pydantic request / response schemas
│   │   ├── agent.py
│   │   ├── incident.py
│   │   └── shipment.py
│   ├── services/             # Business logic layer
│   │   ├── agent_service.py
│   │   ├── incident_service.py
│   │   └── shipment_service.py
│   └── utils/
│       ├── responses.py      # Standardised JSON helpers
│       └── security.py       # JWT + bcrypt utilities
├── tests/
│   ├── conftest.py           # Pytest fixtures (in-memory SQLite)
│   ├── test_health.py
│   └── test_shipments.py
├── .env.example
├── .gitignore
├── alembic.ini
├── main.py
└── requirements.txt
```

---

## Quick Start

### 1. Create & activate virtual environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL and SECRET_KEY
```

### 4. Start PostgreSQL (Docker)

```bash
docker run -d \
  --name supplyguard-db \
  -e POSTGRES_USER=supplyguard \
  -e POSTGRES_PASSWORD=supplyguard \
  -e POSTGRES_DB=supplyguard_db \
  -p 5432:5432 \
  postgres:16-alpine
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the API server

```bash
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server health check |
| GET | `/api/v1/shipments/` | List all shipments |
| POST | `/api/v1/shipments/` | Create a shipment |
| PATCH | `/api/v1/shipments/{id}` | Update a shipment |
| DELETE | `/api/v1/shipments/{id}` | Delete a shipment |
| GET | `/api/v1/agents/` | List all agents |
| POST | `/api/v1/agents/` | Register an agent |
| PATCH | `/api/v1/agents/{id}` | Update agent status |
| GET | `/api/v1/incidents/` | List incidents |
| POST | `/api/v1/incidents/` | Report an incident |
| PATCH | `/api/v1/incidents/{id}` | Update an incident |
| GET | `/api/v1/network/health` | Dashboard telemetry snapshot |
