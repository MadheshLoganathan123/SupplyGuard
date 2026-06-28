"""
Agents API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.database.session import get_db
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.schemas.reports import AgentPerformanceRead
from app.services.agent_service import AgentService
from app.services.reporting_service import ReportingService
from app.services.reroute_job import run_reroute_job
from app.services.projection_service import run_projection_job
from app.services.intervention_service import process_intervention

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# General Orchestration Endpoint (Manual Operator Trigger)
# ─────────────────────────────────────────────────────────────────────────────

class OrchestrateRequest(BaseModel):
    """General orchestration request from operator/UI."""
    action_type: str = "reroute"  # reroute, allocation, negotiation
    sector: Optional[str] = "GLOBAL"
    threat_level: Optional[str] = "NORMAL"
    incident_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/orchestrate", response_model=Dict[str, Any])
async def trigger_orchestration(
    payload: OrchestrateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger general agent orchestration from operator (e.g., UI reroute button).
    
    Supports:
    - Global sector reroute
    - Specific sector reroute
    - Emergency negotiations
    
    Returns:
    - action_type: Type of action performed
    - affected_sectors: Sectors impacted
    - efficiency_improvement: Estimated efficiency gain
    - shipments_updated: Number of shipments affected
    """
    try:
        orchestrator = AgentOrchestrator(db)
        
        if payload.action_type == "reroute":
            if payload.sector == "GLOBAL" or payload.sector is None:
                # Global reroute - process all sectors
                result = await orchestrator.run_for_sector(
                    sector="*",  # Global marker
                    threat_level=payload.threat_level or "NORMAL",
                    incident_ids=payload.incident_ids or [],
                )
            else:
                # Specific sector reroute
                result = await orchestrator.run_for_sector(
                    sector=payload.sector,
                    threat_level=payload.threat_level or "NORMAL",
                    incident_ids=payload.incident_ids or [],
                )
            
            await db.commit()
            
            results = result.get("results", [])
            successful = sum(1 for r in results if "error" not in r)
            
            return {
                "action_type": "reroute",
                "status": "success",
                "affected_sectors": [payload.sector] if payload.sector != "GLOBAL" else ["Sector 7", "Sector 12", "Sector 14"],
                "shipments_updated": successful,
                "efficiency_improvement": 18.5,  # Placeholder; in production, calculate from results
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "action_type": payload.action_type,
                "status": "not_implemented",
                "message": f"Action type '{payload.action_type}' not yet implemented",
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration error: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Agent CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AgentRead])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    svc = AgentService(db)
    if active_only:
        return await svc.get_active()
    return await svc.get_all(skip=skip, limit=limit)


@router.get("/{agent_id}/performance", response_model=AgentPerformanceRead)
async def get_agent_performance(agent_id: str, db: AsyncSession = Depends(get_db)):
    perf = await ReportingService(db).get_agent_performance(agent_id)
    if not perf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return perf


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    svc = AgentService(db)
    agent = await svc.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    return await AgentService(db).create(payload)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str, payload: AgentUpdate, db: AsyncSession = Depends(get_db)
):
    svc = AgentService(db)
    agent = await svc.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await svc.update(agent, payload)


# ─────────────────────────────────────────────────────────────────────────────
# Agent Orchestration Endpoints (Week 2+)
# ─────────────────────────────────────────────────────────────────────────────

class RerouteRequest(BaseModel):
    """Request to reroute a single shipment."""
    shipment_id: str
    incident_ids: Optional[List[str]] = None


class SectorRerouteRequest(BaseModel):
    """Request to reroute all shipments in a sector."""
    sector: str
    threat_level: str = "NORMAL"
    incident_ids: Optional[List[str]] = None


class ProjectionRequest(BaseModel):
    """Request to run a demand projection."""
    projection_id: str
    use_agent_orchestrator: bool = True


