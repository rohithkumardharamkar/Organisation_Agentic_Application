import json
import re
from typing import Dict, Any, List, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings

async def route_memory(query: str) -> Tuple[List[str], Any]:
    """
    Classify the query using the fast LLM model to determine which memory systems should be activated.
    Returns: (list of memory sources, employee_or_project_name)
    """
    system_prompt = (
        "You are the Workforce Memory Router. Analyze the user's query and decide which memory systems are needed to answer it.\n\n"
        "Memory Systems:\n"
        "- entity: For structured employee profile, designation, department, manager, location, skills, and allocations.\n"
        "- episodic: For chronological logs of timesheets, submissions, approvals, sprint achievements, leaves, and activity types.\n"
        "- vector: For semantic knowledge retrieval from uploaded policies, SOPs, handbooks, guidelines, and standards.\n"
        "- summary: For high-level workforce health summary or general conversation.\n\n"
        "If a query refers to multiple aspects, route to multiple systems (e.g. ['entity', 'episodic']).\n"
        "Extract any specific Employee or Project name if mentioned (e.g., 'Amit Kumar', 'CRM Overhaul').\n\n"
        "You MUST respond with a JSON object in this exact schema:\n"
        "{\n"
        "  \"sources\": [\"entity\"|\"episodic\"|\"vector\"|\"summary\"],\n"
        "  \"merchant\": \"Employee or Project name mentioned or null\"\n"
        "}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]
    
    merchant = None
    sources = ["summary"] # Default fallback
    
    try:
        res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
        parsed = json.loads(res["text"])
        sources = parsed.get("sources", ["summary"])
        merchant = parsed.get("merchant")
    except Exception:
        # Regex-based fallback routing
        query_lower = query.lower()
        
        # Detect employee or project fallback
        for m in ["amit", "rahul", "priya", "crm", "migration", "dashboard"]:
            if m in query_lower:
                merchant = m
                break
                     
        sources = []
        if any(w in query_lower for w in ["employee", "role", "designation", "skill", "manager", "allocation", "location"]):
            sources.append("entity")
        if any(w in query_lower for w in ["timesheet", "leave", "sprint", "approval", "absent", "compliance", "report", "hours"]):
            sources.append("episodic")
        if any(w in query_lower for w in ["policy", "sop", "guideline", "handbook", "standards", "document", "file"]):
            sources.append("vector")
            
        if not sources:
            sources.append("summary")
            
    # Clean up sources list
    valid_sources = [s for s in sources if s in ["entity", "episodic", "vector", "summary"]]
    
    if not valid_sources:
        valid_sources = ["summary"]
        
    return valid_sources, merchant
