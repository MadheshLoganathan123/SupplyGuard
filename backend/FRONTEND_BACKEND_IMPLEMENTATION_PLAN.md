# Backend Implementation Plan for SupplyGuard Frontend

Purpose: map each frontend screen to concrete backend work (models, endpoints, services, realtime, jobs, and migrations) needed to fully enable the UI features in the repo.

---

## Quick summary
- Many core APIs already exist (shipments, inventory, agents, incidents, auth). This plan lists gaps and new work required to make the frontend interactive, realtime, and AI-driven.

---

**Screens covered**
- Dashboard (`/`) — negotiation logs, telemetry, threat level, metrics
- Logistics (`/logistics`) — shipments CRUD, path suggestions, reroute actions, register shipments
- Network (`/network`) — topology, node detail, demand projection, node telemetry
- Reports (`/reports`) — incidents, exports, heuristics tuning, agent performance
- Auth (`/auth/*`) — signup/signin/profile management
- AppShell / global — notifications, UI actions (initiate reroute), real-time updates

---

## Per-screen backend requirements

- Dashboard (/)
  - Endpoints:
    - `GET /api/dashboard/metrics` — aggregated metrics (threat level, active disruptions count, supply match %, fleet counts)
    - `GET /api/telemetry/recent?limit=...` — latest telemetry messages for map and node telemetry
    - `GET /api/agent-logs?limit=...` — negotiation hub logs (paginated)
    - `POST /api/interventions` — record operator interventions (operator message -> queued to AI system)
  - Services:
    - `TelemetryService` to aggregate and store incoming telemetry (time-series table)
    - `LogService` to persist agent negotiation logs (and expose search/filter)
    - `DashboardAggregator` to compute metrics from telemetry/shipments/inventory
  - Realtime:
    - Server-sent events (SSE) or WebSocket channel `/ws/dashboard` to push live logs, metrics, and map updates

- Logistics (/logistics)
  - Existing: Shipments endpoints exist at `app/api/endpoints/shipments.py` — verify fields match frontend needs (shipment_code, origin, destination, status, agent).
  - Additional endpoints / features:
    - `POST /api/ai/reroute` — request AI to compute alternate paths for a shipment or a sector (payload: shipment_id or area polygon; result: candidate paths)
    - `POST /api/shipments/{id}/trigger-reroute` — create reroute job and notify clients
    - `GET /api/paths/suggestions?area=...` — cached path suggestions
  - Services:
    - `RoutingService` that calls AI models or agent services to compute routes and returns structured candidate paths
    - `RerouteJob` (background worker) to run potentially long computations and update shipment records
  - Realtime:
    - Push shipment updates via `/ws/shipments` or via pub/sub (Supabase Realtime) so front end table updates without refresh

- Network (/network)
  - Endpoints:
    - `GET /api/nodes` — list topology nodes (type, status, inventory level, threat)
    - `GET /api/nodes/{id}` — node detail (connected logistics, telemetry, images)
    - `POST /api/projections` — run demand projection (returns job id); `GET /api/projections/{id}` result
  - Services:
    - `NodeService` for CRUD and telemetry aggregation
    - `ProjectionService` to schedule/run demand projections (AI/ML job) and store results
  - Data:
    - Telemetry ingestion endpoint `POST /api/telemetry` (node_id, metric, timestamp)
  - Realtime:
    - Node status updates through WS/SSE channel or pub/sub topic

- Reports (/reports)
  - Endpoints:
    - `GET /api/incidents` — list incidents (already exists under incidents endpoint)
    - `POST /api/reports/export?format=pdf|xls|json` — generate and return export (background if large)
    - `GET /api/agents/{id}/performance` — historical performance metrics
    - `POST /api/heuristics` & `GET /api/heuristics` — store/retrieve heuristics settings (affects agent behavior)
  - Services:
    - `ReportingService` to produce exports and audit trails
    - `HeuristicsService` to persist, version, and apply heuristic parameters used by agent runners

