from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import EntityMemory

async def get_user_entities(user_id: str, db: AsyncSession) -> Dict[str, str]:
    """Retrieve user-specific key-value entities."""
    stmt = select(EntityMemory).where(EntityMemory.user_id == user_id)
    result = await db.execute(stmt)
    entities = result.scalars().all()
    return {e.entity_name: e.entity_value for e in entities}

async def save_user_entity(user_id: str, entity_name: str, entity_value: str, confidence_score: float, db: AsyncSession):
    """Save or update a user-specific entity."""
    stmt = select(EntityMemory).where(EntityMemory.user_id == user_id, EntityMemory.entity_name == entity_name)
    res = await db.execute(stmt)
    entity = res.scalar_one_or_none()
    if entity:
        entity.entity_value = entity_value
        entity.confidence_score = confidence_score
    else:
        entity = EntityMemory(user_id=user_id, entity_name=entity_name, entity_value=entity_value, confidence_score=confidence_score)
        db.add(entity)
    await db.flush()
