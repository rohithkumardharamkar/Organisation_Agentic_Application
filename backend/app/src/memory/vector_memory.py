from typing import Dict, Any, List
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.employee import Employee
from models.project import Project

# Global memory cache for vector chunks
_cached_vectors: List[Dict[str, Any]] = []

def generate_simple_embedding(text: str) -> List[float]:
    hash_val = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    vector = [(hash_val >> (i % 256) & 1) * 0.1 for i in range(1536)]
    return vector

def compute_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))

async def create_embeddings(db: AsyncSession) -> List[Dict[str, Any]]:
    global _cached_vectors
    _cached_vectors = []
    
    # 1. Employee Embeddings
    result = await db.execute(select(Employee))
    employees = result.scalars().all()
    for e in employees:
        text = f"Employee: {e.employee_name}, Role: {e.designation}, Department: {e.department}"
        _cached_vectors.append({
            "text": text,
            "embedding": generate_simple_embedding(text),
            "source": "employee",
            "patient_id": 1,
            "patient_name": "User"
        })
                
    # 2. Project Embeddings
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    for p in projects:
        text = f"Project: {p.project_name}, Status: {p.status}, Budget: {p.budget}"
        _cached_vectors.append({
            "text": text,
            "embedding": generate_simple_embedding(text),
            "source": "project",
            "patient_id": 1,
            "patient_name": "User"
        })
                
    return _cached_vectors

async def semantic_search(query: str, db: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    global _cached_vectors
    if not _cached_vectors:
        await create_embeddings(db)
        
    query_vector = generate_simple_embedding(query)
    scored = []
    
    for item in _cached_vectors:
        similarity = compute_cosine_similarity(query_vector, item["embedding"])
        
        keywords = query.lower().split()
        item_text_lower = item["text"].lower()
        match_count = sum(1 for kw in keywords if kw in item_text_lower)
        if keywords:
            similarity += 0.15 * (match_count / len(keywords))
            
        scored.append((similarity, item))
        
    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, item in scored[:limit]:
        results.append({
            "text": item["text"],
            "content": item["text"],
            "document_name": item["source"],
            "patient_id": item["patient_id"],
            "patient_name": item["patient_name"],
            "source": item["source"],
            "similarity_score": round(score, 4)
        })
    return results

async def retrieve_relevant_context(query: str, db: AsyncSession) -> str:
    results = await semantic_search(query, db, limit=3)
    if not results:
        return "No relevant vector memory context found."
        
    context_lines = []
    for r in results:
        context_lines.append(f"- [{r['source'].upper()}] (Score: {r['similarity_score']}): {r['text']}")
    return "\n".join(context_lines)
