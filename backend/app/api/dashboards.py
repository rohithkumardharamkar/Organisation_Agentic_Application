from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from sqlalchemy.future import select
from models.employee import Employee
from models.project import Project, ResourceAllocation
from models.timesheet import Timesheet, LeaveRecord
from models.process import ProcessReport

from src.core.database import get_db
from services.prediction_engine import PredictionEngine

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])

@router.get("/executive")
async def get_executive_dashboard(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    from src.tools.workforce_tools import (
        organization_health,
        generate_executive_actions,
        skill_intelligence_tool,
        hiring_forecast,
        project_health_tool,
        predict_project_risk,
        bench_optimization,
        resource_utilization_tool
    )
    
    # 1. Fetch organizational health (utilization, compliance, delivery health)
    health_data = await organization_health(db)
    
    # 2. Total and Active employees
    emp_all_stmt = select(Employee)
    res_all = await db.execute(emp_all_stmt)
    all_emps = res_all.scalars().all()
    total_employees = len(all_emps)
    active_employees = sum(1 for e in all_emps if e.employment_status == "Active")
    
    # 3. Utilization & Bench
    utilization_pct = health_data.get("resource_utilization_index", 80.0)
    bench_data = await bench_optimization(db)
    bench_size = bench_data.get("bench_size", 0)
    bench_pct = round((bench_size / active_employees * 100), 1) if active_employees > 0 else 0.0
    
    # 4. Project Health and Risky Projects
    proj_tool_res = await project_health_tool(db)
    proj_data = proj_tool_res.get("data", {})
    projects = proj_data.get("projects", [])
    total_projects = len(projects)
    
    risky_projects_count = 0
    top_risks = []
    for p in projects:
        risk_res = await predict_project_risk(db, p["project_id"])
        risk_score = risk_res.get("risk_score", 0)
        if risk_score > 50:
            risky_projects_count += 1
            top_risks.append(f"Project '{p['project_name']}' is at High Risk ({risk_score}%) due to delay indicators.")
            
    if not top_risks:
        top_risks = ["No high-risk project threats detected currently."]
        
    delivery_health = health_data.get("delivery_health_index", 100.0)
    project_health_pct = delivery_health
    
    # 5. Resource Demand and Hiring Demand
    # Open allocations or projects under-resourced
    resource_demand_count = sum(1 for p in projects if p.get("resource_count", 0) < 2)
    
    hiring_data = await hiring_forecast(db)
    hiring_reqs = hiring_data.get("hiring_requisitions", [])
    hiring_demand_count = sum(r.get("count", 0) for r in hiring_reqs)
    
    # 6. Skill Gaps and Critical shortages
    skill_data = await skill_intelligence_tool(db)
    skill_gaps_count = len(skill_data.get("data", {}).get("critical_skills", []))
    critical_skills = [s.get("skill") for s in skill_data.get("data", {}).get("critical_skills", [])]
    
    # 7. AI Insights: Actions, Hiring needs, Resource issues
    actions_res = await generate_executive_actions(db)
    executive_actions = actions_res.get("actions", [])
    
    hiring_needs = [f"Recruit {r.get('count')} {r.get('role_req')} within {r.get('timeline')} ({r.get('priority')} priority)" for r in hiring_reqs]
    
    bench_names = [b.get("name") for b in bench_data.get("bench_resources", [])]
    resource_issues = []
    if bench_names:
        resource_issues.append(f"Unallocated (Bench) Talent: {', '.join(bench_names)}.")
    
    # Check over-allocated employees
    util_details = await resource_utilization_tool(db)
    over_allocated = util_details.get("data", {}).get("over_allocated_employees", [])
    if over_allocated:
        resource_issues.append(f"Over-allocated resources (>100% capacity): {', '.join([o['name'] for o in over_allocated])}.")
    if not resource_issues:
        resource_issues = ["Resource allocations are balanced across the active delivery lifecycle."]
        
    return {
        "metrics": {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "utilization_percentage": utilization_pct,
            "bench_percentage": bench_pct,
            "project_health": project_health_pct,
            "resource_demand": resource_demand_count,
            "hiring_demand": hiring_demand_count,
            "skill_gaps": skill_gaps_count,
            "risky_projects": risky_projects_count,
            "delivery_health": delivery_health
        },
        "ai_insights": {
            "top_risks": top_risks,
            "recommended_actions": [a.get("action") for a in executive_actions],
            "hiring_needs": hiring_needs,
            "resource_issues": resource_issues,
            "skill_shortages": [f"Critical single-point skills missing scale: {', '.join(critical_skills)}"] if critical_skills else ["No critical skill shortages identified."]
        },
        # Maintain legacy keys to prevent breaking existing dashboard code
        "organizational_health_score": health_data.get("overall_health_score", 85),
        "delivery_risk_score": round(100.0 - health_data.get("delivery_health_index", 100.0), 1),
        "workforce_efficiency_score": health_data.get("resource_utilization_index", 92),
        "active_risks": top_risks,
        "utilization_trends": {"current_utilization": utilization_pct},
        "executive_actions": executive_actions
    }

@router.get("/workforce")
async def get_workforce_dashboard(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    return {
        "utilization_heatmap": {"Engineering": 85, "Sales": 90, "Marketing": 70},
        "available_resources": 15,
        "bench_resources": 5,
        "overallocated_employees": 3
    }

@router.get("/projects")
async def get_projects_dashboard(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    engine = PredictionEngine(db)
    delays = await engine.predict_project_delays()
    return {
        "project_health_score": 88,
        "delay_risks": delays,
        "resource_coverage": "95%",
        "delivery_forecast": "On Track"
    }

@router.get("/talent")
async def get_talent_dashboard(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    engine = PredictionEngine(db)
    shortages = await engine.predict_resource_shortages()
    return {
        "skills_inventory": {"Python": 50, "React": 30, "AWS": 20},
        "skill_gaps": shortages,
        "hiring_recommendations": "Hire 3 Python Devs",
        "future_demand_forecast": "High demand for AI Engineers"
    }

@router.get("/role/{role}")
async def get_role_dashboard(role: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    if role == "Employee":
        # Timesheets pending
        stmt = select(Timesheet).where(Timesheet.approval_status == "Pending")
        res = await db.execute(stmt)
        pending_timesheets = len(res.scalars().all())
        return {
            "role": role,
            "metrics": [
                {"label": "Pending Timesheets", "value": pending_timesheets},
                {"label": "Recent Notifications", "value": 2},
                {"label": "Upcoming Project Deadlines", "value": 1}
            ]
        }
    elif role == "Process Engineer":
        stmt = select(ProcessReport)
        res = await db.execute(stmt)
        reports = len(res.scalars().all())
        return {
            "role": role,
            "metrics": [
                {"label": "Total Sprint Reports", "value": reports},
                {"label": "Active Risks Identified", "value": 3},
                {"label": "Missing Requirements", "value": 1}
            ]
        }
    elif role == "Reporting Manager":
        stmt = select(Timesheet).where(Timesheet.approval_status == "Pending")
        res = await db.execute(stmt)
        pending_ts = len(res.scalars().all())
        
        stmt_lv = select(LeaveRecord).where(LeaveRecord.approval_status == "Pending")
        res_lv = await db.execute(stmt_lv)
        pending_lv = len(res_lv.scalars().all())
        
        return {
            "role": role,
            "metrics": [
                {"label": "Pending Timesheet Approvals", "value": pending_ts},
                {"label": "Pending Leave Requests", "value": pending_lv},
                {"label": "Underperforming Projects", "value": 1}
            ]
        }
    elif role == "HR":
        stmt = select(Employee).where(Employee.employment_status == "Active")
        res = await db.execute(stmt)
        active_emps = len(res.scalars().all())
        
        return {
            "role": role,
            "metrics": [
                {"label": "Total Active Employees", "value": active_emps},
                {"label": "Skill Gaps Identified", "value": 2},
                {"label": "Open Requisitions", "value": 3}
            ]
        }
    else:
        return {"role": role, "metrics": []}
