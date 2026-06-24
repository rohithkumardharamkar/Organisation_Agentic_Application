from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from src.core.database import get_db
from models.process import ProcessReport
from models.project import Project

router = APIRouter(prefix="/process", tags=["Process Engineering"])

class ProcessReportCreate(BaseModel):
    project_id: int
    employee_id: int
    report_date: date
    report_type: str # Daily, Weekly, Sprint, Monthly
    timeframe_label: str
    achievements: Optional[str] = None
    risks_identified: Optional[str] = None
    missing_requirements: Optional[str] = None
    future_improvements: Optional[str] = None

@router.post("/reports")
async def create_process_report(req: ProcessReportCreate, db: AsyncSession = Depends(get_db)):
    report = ProcessReport(
        project_id=req.project_id,
        employee_id=req.employee_id,
        report_date=req.report_date,
        report_type=req.report_type,
        timeframe_label=req.timeframe_label,
        achievements=req.achievements,
        risks_identified=req.risks_identified,
        missing_requirements=req.missing_requirements,
        future_improvements=req.future_improvements
    )
    db.add(report)
    await db.commit()
    return {"message": "Process report created successfully", "report_id": report.report_id}

@router.get("/reports/{project_id}")
async def get_project_reports(project_id: int, report_type: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(ProcessReport).where(ProcessReport.project_id == project_id)
    if report_type:
        stmt = stmt.where(ProcessReport.report_type == report_type)
    
    # Order by newest first
    stmt = stmt.order_by(ProcessReport.report_date.desc())
    
    res = await db.execute(stmt)
    reports = res.scalars().all()
    
    # Let's get project details
    proj_stmt = select(Project).where(Project.project_id == project_id)
    proj_res = await db.execute(proj_stmt)
    project = proj_res.scalar_one_or_none()
    
    project_name = project.project_name if project else "Unknown Project"
    
    return {
        "project_id": project_id,
        "project_name": project_name,
        "reports": reports
    }
