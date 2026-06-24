import pytest
import asyncio
import random
from httpx import ASGITransport, AsyncClient
from main import app
from src.core.database import Base, engine, SessionLocal
from src.core.seed import seed_data
from sqlalchemy import select
from models.user import User

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

async def get_test_user_token(ac: AsyncClient, role: str) -> str:
    email = f"user_{role.lower()}_{random.randint(1000, 9999)}@example.com"
    signup_payload = {
        "email": email,
        "password": "securepassword123",
        "name": f"Test {role} User",
        "role": role
    }
    signup_res = await ac.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 200, f"Signup failed: {signup_res.text}"
    
    login_data = {
        "username": email,
        "password": "securepassword123"
    }
    login_res = await ac.post("/api/v1/auth/login", data=login_data)
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    return login_res.json()["access_token"]

@pytest.mark.asyncio
async def test_executive_dashboard_access():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = await get_test_user_token(ac, "HR")
        headers = {"Authorization": f"Bearer {token}"}
        
        res = await ac.get("/api/v1/dashboards/executive", headers=headers)
        assert res.status_code == 200
        data = res.json()
        
        # Verify all 10 telemetry metrics exist
        assert "metrics" in data
        metrics = data["metrics"]
        assert "total_employees" in metrics
        assert "active_employees" in metrics
        assert "utilization_percentage" in metrics
        assert "bench_percentage" in metrics
        assert "project_health" in metrics
        assert "resource_demand" in metrics
        assert "hiring_demand" in metrics
        assert "skill_gaps" in metrics
        assert "risky_projects" in metrics
        assert "delivery_health" in metrics
        
        # Verify 5 AI Insights panels exist
        assert "ai_insights" in data
        ai_insights = data["ai_insights"]
        assert "top_risks" in ai_insights
        assert "recommended_actions" in ai_insights
        assert "hiring_needs" in ai_insights
        assert "resource_issues" in ai_insights
        assert "skill_shortages" in ai_insights

@pytest.mark.asyncio
async def test_document_upload_permissions():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_token = await get_test_user_token(ac, "Employee")
        hr_token = await get_test_user_token(ac, "HR")
        
        # 1. Non-HR (Employee) should be forbidden
        emp_headers = {"Authorization": f"Bearer {emp_token}"}
        files = {"file": ("test_doc.txt", b"Mock document content for testing.", "text/plain")}
        data = {"category": "Policies", "allowed_roles": "all"}
        
        res_emp = await ac.post("/api/v1/knowledge/upload", headers=emp_headers, files=files, data=data)
        assert res_emp.status_code == 403
        assert "Only HR is authorized" in res_emp.json()["detail"]
        
        # 2. HR should be authorized to upload
        hr_headers = {"Authorization": f"Bearer {hr_token}"}
        files = {"file": ("test_doc_hr.txt", b"Mock HR policy document.", "text/plain")}
        res_hr = await ac.post("/api/v1/knowledge/upload", headers=hr_headers, files=files, data=data)
        assert res_hr.status_code == 201
        
        upload_data = res_hr.json()
        assert "successfully uploaded" in upload_data["message"]
        
        # 3. Retrieve documents
        res_docs = await ac.get("/api/v1/knowledge/documents", headers=hr_headers)
        assert res_docs.status_code == 200
        docs_list = res_docs.json()
        doc_id = None
        for d in docs_list:
            if d["filename"] == "test_doc_hr.txt":
                doc_id = d["id"]
                break
        assert doc_id is not None
        
        # 4. Attempt to delete as non-HR
        res_del_emp = await ac.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=emp_headers)
        assert res_del_emp.status_code == 403
        
        # 5. Delete as HR
        res_del_hr = await ac.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=hr_headers)
        assert res_del_hr.status_code == 200
        assert "successfully deleted" in res_del_hr.json()["message"]
