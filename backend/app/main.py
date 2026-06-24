import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the root of the backend/app is in Python path so imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import Base, engine
from src.core.seed import seed_data

# Import routers
from api.auth import router as auth_router
from api.copilot import router as copilot_router

from api.workforce import router as workforce_router
from api.dashboards import router as dashboards_router
from api.timesheets import router as timesheets_router
from api.process import router as process_router
from api.ai_ops import router as ai_ops_router
from api.knowledge import router as knowledge_router
from api.evaluation import router as evaluation_router

app = FastAPI(
    title="Yottaflex Workforce API",
    description="REST API backend for the Yottaflex Workforce OS.",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(copilot_router, prefix="/api/v1")

app.include_router(workforce_router, prefix="/api/v1")
app.include_router(dashboards_router, prefix="/api/v1")
app.include_router(timesheets_router, prefix="/api/v1")
app.include_router(process_router, prefix="/api/v1")
app.include_router(ai_ops_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    # Make sure all models are imported to register them on the Base metadata
    import models
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # SQLite migration: alter uploaded_files if columns category, uploaded_by, allowed_roles, version are missing
        try:
            res = await conn.execute(text("PRAGMA table_info(uploaded_files);"))
            columns = [row[1] for row in res.fetchall()]
            if columns:
                if "category" not in columns:
                    await conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN category VARCHAR(100);"))
                if "uploaded_by" not in columns:
                    await conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN uploaded_by VARCHAR(100);"))
                if "allowed_roles" not in columns:
                    await conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN allowed_roles VARCHAR(255);"))
                if "version" not in columns:
                    await conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN version INTEGER DEFAULT 1;"))
                print("Database schema upgraded with RAG fields.")
        except Exception as e:
            print(f"Error executing schema upgrades: {e}")
            
    print("Database tables initialized successfully.")
    
    # Auto-seed dummy data
    try:
        await seed_data()
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Error seeding database on startup: {e}")

@app.get("/")
async def root():
    return {"message": "Yottaflex API Backend is running."}
