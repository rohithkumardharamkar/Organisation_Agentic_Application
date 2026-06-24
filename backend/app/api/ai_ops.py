from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List

from src.core.database import get_db
from src.models.db_models import PendingApproval, AuditLog
from services.langgraph_service import LanggraphService

router = APIRouter(prefix="/ai-ops", tags=["AI Operations"])

@router.get("/activities")
async def get_agent_activities(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    # Fetch real audit logs from the database
    try:
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(30)
        res = await db.execute(stmt)
        logs = res.scalars().all()
        
        if not logs:
            # Fallback simulated logs if DB is empty
            return [
                {"agent": "Resource Optimization Agent", "action": "Detected 5 underutilized resources", "timestamp": "2026-06-21T10:00:00Z"},
                {"agent": "Project Health Agent", "action": "Predicted delay for Project Beta", "timestamp": "2026-06-21T10:15:00Z"}
            ]
            
        return [
            {
                "agent": l.agent,
                "action": f"{l.action}: {l.details}",
                "timestamp": l.timestamp.isoformat() if l.timestamp else "N/A"
            }
            for l in logs
        ]
    except Exception as e:
        print(f"Error fetching activities: {e}")
        return []

@router.get("/approvals")
async def get_pending_approvals(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    # Fetch real pending/completed approvals from DB
    try:
        stmt = select(PendingApproval).order_by(PendingApproval.created_at.desc())
        res = await db.execute(stmt)
        apps = res.scalars().all()
        
        if not apps:
            return [
                {"id": "1", "thread_id": "simulated_thread", "action": "Resource Allocation", "description": "Reallocate John Doe to Project Beta", "risk_level": "Medium", "status": "Pending", "created_at": "2026-06-21T10:00:00Z"}
            ]
            
        return [
            {
                "id": str(a.id),
                "thread_id": a.thread_id,
                "action": a.action_type,
                "description": a.description,
                "risk_level": a.risk_level,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else "N/A"
            }
            for a in apps
        ]
    except Exception as e:
        print(f"Error fetching approvals: {e}")
        return []

@router.post("/approvals/{approval_id}/approve")
async def approve_action(approval_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # Resolve the pending approval row
    if not approval_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid approval ID format.")
        
    stmt = select(PendingApproval).where(PendingApproval.id == int(approval_id))
    res = await db.execute(stmt)
    pending = res.scalar_one_or_none()
    
    if not pending:
        raise HTTPException(status_code=404, detail="Approval request not found.")
        
    if pending.status != "Pending":
        return {"status": "error", "message": f"Approval request is already {pending.status}."}
        
    # Resume the LangGraph workflow
    try:
        service = LanggraphService(db)
        await service.approve_action(thread_id=pending.thread_id, approve=True, user_id="user_1")
        
        # Update row status
        pending.status = "Approved"
        await db.commit()
        return {"status": "success", "message": f"Approval {approval_id} granted and workflow resumed."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")

@router.post("/approvals/{approval_id}/reject")
async def reject_action(approval_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    if not approval_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid approval ID format.")
        
    stmt = select(PendingApproval).where(PendingApproval.id == int(approval_id))
    res = await db.execute(stmt)
    pending = res.scalar_one_or_none()
    
    if not pending:
        raise HTTPException(status_code=404, detail="Approval request not found.")
        
    if pending.status != "Pending":
        return {"status": "error", "message": f"Approval request is already {pending.status}."}
        
    # Resume the LangGraph workflow with rejection
    try:
        service = LanggraphService(db)
        await service.approve_action(thread_id=pending.thread_id, approve=False, user_id="user_1")
        
        # Update row status
        pending.status = "Rejected"
        await db.commit()
        return {"status": "success", "message": f"Approval {approval_id} rejected and workflow halted."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reject workflow: {str(e)}")


@router.get("/registry")
async def get_agent_registry() -> List[Dict[str, Any]]:
    from src.agents.registry import AGENT_REGISTRY
    return [agent.to_dict() for agent in AGENT_REGISTRY.values()]


@router.get("/metrics")
async def get_ops_metrics() -> Dict[str, Any]:
    from src.observability.langsmith import get_observability_metrics
    return get_observability_metrics()

