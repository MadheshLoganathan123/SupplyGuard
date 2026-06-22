# Week 2 Agent Core — Developer Quick Start

## Overview

The SupplyGuard agent core is now fully operational. This guide shows how to use it.

---

## Quick Integration Examples

### 1. Process a Single Shipment (Python)

```python
from app.agents.orchestrator import AgentOrchestrator
from app.database.session import AsyncSessionLocal

async def reroute_shipment(shipment_id: str, incident_ids: list[str]):
    async with AsyncSessionLocal() as db:
        orchestrator = AgentOrchestrator(db)
        
        result = await orchestrator.run_for_shipment(
            shipment_id=shipment_id,
            incident_ids=incident_ids
        )
        
        # Result contains:
        # - shipment: Updated Shipment object
        # - actions: List of AgentAction objects
        # - logs: List of AgentLog entries
        # - heuristic_adjustments: Applied heuristics
        
        return result
```

### 2. Process a Sector (Batch)

```python
async def reroute_sector(sector: str, threat_level: str):
    async with AsyncSessionLocal() as db:
        orchestrator = AgentOrchestrator(db)
        
        result = await orchestrator.run_for_sector(
            sector=sector,
            threat_level=threat_level,  # NORMAL, ELEVATED, CRITICAL
            incident_ids=["inc1", "inc2"]
        )
        
        print(f"Processed {result['shipments_processed']} shipments")
        return result
```

### 3. Run Demand Projection with Agent Sourcing

```python
from app.services.projection_service import run_projection_job

async def project_demand(projection_id: str):
    result = await run_projection_job(
        projection_id=projection_id,
        use_agent_orchestrator=True  # Invoke SourcingAgent if gap > 2%
    )
    
    print(f"Supply-demand gap: {result['result']['supply_demand_gap_pct']}%")
    print(f"Heuristics applied: {result['result']['heuristics_applied']}")
    return result
```

### 4. Process Operator Intervention

```python
from app.services.intervention_service import process_intervention

async def handle_intervention(intervention_id: str):
    result = await process_intervention(intervention_id)
    
    # result contains:
    # - status: "resolved" or "escalated"
    # - intervention_type: "REROUTE", "ALLOCATE_SUPPLY", or "NEGOTIATE"
    # - agent_responses: Responses from agents
    
    return result
```

### 5. Async Background Job (Celery-ready)

```python
from app.services.reroute_job import run_reroute_job

# In a background task queue:
async def reroute_task(shipment_id: str):
    return await run_reroute_job(
        shipment_id=shipment_id,
        incident_ids=[]
    )
    
# Returns:
# {
#     "shipment_id": "uuid",
#     "shipment_code": "SHP-001",
#     "status": "REROUTED",
#     "action_taken": "REROUTE",
#     "confidence": 0.92,
#     "logs_created": 2,
#     "selected_driver": "Driver A",
#     "selected_store": "Store B"
# }
```

---

## API Usage

### Single Shipment Reroute

```bash
curl -X POST http://localhost:8000/api/v1/agents/orchestrate/reroute \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
    "incident_ids": ["incident-123"]
  }'
```

**Response:**
```json
{
  "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
  "shipment_code": "SHP-001",
  "status": "REROUTED",
  "action_taken": "REROUTE",
  "confidence": 0.92,
  "logs_created": 2,
  "selected_driver": "Driver Alpha (Truck 5)",
  "selected_store": "Store B (North)"
}
```

### Sector-wide Reroute

```bash
curl -X POST http://localhost:8000/api/v1/agents/orchestrate/sector \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "NORTH",
    "threat_level": "CRITICAL",
    "incident_ids": ["flood-001", "road-block-002"]
  }'
```

### Async Reroute Job

```bash
curl -X POST http://localhost:8000/api/v1/agents/jobs/reroute \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Operator Intervention

```bash
# Intervention text examples:
# - "Reroute shipment SHP-001 due to flood"
# - "Allocate supply from North to South sector"
# - "Negotiate with Store B for emergency delivery"

curl -X POST http://localhost:8000/api/v1/agents/jobs/intervention \
  -H "Content-Type: application/json" \
  -d '{
    "intervention_id": "intv-456"
  }'
