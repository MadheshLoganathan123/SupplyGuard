# SupplyGuard — 30-Day Agentic AI Plan

**Goal:** Agentic supply-chain MVP in 30 days | **API:** `/api/v1` | **Updated:** June 2026

---

## Vision

Agents **perceive** state → **reason** (heuristics + LLM) → **act** on shipments/supply → **log** for operators.

---

## Done (skip)

Dashboard, Logistics, Network, Reports wired to backend + DB. Auth/Profile via Supabase. APIs: shipments, nodes, projections, heuristics, JSON export, incidents, telemetry. SQL: `01_`/`02_`/`03_`. Agent class skeletons exist.

**Still stubbed:** reroute/projection jobs, ProfileService, WebSocket, LLM, PDF export.

---

## Week 1 — Foundation (Days 1–7)

- [ ] **1–2:** Alembic; unify migrations; add `reroute_jobs`, `user_actions`
- [ ] **3–4:** Implement `ProfileService` (CRUD + discover farmers/drivers/stores)
- [ ] **5:** Signup trigger → auto `user_profiles` row
- [ ] **6:** Pick one profile path: backend `/profiles/*` or keep Supabase direct
- [ ] **7:** Enable `agent_logs` Realtime; smoke-test all screens

**Exit:** One migration command; profiles queryable.

---

## Week 2 — Agent Core (Days 8–14)

- [ ] **8–9:** `AgentOrchestrator` + `ProfileContextService`
- [ ] **10–11:** `LogisticsAgent` v1 → real paths in `reroute_jobs`
- [ ] **12:** `SourcingAgent` v1 → store/farmer matching
- [ ] **13:** Wire reroute + projection jobs to orchestrator; apply heuristics
- [ ] **14:** Interventions → agent reply in negotiation hub

**Exit:** Logistics reroute produces agent paths + logs.

---

## Week 3 — Intelligence + Live UI (Days 15–21)

- [ ] **15–16:** `llm_service.py` + structured agent outputs
- [ ] **17:** Agent tools: `find_drivers`, `query_inventory`, `compute_route`
- [ ] **18:** `NegotiationAgent` for pantry/incident coordination
- [ ] **19:** WebSocket `/ws/dashboard`, `/ws/shipments`
- [ ] **20:** Live dashboard ticker; AppShell reroute → backend
- [ ] **21:** Logistics paths from API (remove static cards)

**Exit:** LLM-assisted agent + live updates without full refresh.

---

## Week 4 — Ship (Days 22–30)

- [ ] **22–23:** Reports incident create/resolve; auth guards on heavy endpoints
- [ ] **24:** PDF audit export
- [ ] **25:** Notifications API + AppShell bell
- [ ] **26–27:** Tests — services, agents, reroute integration
- [ ] **28:** Network telemetry-driven nodes; projection uses real inventory
- [ ] **29:** E2E demo: login → incident → reroute → log → export
- [ ] **30:** Staging deploy + README runbook

**Exit:** Demo-ready MVP.

---

## If Behind — Cut Last

| Keep (P0) | Cut first (P4) |
|-----------|----------------|
| Orchestrator + LogisticsAgent reroute | Supply-side portals |
| ProfileService + interventions | PDF/notifications |
| WebSocket updates | Advanced ML forecasting |

---

## Day 30 Checklist

- [ ] Reroute → agent paths → shipment update → dashboard log
- [ ] Heuristics affect agent scoring (visible in logs)
- [ ] Intervention → agent reply < 30s
- [ ] JSON + PDF export from Reports
- [ ] Fresh DB migrates with one command

---

## Key Paths

Backend: `app/agents/`, `app/services/`, `app/api/endpoints/`, `alembic/versions/`  
Frontend: `src/app/page.tsx`, `logistics/page.tsx`, `AppShell.tsx`

---

## Post Day 30

Farmer/driver/store portals, Celery/Redis, ML forecasting, mobile, multi-region.

---

## Progress so far
- Dashboard, Logistics, Network, and Reports screens wired to backend APIs.
- Auth/Profile integration completed via Supabase and backend profile model scaffolding.
- API endpoints implemented for shipments, agents, incidents, and network telemetry.
- SQL migration files created and Alembic configured for schema versioning.
- Agent service skeletons exist for `LogisticsAgent`, `SourcingAgent`, and backend orchestration.
- Backend test coverage added for health and shipment flows.

## Efficiency improvements to make SupplyGuard implementation stronger
- Use structured service layers (`app/services/`) to isolate business logic from API routers.
- Keep agent decisions and reroute rules in dedicated `app/agents/` modules for easier testing.
- Add standardized JSON response helpers so frontend integration is predictable.
- Maintain a shared `config.py` for environment-driven settings and database connection.
- Add seed data scripts for demo-ready farms, stores, and shipments.
- Reserve a lightweight `demo` section in docs for reproducible walkthroughs.
