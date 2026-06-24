import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings
from src.agents.registry import get_registry_summary, AGENT_REGISTRY

async def run_supervisor_agent(user_query: str, chat_context: str = "", user_role: str = "Employee") -> Dict[str, Any]:
    """
    Supervisor Agent executing Intent Detection, Risk Assessment, Priority Detection,
    and Multi-Agent Routing with Confidence Scoring.

    Returns selected_agents (list), confidence score, reasoning, and routing metadata.
    """
    # Dynamically generate agent list from registry filtered by user role
    agent_summary = get_registry_summary(role=user_role)
    available_agent_names = [a.name for a in AGENT_REGISTRY.values() if user_role in a.permissions]

    system_prompt = (
        f"You are the Lead Yottaflex Workforce OS Supervisor. The user you are talking to has the role: {user_role}.\n"
        "Your task is to analyze the user's organizational query, classify the intent, detect the priority, assess the risk level, "
        "and route to ONE OR MORE specialist agents.\n\n"
        "IMPORTANT: If the query spans multiple domains (e.g., resource availability AND skill gaps), select MULTIPLE agents.\n"
        "Select only agents the user's role permits.\n\n"
        f"Available Agents for role '{user_role}':\n{agent_summary}\n\n"
        "Do NOT answer the query directly. Only output the classification in JSON.\n\n"
        "Intents to choose from:\n"
        "- employee_queries, hr_queries, manager_queries, process_engineering, executive_summary, knowledge_search, "
        "resource_optimization, skill_intelligence, project_risk, workforce_planning, executive_insights\n"
        "Priority to choose from: low|medium|high\n"
        "Risk levels to choose from: low|medium|high\n\n"
        "You MUST output a JSON response matching this exact schema:\n"
        "{\n"
        '  "intent": "[selected_intent]",\n'
        '  "priority": "low|medium|high",\n'
        '  "risk_level": "low|medium|high",\n'
        '  "selected_agents": ["agent_name_1", "agent_name_2"],\n'
        '  "confidence": 0.93,\n'
        '  "reasoning": "Brief explanation of your classification and why these agents were selected"\n'
        "}\n\n"
        "Rules:\n"
        "- selected_agents MUST be a JSON array of 1 to 3 agent names from the available list.\n"
        "- confidence MUST be a float from 0.0 to 1.0 reflecting your certainty in the routing.\n"
        "- For simple single-domain queries, select exactly 1 agent.\n"
        "- For complex cross-domain queries, select 2-3 agents that should run in parallel."
    )

    query_text = f"User Query: {user_query}"
    if chat_context:
        query_text = f"Chat Context:\n{chat_context}\n\n{query_text}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query_text)
    ]

    res = await call_model(messages, settings.REASONING_MODEL, json_mode=True)

    try:
        parsed = json.loads(res["text"])

        # Normalize selected_agents: support both old single target_agent and new multi-agent format
        selected_agents = parsed.get("selected_agents", [])
        if not selected_agents:
            # Backwards compatibility: if LLM returned target_agent instead
            target = parsed.get("target_agent")
            if target:
                selected_agents = [target]
            else:
                selected_agents = ["employee_agent"]

        # Ensure all selected agents are valid and role-permitted
        selected_agents = [a for a in selected_agents if a in available_agent_names]
        if not selected_agents:
            selected_agents = ["employee_agent"] if "employee_agent" in available_agent_names else [available_agent_names[0]]

        confidence = float(parsed.get("confidence", 0.85))
        reasoning = parsed.get("reasoning", "")

        return {
            "intent": parsed.get("intent", "employee_queries"),
            "priority": parsed.get("priority", "medium"),
            "risk_level": parsed.get("risk_level", "low"),
            "selected_agents": selected_agents,
            "target_agent": selected_agents[0],  # Backwards compat: primary agent
            "confidence": confidence,
            "reasoning": reasoning,
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
    except Exception:
        # Fallback keyword-based classification
        intent = "employee_queries"
        target_agent = "employee_agent"
        priority = "medium"
        risk_level = "low"

        query_lower = user_query.lower()
        if "document" in query_lower or "policy" in query_lower or "sop" in query_lower or "handbook" in query_lower:
            intent = "knowledge_search"
            target_agent = "knowledge_agent"
        elif "hiring" in query_lower or "forecast" in query_lower:
            intent = "workforce_planning"
            target_agent = "workforce_planning_agent"
        elif "risk" in query_lower or "delay" in query_lower:
            intent = "project_risk"
            target_agent = "project_risk_agent"
        elif "skill" in query_lower or "gap" in query_lower:
            intent = "skill_intelligence"
            target_agent = "skill_intelligence_agent"
        elif "bench" in query_lower or "utilization" in query_lower or "allocate" in query_lower or "recommend resource" in query_lower:
            intent = "resource_optimization"
            target_agent = "resource_optimization_agent"
        elif "health" in query_lower or "executive action" in query_lower:
            intent = "executive_insights"
            target_agent = "executive_insights_agent"
        elif "sprint" in query_lower or "process" in query_lower:
            intent = "process_engineering"
            target_agent = "process_agent"
        elif "leave" in query_lower or "absent" in query_lower or "hr" in query_lower:
            intent = "hr_queries"
            target_agent = "hr_agent"
        elif "approval" in query_lower or "timesheet" in query_lower:
            intent = "manager_queries"
            target_agent = "manager_agent"

        # Multi-agent detection in fallback: check if query spans multiple domains
        selected_agents = [target_agent]
        if ("skill" in query_lower or "gap" in query_lower) and ("bench" in query_lower or "available" in query_lower or "utilization" in query_lower):
            selected_agents = ["resource_optimization_agent", "skill_intelligence_agent"]
        elif ("risk" in query_lower or "delay" in query_lower) and ("resource" in query_lower or "allocat" in query_lower):
            selected_agents = ["project_risk_agent", "resource_optimization_agent"]

        # Filter by role permissions
        selected_agents = [a for a in selected_agents if a in available_agent_names]
        if not selected_agents:
            selected_agents = [target_agent] if target_agent in available_agent_names else ["employee_agent"]

        return {
            "intent": intent,
            "priority": priority,
            "risk_level": risk_level,
            "selected_agents": selected_agents,
            "target_agent": selected_agents[0],
            "confidence": 0.70,
            "reasoning": "Fallback keyword-based routing due to non-JSON LLM output",
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
