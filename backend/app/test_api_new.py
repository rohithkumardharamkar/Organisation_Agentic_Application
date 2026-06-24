import pytest
import asyncio
import random
from httpx import ASGITransport, AsyncClient
from main import app
from src.core.database import Base, engine

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
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def get_test_token(ac: AsyncClient) -> str:
    email = f"testuser_{random.randint(1000, 9999)}@example.com"
    signup_payload = {
        "email": email,
        "password": "securepassword123",
        "name": "Test User"
    }
    await ac.post("/api/v1/auth/signup", json=signup_payload)
    login_data = {
        "username": email,
        "password": "securepassword123"
    }
    res = await ac.post("/api/v1/auth/login", data=login_data)
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_auth_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"testuser_{random.randint(1000, 9999)}@example.com"
        # Signup
        signup_payload = {
            "email": email,
            "password": "securepassword123",
            "name": "Test User"
        }
        res = await ac.post("/api/v1/auth/signup", json=signup_payload)
        assert res.status_code == 200
        assert res.json()["user"]["email"] == email
        
        # Login
        login_data = {
            "username": email,
            "password": "securepassword123"
        }
        res = await ac.post("/api/v1/auth/login", data=login_data)
        assert res.status_code == 200
        token_data = res.json()
        assert "access_token" in token_data
        token = token_data["access_token"]
        
        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        res = await ac.get("/api/v1/copilot/history", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


