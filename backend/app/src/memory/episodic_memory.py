from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import EpisodicMemory

async def get_episodic_memories(user_id: str, db: AsyncSession) -> List[str]:
    """Retrieve episodic memories for a user."""
    stmt = select(EpisodicMemory).where(EpisodicMemory.user_id == user_id).order_by(desc(EpisodicMemory.created_at))
    result = await db.execute(stmt)
    memories = result.scalars().all()
    return [m.memory for m in memories]

async def save_episodic_memory(user_id: str, memory_text: str, importance: float, db: AsyncSession):
    """Save an episodic memory for a user."""
    memory_obj = EpisodicMemory(user_id=user_id, memory=memory_text, importance=importance)
    db.add(memory_obj)
    await db.flush()
