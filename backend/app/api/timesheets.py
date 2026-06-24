from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from pydantic import BaseModel

from src.core.database import get_db
from models.timesheet import Timesheet, LeaveRecord
from models.employee import Employee
from models.project import Project

router = APIRouter(prefix="/timesheets", tags=["Timesheets"])

# --- Mock Email Service ---
def send_mock_email(to_email: str, subject: str, body: str):
    print(f"\n[EMAIL SENT to {to_email}]")
    print(f"Subject: {subject}")
    print(f"Body: {body}\n")

# --- Pydantic Schemas ---
class TimesheetSubmitRequest(BaseModel):
    employee_id: int
    project_id: int
    work_date: date
    hours_logged: float
    activity_type: Optional[str] = None
    note: Optional[str] = None
    status: str = "Submitted"

class BulkTimesheetSubmitRequest(BaseModel):
    employee_id: int
    entries: List[Dict[str, Any]]  # list of {project_id, work_date, hours_logged, activity_type, note}

class LeaveSubmitRequest(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None

class ApprovalRequest(BaseModel):
    status: str  # "Approved" or "Rejected"
    comment: Optional[str] = None

# --- Helper ---
def _ts_to_dict(ts: Timesheet, project_name: str = None) -> Dict:
    return {
        "timesheet_id": ts.timesheet_id,
        "employee_id": ts.employee_id,
        "project_id": ts.project_id,
        "project_name": project_name or f"Project #{ts.project_id}",
        "work_date": str(ts.work_date),
        "hours_logged": ts.hours_logged,
        "activity_type": ts.activity_type,
        "note": ts.note,
        "submission_status": ts.submission_status,
        "approval_status": ts.approval_status,
        "created_at": ts.created_at.isoformat() if ts.created_at else None,
    }

def _lv_to_dict(lv: LeaveRecord) -> Dict:
    delta = (lv.end_date - lv.start_date).days + 1
    return {
        "leave_id": lv.leave_id,
        "employee_id": lv.employee_id,
        "leave_type": lv.leave_type,
        "start_date": str(lv.start_date),
        "end_date": str(lv.end_date),
        "days": delta,
        "approval_status": lv.approval_status,
        "created_at": lv.created_at.isoformat() if lv.created_at else None,
    }

# ===========================================================================
# TIMESHEET ENDPOINTS
# ===========================================================================

@router.post("/")
async def submit_timesheet(req: TimesheetSubmitRequest, db: AsyncSession = Depends(get_db)):
    timesheet = Timesheet(
        employee_id=req.employee_id,
        project_id=req.project_id,
        work_date=req.work_date,
        hours_logged=req.hours_logged,
        activity_type=req.activity_type,
        note=req.note,
        submission_status=req.status,
        approval_status="Pending"
    )
    db.add(timesheet)

    emp_stmt = select(Employee).where(Employee.employee_id == req.employee_id)
    emp_res = await db.execute(emp_stmt)
    emp = emp_res.scalar_one_or_none()

    if emp and emp.manager_id:
        mgr_stmt = select(Employee).where(Employee.employee_id == emp.manager_id)
        mgr_res = await db.execute(mgr_stmt)
        manager = mgr_res.scalar_one_or_none()
        if manager:
            send_mock_email(
                manager.email,
                f"Pending Timesheet Approval: {emp.employee_name}",
                f"Employee {emp.employee_name} has submitted a timesheet for {req.hours_logged} hours on {req.work_date}."
            )

    await db.commit()
    return {"message": "Timesheet submitted successfully", "id": timesheet.timesheet_id}


@router.post("/bulk")
async def bulk_submit_timesheets(req: BulkTimesheetSubmitRequest, db: AsyncSession = Depends(get_db)):
    """Submit multiple timesheet entries at once for a week."""
    created_ids = []
    for entry in req.entries:
        ts = Timesheet(
            employee_id=req.employee_id,
            project_id=entry.get("project_id", 1),
            work_date=entry.get("work_date"),
            hours_logged=float(entry.get("hours_logged", 0)),
            activity_type=entry.get("activity_type"),
            note=entry.get("note"),
            submission_status="Submitted",
            approval_status="Pending"
        )
        db.add(ts)
        created_ids.append(ts)

    await db.flush()
    ids = [ts.timesheet_id for ts in created_ids]

    emp_stmt = select(Employee).where(Employee.employee_id == req.employee_id)
    emp_res = await db.execute(emp_stmt)
    emp = emp_res.scalar_one_or_none()

    if emp and emp.manager_id:
        mgr_stmt = select(Employee).where(Employee.employee_id == emp.manager_id)
        mgr_res = await db.execute(mgr_stmt)
        manager = mgr_res.scalar_one_or_none()
        if manager:
            send_mock_email(
                manager.email,
                f"Weekly Timesheet Submitted: {emp.employee_name}",
                f"Employee {emp.employee_name} submitted {len(req.entries)} timesheet entries for approval."
            )

    await db.commit()
    return {"message": f"{len(req.entries)} entries submitted successfully", "ids": ids}


@router.get("/employee/{employee_id}")
async def get_employee_timesheets(
    employee_id: int,
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get timesheets for an employee with optional filters."""
    conditions = [Timesheet.employee_id == employee_id]
    if status:
        conditions.append(Timesheet.approval_status == status)
    if from_date:
        conditions.append(Timesheet.work_date >= from_date)
    if to_date:
        conditions.append(Timesheet.work_date <= to_date)

    stmt = select(Timesheet).where(and_(*conditions)).order_by(Timesheet.work_date.desc())
    res = await db.execute(stmt)
    timesheets = res.scalars().all()

    # Fetch project names
    project_ids = list({ts.project_id for ts in timesheets})
    proj_stmt = select(Project).where(Project.project_id.in_(project_ids))
    proj_res = await db.execute(proj_stmt)
    projects = {p.project_id: p.project_name for p in proj_res.scalars().all()}

    return [_ts_to_dict(ts, projects.get(ts.project_id)) for ts in timesheets]


@router.get("/employee/{employee_id}/stats")
async def get_employee_timesheet_stats(employee_id: int, db: AsyncSession = Depends(get_db)):
    """Get summary statistics for an employee's timesheets."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Total this week
    week_res = await db.execute(
        select(func.sum(Timesheet.hours_logged)).where(
            and_(Timesheet.employee_id == employee_id, Timesheet.work_date >= week_start)
        )
    )
    week_hours = week_res.scalar() or 0.0

    # Total this month
    month_res = await db.execute(
        select(func.sum(Timesheet.hours_logged)).where(
            and_(Timesheet.employee_id == employee_id, Timesheet.work_date >= month_start)
        )
    )
    month_hours = month_res.scalar() or 0.0

    # Pending approvals
    pending_res = await db.execute(
        select(func.count(Timesheet.timesheet_id)).where(
            and_(Timesheet.employee_id == employee_id, Timesheet.approval_status == "Pending")
        )
    )
    pending_count = pending_res.scalar() or 0

    # Approved entries
    approved_res = await db.execute(
        select(func.count(Timesheet.timesheet_id)).where(
            and_(Timesheet.employee_id == employee_id, Timesheet.approval_status == "Approved")
        )
    )
    approved_count = approved_res.scalar() or 0

    # Rejected entries
    rejected_res = await db.execute(
        select(func.count(Timesheet.timesheet_id)).where(
            and_(Timesheet.employee_id == employee_id, Timesheet.approval_status == "Rejected")
        )
    )
    rejected_count = rejected_res.scalar() or 0

    # Hours by project (last 30 days)
    proj_hours_res = await db.execute(
        select(Timesheet.project_id, func.sum(Timesheet.hours_logged)).where(
            and_(Timesheet.employee_id == employee_id, Timesheet.work_date >= month_start)
        ).group_by(Timesheet.project_id)
    )
    proj_hours_raw = proj_hours_res.all()

    project_ids = [row[0] for row in proj_hours_raw]
    proj_stmt = select(Project).where(Project.project_id.in_(project_ids))
    proj_res = await db.execute(proj_stmt)
    projects = {p.project_id: p.project_name for p in proj_res.scalars().all()}

    hours_by_project = [
        {"project_id": row[0], "project_name": projects.get(row[0], f"Project #{row[0]}"), "hours": float(row[1])}
        for row in proj_hours_raw
    ]

    # Daily breakdown for last 7 days
    daily_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_res = await db.execute(
            select(func.sum(Timesheet.hours_logged)).where(
                and_(Timesheet.employee_id == employee_id, Timesheet.work_date == d)
            )
        )
        daily_data.append({"date": str(d), "hours": float(day_res.scalar() or 0)})

    return {
        "week_hours": round(week_hours, 1),
        "month_hours": round(month_hours, 1),
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "hours_by_project": hours_by_project,
        "daily_breakdown": daily_data,
        "target_week_hours": 40.0,
        "compliance_rate": round(min(week_hours / 40.0 * 100, 100), 1),
    }


@router.get("/projects/list")
async def get_projects_list(db: AsyncSession = Depends(get_db)):
    """Get list of active projects for timesheet dropdown."""
    stmt = select(Project).where(Project.status.in_(["Active", "At Risk"]))
    res = await db.execute(stmt)
    projects = res.scalars().all()
    return [
        {"project_id": p.project_id, "project_name": p.project_name, "status": p.status}
        for p in projects
    ]


# ===========================================================================
# LEAVE ENDPOINTS
# ===========================================================================

@router.post("/leaves")
async def submit_leave(req: LeaveSubmitRequest, db: AsyncSession = Depends(get_db)):
    # Check for overlapping leaves
    overlap_stmt = select(LeaveRecord).where(
        and_(
            LeaveRecord.employee_id == req.employee_id,
            LeaveRecord.approval_status != "Rejected",
            LeaveRecord.start_date <= req.end_date,
            LeaveRecord.end_date >= req.start_date
        )
    )
    overlap_res = await db.execute(overlap_stmt)
    if overlap_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Overlapping leave request exists for this period.")

    leave = LeaveRecord(
        employee_id=req.employee_id,
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        approval_status="Pending"
    )
    db.add(leave)

    emp_stmt = select(Employee).where(Employee.employee_id == req.employee_id)
    emp_res = await db.execute(emp_stmt)
    emp = emp_res.scalar_one_or_none()

    if emp and emp.manager_id:
        mgr_stmt = select(Employee).where(Employee.employee_id == emp.manager_id)
        mgr_res = await db.execute(mgr_stmt)
        manager = mgr_res.scalar_one_or_none()
        if manager:
            send_mock_email(
                manager.email,
                f"Leave Request: {emp.employee_name}",
                f"Employee {emp.employee_name} has requested {req.leave_type} leave from {req.start_date} to {req.end_date}.\nReason: {req.reason or 'Not provided'}"
            )

    await db.commit()
    return {"message": "Leave submitted successfully", "id": leave.leave_id}


@router.get("/leaves/employee/{employee_id}")
async def get_employee_leaves(employee_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(LeaveRecord).where(LeaveRecord.employee_id == employee_id).order_by(LeaveRecord.start_date.desc())
    res = await db.execute(stmt)
    leaves = res.scalars().all()
    return [_lv_to_dict(lv) for lv in leaves]


@router.get("/leaves/employee/{employee_id}/balance")
async def get_leave_balance(employee_id: int, db: AsyncSession = Depends(get_db)):
    """Compute annual leave balance summary."""
    year_start = date.today().replace(month=1, day=1)
    stmt = select(LeaveRecord).where(
        and_(
            LeaveRecord.employee_id == employee_id,
            LeaveRecord.start_date >= year_start,
            LeaveRecord.approval_status.in_(["Approved", "Pending"])
        )
    )
    res = await db.execute(stmt)
    leaves = res.scalars().all()

    used = {"Sick": 0, "Vacation": 0, "Personal": 0, "Casual": 0, "Compensatory": 0}
    pending = {"Sick": 0, "Vacation": 0, "Personal": 0, "Casual": 0, "Compensatory": 0}

    for lv in leaves:
        days = (lv.end_date - lv.start_date).days + 1
        lt = lv.leave_type if lv.leave_type in used else "Personal"
        if lv.approval_status == "Approved":
            used[lt] = used.get(lt, 0) + days
        else:
            pending[lt] = pending.get(lt, 0) + days

    annual_allowances = {"Sick": 12, "Vacation": 15, "Personal": 6, "Casual": 10, "Compensatory": 5}

    balance = []
    for lt, allowance in annual_allowances.items():
        taken = used.get(lt, 0)
        pend = pending.get(lt, 0)
        remaining = allowance - taken - pend
        balance.append({
            "leave_type": lt,
            "annual_allowance": allowance,
            "used": taken,
            "pending": pend,
            "remaining": max(remaining, 0),
            "percentage_used": round(min(taken / allowance * 100, 100), 1)
        })

    return {"balance": balance, "year": date.today().year}


# ===========================================================================
# MANAGER / ADMIN ENDPOINTS
# ===========================================================================

@router.get("/pending/{manager_id}")
async def get_pending_approvals(manager_id: int, db: AsyncSession = Depends(get_db)):
    emp_stmt = select(Employee).where(Employee.manager_id == manager_id)
    emp_res = await db.execute(emp_stmt)
    subordinates = emp_res.scalars().all()
    sub_ids = [e.employee_id for e in subordinates]

    if not sub_ids:
        return {"timesheets": [], "leaves": []}

    ts_stmt = select(Timesheet).where(
        and_(Timesheet.employee_id.in_(sub_ids), Timesheet.approval_status == "Pending")
    ).order_by(Timesheet.work_date.desc())
    ts_res = await db.execute(ts_stmt)
    pending_ts = ts_res.scalars().all()

    project_ids = list({ts.project_id for ts in pending_ts})
    proj_res = await db.execute(select(Project).where(Project.project_id.in_(project_ids)))
    projects = {p.project_id: p.project_name for p in proj_res.scalars().all()}

    emp_map = {e.employee_id: e.employee_name for e in subordinates}

    ts_dicts = []
    for ts in pending_ts:
        d = _ts_to_dict(ts, projects.get(ts.project_id))
        d["employee_name"] = emp_map.get(ts.employee_id, f"Emp #{ts.employee_id}")
        ts_dicts.append(d)

    lv_stmt = select(LeaveRecord).where(
        and_(LeaveRecord.employee_id.in_(sub_ids), LeaveRecord.approval_status == "Pending")
    ).order_by(LeaveRecord.start_date.desc())
    lv_res = await db.execute(lv_stmt)
    pending_lv = lv_res.scalars().all()

    lv_dicts = []
    for lv in pending_lv:
        d = _lv_to_dict(lv)
        d["employee_name"] = emp_map.get(lv.employee_id, f"Emp #{lv.employee_id}")
        lv_dicts.append(d)

    return {"timesheets": ts_dicts, "leaves": lv_dicts}


@router.put("/{timesheet_id}/approve")
async def approve_timesheet(timesheet_id: int, req: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(Timesheet).where(Timesheet.timesheet_id == timesheet_id)
    res = await db.execute(stmt)
    timesheet = res.scalar_one_or_none()
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    timesheet.approval_status = req.status
    await db.commit()

    emp_stmt = select(Employee).where(Employee.employee_id == timesheet.employee_id)
    emp_res = await db.execute(emp_stmt)
    emp = emp_res.scalar_one_or_none()
    if emp:
        send_mock_email(
            emp.email,
            f"Timesheet {req.status}",
            f"Your timesheet for {timesheet.work_date} has been {req.status}."
            + (f"\nManager comment: {req.comment}" if req.comment else "")
        )

    return {"message": f"Timesheet {req.status.lower()}"}


@router.put("/leaves/{leave_id}/approve")
async def approve_leave(leave_id: int, req: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(LeaveRecord).where(LeaveRecord.leave_id == leave_id)
    res = await db.execute(stmt)
    leave = res.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave record not found")

    leave.approval_status = req.status
    await db.commit()

    emp_stmt = select(Employee).where(Employee.employee_id == leave.employee_id)
    emp_res = await db.execute(emp_stmt)
    emp = emp_res.scalar_one_or_none()
    if emp:
        send_mock_email(
            emp.email,
            f"Leave Request {req.status}",
            f"Your {leave.leave_type} leave from {leave.start_date} to {leave.end_date} has been {req.status}."
            + (f"\nComment: {req.comment}" if req.comment else "")
        )

    return {"message": f"Leave {req.status.lower()}"}


@router.delete("/{timesheet_id}")
async def delete_timesheet(timesheet_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a draft or rejected timesheet entry."""
    stmt = select(Timesheet).where(Timesheet.timesheet_id == timesheet_id)
    res = await db.execute(stmt)
    ts = res.scalar_one_or_none()
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    if ts.approval_status == "Approved":
        raise HTTPException(status_code=400, detail="Cannot delete an approved timesheet.")
    await db.delete(ts)
    await db.commit()
    return {"message": "Timesheet deleted successfully"}