class InterventionRequest(BaseModel):
    """Request to process an operator intervention."""
    intervention_id: str


@router.post("/orchestrate/reroute", response_model=Dict[str, Any])
async def orchestrate_shipment_reroute(
    payload: RerouteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the full agent orchestration cycle for a single shipment reroute.
    
    Returns:
    - shipment: Updated shipment with new status
    - action_taken: Type of action (REROUTE, MONITOR, etc.)
    - confidence: Agent confidence in the decision
    - logs_created: Number of agent logs created
    - selected_driver: Driver assigned for reroute (if any)
    - selected_store: Store assigned for reroute (if any)
    """
    try:
        orchestrator = AgentOrchestrator(db)
        result = await orchestrator.run_for_shipment(
            shipment_id=payload.shipment_id,
            incident_ids=payload.incident_ids or [],
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        await db.commit()
        
        shipment = result.get("shipment")
        actions = result.get("actions", [])
        primary_action = actions[0] if actions else None
        
        return {
            "shipment_id": shipment.id,
            "shipment_code": shipment.shipment_code,
            "status": shipment.status.value,
            "action_taken": primary_action.action_type if primary_action else "MONITOR",
            "confidence": primary_action.confidence if primary_action else 0.0,
            "logs_created": len(result.get("logs", [])),
            "selected_driver": primary_action.payload.get("selected_driver") if primary_action else None,
            "selected_store": primary_action.payload.get("selected_store") if primary_action else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration error: {str(e)}"
        )


@router.post("/orchestrate/sector", response_model=Dict[str, Any])
async def orchestrate_sector_reroute(
    payload: SectorRerouteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run agent orchestration for all shipments in a sector.
    
    Returns:
    - sector: Sector processed
    - threat_level: Threat level used
    - shipments_processed: Total shipments processed
    - successful: Successful reroutes
    - logs_created: Total agent logs created
    """
    try:
        orchestrator = AgentOrchestrator(db)
        result = await orchestrator.run_for_sector(
            sector=payload.sector,
            threat_level=payload.threat_level,
            incident_ids=payload.incident_ids or [],
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        await db.commit()
        
        results = result.get("results", [])
        successful = sum(1 for r in results if "error" not in r)
        
        return {
            "sector": result.get("sector"),
            "threat_level": result.get("threat_level"),
            "shipments_processed": len(results),
            "successful": successful,
            "failed": len(results) - successful,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration error: {str(e)}"
        )


@router.post("/jobs/reroute", response_model=Dict[str, Any])
async def submit_reroute_job(payload: RerouteRequest):
    """
    Submit an async reroute job (background processing).
    
    In production, this would queue the job in Celery/Redis.
    For now, returns immediate result.
    """
    try:
        result = await run_reroute_job(
            shipment_id=payload.shipment_id,
            incident_ids=payload.incident_ids,
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reroute job error: {str(e)}"
        )


@router.post("/jobs/projection", response_model=Dict[str, Any])
async def submit_projection_job(payload: ProjectionRequest):
    """
    Submit a demand projection job with optional agent orchestration.
    
    Returns:
    - projection_id: Projection ID
    - status: Job status (complete, error)
    - result: Projection results (supply/demand gap, adjustments, etc.)
    """
    try:
        result = await run_projection_job(
            projection_id=payload.projection_id,
            use_agent_orchestrator=payload.use_agent_orchestrator,
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Projection job error: {str(e)}"
        )


@router.post("/jobs/intervention", response_model=Dict[str, Any])
async def submit_intervention_job(payload: InterventionRequest):
    """
    Process an operator intervention through the agent system.
    
    Returns:
    - intervention_id: Intervention ID
    - status: Resolution status (resolved, escalated, error)
    - intervention_type: Classified intervention type
    - agent_responses: Responses from agents invoked
    """
    try:
        result = await process_intervention(intervention_id=payload.intervention_id)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intervention job error: {str(e)}"
        )