```

---

## Understanding Agent Decisions

### LogisticsAgent Decision Process

1. **Perceive:** Fetch drivers and stores from Supabase
2. **Filter Drivers:** By capacity, emergency-readiness, location
3. **Filter Stores:** By emergency acceptance, cold-storage
4. **Score & Rank:** Select best driver and store
5. **Decide:** Return REROUTE action with selected resources
6. **Confidence:** 0.85–0.95 based on match quality

### SourcingAgent Decision Process

1. **Perceive:** Fetch farmers and stores from Supabase
2. **Match:** Compute score for each farmer-store pair
3. **Score Factors:**
   - Crop type match (30%)
   - Quantity compatibility (40%)
   - Farmer trust score (20%)
   - Self-delivery capability (10%)
4. **Decide:** Return ALLOCATE_SURPLUS or REQUEST_RESUPPLY
5. **Confidence:** 0.85–0.88 based on match count

### Heuristic Adjustments

Active heuristics can:
- **Increase confidence:** If high-trust farmers available (+0.1)
- **Decrease confidence:** If multiple competing demands (-0.05)
- **Flag for review:** If supply gap > 5%
- **Override decision:** Via trigger matching (threat_level, incident count)

**Check applied heuristics in logs:**
```python
result = await orchestrator.run_for_shipment(shipment_id)
heuristics = result["heuristic_adjustments"]
print(f"Applied rules: {heuristics['applied_rules']}")
print(f"Confidence adjustment: {heuristics['confidence_adjustments']}")
```

---

## Logging & Audit Trail

### Fetch Agent Logs for a Shipment

```python
from app.services.agent_log_service import AgentLogService

async def get_shipment_audit_trail(shipment_id: str, db):
    log_svc = AgentLogService(db)
    logs = await log_svc.get_agent_logs_by_shipment(shipment_id)
    
    for log in logs:
        print(f"{log.agent_name}: {log.action_type} (confidence={log.confidence})")
        print(f"  Payload: {log.payload}")
```

### Fetch Sector-level Activity

```python
async def get_sector_activity(sector: str, db):
    log_svc = AgentLogService(db)
    logs = await log_svc.get_agent_logs_by_sector(sector, limit=100)
    
    reroutes = sum(1 for log in logs if log.action_type == "REROUTE")
    allocations = sum(1 for log in logs if log.action_type == "ALLOCATE_SUPPLY")
    
    print(f"Sector {sector}: {reroutes} reroutes, {allocations} allocations")
```

---

## Debugging

### Check Agent Logic

```python
from app.agents.logistics_agent import LogisticsAgent
from app.agents.base_agent import AgentContext

# Directly test agent decision
agent = LogisticsAgent()
context = AgentContext(
    sector="NORTH",
    threat_level="CRITICAL",
    active_incidents=["flood-001"],
    metadata={"origin": "Farm A", "destination": "Store B"}
)

perception = await agent.perceive(context)
action = await agent.decide(perception)

print(f"Decision: {action.action_type}")
print(f"Confidence: {action.confidence}")
print(f"Payload: {action.payload}")
```

### Check Profile Context

```python
from app.services.profile_context_service import ProfileContextService

context_svc = ProfileContextService(db)
context = await context_svc.build_context(shipment, incident_ids=["flood"])

print(f"Threat level: {context.threat_level}")
print(f"Inventory status: {context.inventory_status}")
print(f"Available drivers: {context.metadata['driver_availability']}")
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Agent not found" | Agent name mismatch | Use exact names: "LogisticsAgent", "SourcingAgent" |
| Confidence too low | No matching drivers/stores | Check Supabase profiles exist and match shipment specs |
| Heuristics not applied | No active heuristic | Create heuristic via `/api/v1/heuristics` |
| Slow orchestration | Large sector with many shipments | Use `run_for_shipment()` for single vs `run_for_sector()` for batch |
| Logs not broadcast | WebSocket not connected | Check `manager.broadcast()` in agent_log_service |

---

## Next Week (Week 3)

- Replace stub agent logic with LLM-powered reasoning
- Add agent tools: `find_drivers()`, `query_inventory()`, `compute_route()`
- Implement NegotiationAgent for pantry/incident coordination
- Wire WebSocket updates for real-time dashboard ticker
- Add structured output parsing from LLM responses

---

## Architecture Overview

```
API Request
  ↓
Endpoint Handler
  ↓
AgentOrchestrator.run_for_shipment()
  ↓
ProfileContextService.build_context() [Fetches Supabase profiles]
  ↓
LogisticsAgent.perceive() → decide() [Real driver/store selection]
  ↓
SourcingAgent.perceive() → decide() [Supply matching]
  ↓
HeuristicsService.get_active() [Apply confidence tuning]
  ↓
AgentLogService.create_log() [Audit trail + WebSocket broadcast]
  ↓
ShipmentService.update() [Persist changes]
  ↓
Response with selected driver + store + logs
```

---

**Reference:** See WEEK2_AGENT_CORE_COMPLETE.md for full implementation details.
