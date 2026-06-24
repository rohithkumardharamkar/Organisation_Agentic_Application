import pytest
import asyncio
from src.core.database import Base, engine, SessionLocal
from src.core.seed import seed_data
from sqlalchemy import select
from models.employee import Employee
from src.tools.workforce_tools import (
    get_employee_profile,
    get_leave_balance,
    apply_leave,
    get_attendance_summary,
    submit_timesheet,
    get_timesheet_status,
    get_salary_slip,
    search_policy,
    create_ticket,
    get_ticket_status,
    get_job_openings,
    apply_for_job,
    send_notification,
    save_memory,
    retrieve_memory
)

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module", autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def get_any_employee(db):
    stmt = select(Employee).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

@pytest.mark.asyncio
async def test_get_employee_profile():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        assert emp is not None
        
        # Test valid name resolution
        res = await get_employee_profile(db, emp.employee_name)
        assert res["status"] == "success"
        assert res["data"]["name"] == emp.employee_name
        assert "department" in res["data"]
        
        # Test invalid name
        res_fail = await get_employee_profile(db, "Nonexistent Employee")
        assert res_fail["status"] == "error"

@pytest.mark.asyncio
async def test_get_leave_balance():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        res = await get_leave_balance(db, emp.employee_name)
        assert res["status"] == "success"
        assert len(res["leave_balances"]) > 0
        assert "leave_type" in res["leave_balances"][0]

@pytest.mark.asyncio
async def test_apply_leave():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        res = await apply_leave(
            db, 
            employee_id_or_name=emp.employee_name, 
            leave_type="Sick", 
            start_date="2026-07-01", 
            end_date="2026-07-03", 
            reason="Medical recovery"
        )
        assert res["status"] == "success"
        assert "submitted successfully" in res["message"]

@pytest.mark.asyncio
async def test_get_attendance_summary():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        res = await get_attendance_summary(db, emp.employee_name)
        assert res["status"] == "success"
        assert "summary" in res

@pytest.mark.asyncio
async def test_submit_timesheet_and_status():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        res_sub = await submit_timesheet(
            db,
            employee_id_or_name=emp.employee_name,
            project_id=1,
            work_date="2026-06-20",
            hours_logged=8.0,
            activity_type="Development",
            note="Worked on authentication feature"
        )
        assert res_sub["status"] == "success"
        assert "timesheet_id" in res_sub
        
        res_status = await get_timesheet_status(db, emp.employee_name)
        assert res_status["status"] == "success"
        assert res_status["total_recent_entries"] > 0

@pytest.mark.asyncio
async def test_get_salary_slip():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        # According to seed data, we have payroll records seeded for 3 months
        # Let's check month=5, year=2026
        res = await get_salary_slip(db, emp.employee_name, month=5, year=2026)
        assert res["status"] == "success"
        assert "basic_salary" in res["data"]

@pytest.mark.asyncio
async def test_search_policy():
    async with SessionLocal() as db:
        res = await search_policy(db, "Leave")
        assert res["status"] == "success"
        assert res["results_found"] > 0

@pytest.mark.asyncio
async def test_create_and_get_ticket():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        res_create = await create_ticket(
            db,
            employee_id_or_name=emp.employee_name,
            category="IT Support",
            subject="Monitor flicker",
            description="My secondary monitor keeps flickering.",
            priority="Medium"
        )
        assert res_create["status"] == "success"
        ticket_id = res_create["ticket_id"]
        
        res_get = await get_ticket_status(db, ticket_id)
        assert res_get["status"] == "success"
        assert res_get["data"]["subject"] == "Monitor flicker"

@pytest.mark.asyncio
async def test_job_openings_and_apply():
    async with SessionLocal() as db:
        res_jobs = await get_job_openings(db)
        assert res_jobs["status"] == "success"
        assert res_jobs["total_openings"] > 0
        job_id = res_jobs["job_openings"][0]["job_id"]
        
        res_apply = await apply_for_job(
            db,
            job_id=job_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        assert res_apply["status"] == "success"
        assert "Application submitted successfully" in res_apply["message"]

@pytest.mark.asyncio
async def test_send_notification():
    async with SessionLocal() as db:
        emp = await get_any_employee(db)
        res = await send_notification(db, emp.employee_name, "Hello, this is a test notification.")
        assert res["status"] == "success"

@pytest.mark.asyncio
async def test_memory_tools():
    async with SessionLocal() as db:
        res_save = await save_memory(db, "test_user_123", "User likes to work from remote on Fridays.")
        assert res_save["status"] == "success"
        
        res_ret = await retrieve_memory(db, "test_user_123")
        assert res_ret["status"] == "success"
        assert res_ret["total_memories"] > 0
        assert res_ret["memories"][0]["memory"] == "User likes to work from remote on Fridays."
