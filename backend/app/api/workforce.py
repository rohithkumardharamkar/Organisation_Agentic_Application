from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.core.database import get_db
from models.employee import Employee
from models.project import Project
from schemas.workforce import EmployeeResponse, ProjectResponse

router = APIRouter(prefix="/workforce", tags=["Workforce"])

@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(db: AsyncSession = Depends(get_db)):
    stmt = select(Employee)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(db: AsyncSession = Depends(get_db)):
    stmt = select(Project)
    result = await db.execute(stmt)
    return result.scalars().all()