- Auth (/auth/*)
  - Current state: frontend uses Supabase client directly (signUp, signInWithPassword). Backend has `app/api/endpoints/auth.py` that wraps supabase auth.
  - Work to choose: either continue direct Supabase auth from frontend, or route auth via backend for server-side checks and profile creation.
  - Required backend items regardless:
    - Ensure `user_profiles` table is populated on signup (function present `register_user_profile`) and an API to read profiles: `GET /api/users/me` (exists as `/me` in auth endpoint)
    - Admin endpoints: `GET /api/users`, `PATCH /api/users/{id}`, `DELETE /api/users/{id}` for user management
    - Role-based access controls in `app/api/dependencies.py` (verify roles map to frontend role labels)

- Profile Management (/profile)
  - New role-specific profile endpoints:
    - `GET /api/profiles/me` — fetch full user profile (base + role-specific data) for current authenticated user
    - `GET /api/profiles/{user_id}` — admin endpoint to fetch any user's profile
    - `POST /api/profiles/update` — update base profile (address, phone, emergency contact, availability_status)
    - `POST /api/profiles/{role}/update` — update role-specific profile (e.g., `/api/profiles/farmer/update` -> upsert to farmer_profiles table)
  - Services:
    - `ProfileService` to handle base + role-specific upserts and reads
    - Enrich farmer/driver/store/pantry/admin data retrieval with profile flags (trust_score, profile_complete)
  - Role-specific data access:
    - Farmers: fetch farm_name, crops_produced, available_quantity, storage_availability, can_self_deliver for sourcing agent queries
    - Drivers: fetch vehicle_type, max_load_kg, operating_radius_km, operating_status for logistics routing
    - Store owners: fetch store_name, inventory_categories, cold_storage_capacity for supply matching
    - Pantry managers: fetch pantry_name, families_served, warehouse_capacity for emergency distribution
    - Admin: fetch managed_regions, authority_level for permissions and scope

- AppShell / global
  - Endpoints:
    - `POST /api/notifications` and `GET /api/notifications` — user notifications
    - `POST /api/actions/reroute` — invoked from UI "Initiate Reroute" to start an AI job; returns immediate ack and pushes updates
  - Misc:
    - Implement throttling, audit logging for heavy actions (reroute, projection, export)

---

## Data model / DB schema changes (recommended)
Add the following tables (replace snake_case names if inconsistent with current models):

- `user_profiles` (extended with location and role context)
  - id UUID PK, auth_id UUID UNIQUE, full_name TEXT, email TEXT, phone TEXT, address TEXT, latitude NUMERIC, longitude NUMERIC
  - availability_status TEXT, emergency_contact_name TEXT, emergency_contact_phone TEXT, emergency_contact_relationship TEXT
  - profile_complete BOOL, trust_score NUMERIC, trust_reviews INT, role TEXT (enum), additional_credentials TEXT
  - created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

- `farmer_profiles` (role-specific)
  - id UUID PK, auth_id UUID UNIQUE (FK -> user_profiles), farm_name TEXT, farm_type TEXT, crops_produced TEXT[], farm_size_acres NUMERIC
  - available_quantity NUMERIC, expected_harvest_date DATE, storage_availability TEXT, can_self_deliver BOOL, max_delivery_distance_km NUMERIC
  - organic_certification TEXT, government_registration_number TEXT, fssai_number TEXT, emergency_response_ready BOOL
  - created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

- `driver_profiles` (role-specific)
  - id UUID PK, auth_id UUID UNIQUE (FK -> user_profiles), vehicle_type TEXT, vehicle_plate TEXT, max_load_kg NUMERIC, vehicle_capacity_description TEXT
  - license_number TEXT, license_expiry DATE, vehicle_insurance_provider TEXT, insurance_valid_until DATE, permit_reference TEXT
  - current_latitude NUMERIC, current_longitude NUMERIC, operating_radius_km NUMERIC, available_weekdays TEXT
  - night_delivery_allowed BOOL, flood_zone_access BOOL, emergency_ready BOOL
  - created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

- `store_profiles` (role-specific)
  - id UUID PK, auth_id UUID UNIQUE (FK -> user_profiles), store_name TEXT, store_type TEXT, inventory_categories TEXT[]
  - cold_storage_capacity NUMERIC, average_daily_customers INT, average_daily_demand INT
  - current_suppliers TEXT[], alternative_suppliers TEXT[], accepts_emergency_deliveries BOOL, priority_supply_requests BOOL
  - created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

- `pantry_profiles` (role-specific)
  - id UUID PK, auth_id UUID UNIQUE (FK -> user_profiles), pantry_name TEXT, organization_type TEXT, families_served INT, population_covered INT
  - food_requirements TEXT[], has_cold_storage BOOL, warehouse_capacity INT, volunteer_count INT, vehicles_available INT
  - emergency_distribution_capacity INT, distribution_radius_km NUMERIC
  - created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

- `admin_profiles` (role-specific)
  - id UUID PK, auth_id UUID UNIQUE (FK -> user_profiles), organization_name TEXT, department TEXT, designation TEXT, authority_level TEXT
  - managed_regions TEXT[], managed_districts TEXT[], can_approve_routes BOOL, can_broadcast_notifications BOOL
  - created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

- `profile_documents` (optional credential links)
  - id UUID PK, auth_id UUID (FK -> user_profiles), document_type TEXT, document_url TEXT, note TEXT, created_at TIMESTAMPTZ

- `profile_locations` (location history for routing context)
  - id UUID PK, auth_id UUID (FK -> user_profiles), label TEXT, latitude NUMERIC, longitude NUMERIC, recorded_at TIMESTAMPTZ

- `telemetry` (time-series)
  - id UUID PK, node_id UUID (nullable), shipment_id UUID (nullable), type TEXT (metric type), payload JSONB, created_at TIMESTAMPTZ

- `agent_logs`
  - id UUID, source TEXT, agent_id UUID (nullable), level TEXT, message TEXT, metadata JSONB, created_at

- `heuristics`
  - id UUID, name TEXT, payload JSONB, version INT, created_by UUID, created_at, active BOOL

- `projections` (jobs)
  - id UUID, type TEXT, input JSONB, result JSONB, status TEXT (queued/running/done/failed), started_at, finished_at

- `reroute_jobs`
  - id UUID, shipment_id UUID, input JSONB, candidate_paths JSONB, status TEXT, created_at, finished_at

- `notifications`
  - id UUID, user_id UUID, title TEXT, body TEXT, meta JSONB, read BOOL, created_at

- `agent_performance`
  - id UUID, agent_id UUID, metrics JSONB (time-series summary), recorded_at

- Audit tables: `export_jobs`, `user_actions`

Note: some domain tables already exist (`shipments`, `inventory`, `agents`, `incidents`, `stores`, `drivers`) — review and extend columns as needed (e.g., add `last_seen`, `location`, `telemetry_summary` fields).

Migrations: create Alembic migrations for each new table and any column additions.

---

## API surface (signature examples)
(Use these to scaffold FastAPI routers in `app/api/endpoints/` and services in `app/services/`)

- Profiles (new)
  - GET /api/profiles/me -> { user_id, full_name, email, role, phone, address, latitude, longitude, trust_score, profile_complete, ..., role_specific_data }
  - GET /api/profiles/{user_id} -> same (admin only or same user)
  - POST /api/profiles/update-base -> { full_name, phone, address, latitude, longitude, availability_status, emergency_contact_* }
  - POST /api/profiles/farmer/update -> { farm_name, farm_type, crops_produced[], available_quantity, ... } (farmer only)
  - POST /api/profiles/driver/update -> { vehicle_type, max_load_kg, operating_radius_km, license_number, ... } (driver only)
  - POST /api/profiles/store/update -> { store_name, inventory_categories[], cold_storage_capacity, ... } (store owner only)
  - POST /api/profiles/pantry/update -> { pantry_name, families_served, food_requirements[], ... } (pantry manager only)
  - POST /api/profiles/admin/update -> { organization_name, authority_level, managed_regions[], ... } (admin only)
  - GET /api/profiles/discover?role=farmer&crop=rice&radius=50 -> { profiles[] } (discover farmers by crop, region, distance)
  - GET /api/profiles/discover?role=driver&location=lat,lng&vehicle_type=truck -> { profiles[] } (discover drivers by capability)
  - GET /api/profiles/discover?role=store&category=dairy&location=lat,lng -> { profiles[] } (discover stores by inventory type)

- Telemetry
  - POST /api/telemetry
    - body: { node_id?: uuid, shipment_id?: uuid, type: string, payload: object }
    - response: 202 Accepted
  - GET /api/telemetry/recent?node_id=&limit=

- Dashboard
  - GET /api/dashboard/metrics -> { threatLevel, activeDisruptions, supplyMatchPct, fleetCounts }
  - GET /api/agent-logs?limit=&since=
  - POST /api/interventions -> { user_id, text } -> returns { id, status }

- Shipments (existing)
  - POST /api/shipments -> create (ensure frontend modal fields match schema)
  - POST /api/shipments/{id}/trigger-reroute -> kicks off reroute job

- Routing / AI
  - POST /api/ai/reroute -> { shipment_id?, area?: GeoJSON, constraints?: {} } -> { job_id }
  - GET /api/ai/reroute/{job_id} -> { status, results }

- Nodes & Projections
  - GET /api/nodes
  - GET /api/nodes/{id}
  - POST /api/projections -> { node_ids[], horizon, params } -> { job_id }
  - GET /api/projections/{id}

- Heuristics
  - GET /api/heuristics
  - POST /api/heuristics -> { name, payload } (only admin)

- Reports / Exports
  - POST /api/reports/export?format=pdf|xls|json -> { query, job_id }
  - GET /api/reports/export/{job_id}

- Notifications
  - GET /api/notifications?user_id=
  - POST /api/notifications -> create push

---

## Realtime & streaming
Options:
- WebSocket endpoints under FastAPI (`/ws/shipments`, `/ws/dashboard`) + Redis PUB/SUB for cross-process notifications
- Or rely on Supabase Realtime for DB-driven real-time updates (keep Supabase client/server tokens managed securely)

Implementations needed:
- WS manager in backend to broadcast job progress, new telemetry, and agent logs
- Emit events when shipments/inventory/incidents change

---

## Background workers & AI agents
- Use a queue system (Redis + RQ, Celery, or built-in asyncio tasks with persistent job state in DB)
- Jobs:
  - Reroute job (calls routing model / agent service)
  - Projection job (demand forecasting)
  - Export job (generate PDF/XLS/JSON)
- Agent runners:
  - `LogisticsAgent`, `SourcingAgent`, `NegotiationAgent` as orchestrators that accept input, run AI models, and write results to DB + publish events

Design: keep AI model calls behind service layer so they can be swapped (local, hosted, or external) and cached.

---

## Agent enhancements with role-specific profiles

Agents should now leverage profile data to:

- **LogisticsAgent** (reroute planning, shipment optimization)
  - Fetch available drivers via `driver_profiles` (vehicle_type, max_load_kg, operating_radius_km, availability)
  - Fetch store demand via `store_profiles` (average_daily_demand, cold_storage_capacity, priority_supply_requests)
  - Consider emergency capabilities (drivers with emergency_ready=true, stores accepting_emergency_deliveries=true)
  - Filter routes by driver capability (night_delivery_allowed, flood_zone_access) and store acceptance criteria

- **SourcingAgent** (supply matching, farmer sourcing, inventory projection)
  - Query available farmers via `farmer_profiles` (crops_produced, available_quantity, can_self_deliver, max_delivery_distance_km)
  - Match store demand (from `store_profiles.inventory_categories`) against farmer supply (from `farmer_profiles.crops_produced`)
  - Consider storage (farmer storage_availability vs. store cold_storage_capacity)
  - Trust scores from `user_profiles.trust_score` to bias toward reliable suppliers

- **NegotiationAgent** (demand distribution, pantry coordination)
  - Query pantries via `pantry_profiles` (families_served, food_requirements, warehouse_capacity, emergency_distribution_capacity)
  - Match emergency distribution needs with pantry volunteer counts, vehicle capacity, and distribution radius
  - Coordinate with store owners (via `store_profiles`) on emergency stock allocations

- **Profile context helpers**
  - Create service: `ProfileContextService.get_agent_view(user_id, role)` to fetch all role-specific data needed by agents
  - Implement geospatial queries: "drivers within X km of location", "stores in region", "farms with crop type in zone"
  - Cache profile views to reduce repeated queries during agent execution

- **Enriched event payloads**
  - When emitting shipment/inventory/incident updates to agents, include originating user's profile snapshot (name, role, location, authority)
  - Log all agent decisions with profile references for audit trails and heuristic tuning

---

## Auth, roles & permissions
- Use existing `user_profiles` table and `auth` endpoints. Ensure mapping between frontend role labels (Farmer, Driver, Store Owner, Pantry Manager, Admin) and backend `UserRole` enum in `app/schemas/user.py`.
- Protect heavy endpoints (reroute, projections, heuristics, exports) with role checks (admin or specific roles).
- Validate identity propagation for WS connections (token-based auth on WS connect)

---

## Exports, auditing & compliance
- All exports and heavy actions must be recorded in `export_jobs` or `user_actions` for auditability.
- Add rate-limiting for export endpoints.

---

## Testing & verification
- Unit tests for services and routers (add tests under `backend/tests` similar to `test_shipments.py`).
- Integration tests for WS flow and long-running jobs (use test Redis instance or sync job runner in tests).

---

## Priority checklist (implementation order)
1. Profile endpoints: `GET /api/profiles/me`, `POST /api/profiles/{role}/update`, discovery endpoints (high) — enables frontend profile page and agent profile enrichment
2. Telemetry ingestion + storage + `GET /api/telemetry/recent` (high)
3. Dashboard aggregation endpoint `GET /api/dashboard/metrics` (high)
4. Ensure shipments API matches frontend create modal (high)
5. WebSocket or SSE push mechanism for agent logs and shipment updates (high)
6. `POST /api/ai/reroute` + reroute job + job status endpoints (medium)
7. Nodes endpoints + `POST /api/projections` (medium) — integrate with driver & farm profiles for location-aware queries
8. Heuristics endpoints and persistence (medium)
9. Reports export jobs and audit logging (low-medium)
10. Notifications + admin user management endpoints (low)

---

## Estimated implementation notes (rough)
- Basic telemetry + dashboard endpoints: 1–3 days
- WebSocket + job runner + reroute job scaffold: 3–5 days
- Projection service + heuristics: 3–7 days (depends on models)
- Exports and audit: 1–2 days

---

## Next steps I can take for you (pick one)
- Scaffold the missing FastAPI routers and Pydantic schemas for telemetry, projections, reroute jobs
- Add Alembic migrations for the new tables
- Implement a WebSocket manager and sample publish/subscribe pattern
- Wire a simple reroute job that returns a mocked candidate path


---

File created: backend/FRONTEND_BACKEND_IMPLEMENTATION_PLAN.md
