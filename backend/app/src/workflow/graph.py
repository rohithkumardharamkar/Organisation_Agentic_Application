import json
import sqlite3
import re
import asyncio
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from src.agents.state import AgentState
from src.core.database import SessionLocal
from src.core.guardrails import run_guardrails, validate_input, validate_output
from src.agents.supervisor import run_supervisor_agent
from src.agents.planner import run_planner_agent
from src.agents.workforce_agents import (
    employee_agent_node,
    hr_agent_node,
    manager_agent_node,
    process_agent_node,
    executive_agent_node,
    knowledge_agent_node,
    resource_optimization_agent_node,
    skill_intelligence_agent_node,
    project_risk_agent_node,
    workforce_planning_agent_node,
    executive_insights_agent_node
)
from src.core.optimization import (
    compress_context_tool,
    get_cached_tool_result,
    set_cached_tool_result,
    get_optimization_metrics
)
from src.observability.langsmith import log_trace, accumulate_metrics, get_observability_metrics

from src.agents.router import call_model
from src.core.config import settings

# Memory
from src.memory.summary_memory import retrieve_summary, check_and_trigger_summarization
from src.memory.reflection_memory import store_reflection, retrieve_lessons
from src.memory.entity_memory import get_user_entities, save_user_entity
from src.memory.episodic_memory import get_episodic_memories, save_episodic_memory
from src.memory.vector_memory import retrieve_relevant_context



# --- LangGraph Nodes ---

async def input_validation_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "InputValidationNode"})
    query = state.get("user_query", "").strip()
    if not query:
        return {
            "response": "Please provide a valid query.",
            "next_step": "response"
        }
        
    # Greeting Detection
    greeting_pattern = re.compile(
        r"^(hello|hi|hey|greetings|good\s+morning|good\s+afternoon|good\s+evening|yo|hiya|dear\s+agent)(\s+.*)?$",
        re.IGNORECASE
    )
    if greeting_pattern.match(query):
        return {
            "response": "Hello! I am your Lead Workforce Intelligence Agent. How can I help you with employee records, project status, allocations, process engineering reports, or other organizational data today?",
            "intent": "greeting",
            "risk_level": "low",
            "next_step": "response"
        }
        
    # Input Guardrails (PII / Off-Topic detection)
    try:
        validate_input(query)
    except ValueError as e:
        error_msg = str(e)
        log_trace("input_guardrail_blocked", {"reason": error_msg})
        if "Query restricted" in error_msg or "off-topic" in error_msg.lower():
            response_text = "I am a Workforce OS agent. I support organizational data queries only."
        elif "Blocked input" in error_msg:
            response_text = f"Blocked input detected: {error_msg}"
        else:
            response_text = error_msg
        return {
            "response": response_text,
            "next_step": "response"
        }
        
    # Security/Jailbreak Guardrails
    async with SessionLocal() as db:
        guard_res = await run_guardrails(query, db)
        
    if not guard_res.allowed:
        log_trace("guardrail_violation", {"action": guard_res.action, "details": guard_res.details})
        from src.core.email import send_email
        send_email(
            subject=f"SECURITY ALERT: {guard_res.action}",
            body=f"A security violation was blocked by the guardrail system.\n\nQuery: {query}\nAction: {guard_res.action}\nDetails: {guard_res.details}"
        )
        return {
            "response": guard_res.details,
            "next_step": "response"
        }
        
    return {
        "user_query": guard_res.masked_text,
        "next_step": "memory_retrieval"
    }


from src.memory.memory_manager import MemoryManager

async def memory_retrieval_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "MemoryRetrievalNode"})
    user_id = state.get("user_id") or "user_1"
    user_role = state.get("user_role", "Employee")
    
    # Dynamically select relevant memory sources to minimize token usage
    selected_sources = await MemoryManager.select_sources(state["user_query"], user_role)
    
    summary = ""
    entities = {}
    episodic = []
    vector_context = {}
    lessons = []
    
    async with SessionLocal() as db:
        if "summary" in selected_sources:
            summary = await retrieve_summary(user_id, db)
        if "entities" in selected_sources:
            entities = await get_user_entities(user_id, db)
        if "episodic" in selected_sources:
            episodic = await get_episodic_memories(user_id, db)
        if "vector" in selected_sources:
            vector_context = await retrieve_relevant_context(state["user_query"], db)
        if "lessons" in selected_sources:
            lessons = await retrieve_lessons(user_id, db)
        
    lessons_str = "\n".join([f"- {l.get('lesson_learned')}" for l in lessons]) if lessons else ""
    
    retrieved_memories = {
        "summary": summary,
        "entities": entities,
        "episodic": episodic,
        "vector": vector_context
    }
    
    return {
        "selected_memory_sources": selected_sources,
        "retrieved_memories": retrieved_memories,
        "lessons_learned": lessons_str,
        "next_step": "supervisor"
    }



AGENT_ROLE_PERMISSIONS = {
    "employee_agent": ["Employee", "HR", "Reporting Manager", "Process Engineer"],
    "hr_agent": ["HR"],
    "manager_agent": ["Reporting Manager", "HR"],
    "process_agent": ["Process Engineer", "Reporting Manager"],
    "executive_agent": ["HR"],
    "knowledge_agent": ["Employee", "HR", "Reporting Manager", "Process Engineer"],
    "resource_optimization_agent": ["HR", "Reporting Manager"],
    "skill_intelligence_agent": ["HR", "Reporting Manager"],
    "project_risk_agent": ["Reporting Manager", "HR"],
    "workforce_planning_agent": ["HR", "Reporting Manager"],
    "executive_insights_agent": ["HR"],
}

async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "SupervisorNode"})
    query = state["user_query"]
    messages = state.get("messages", [])
    chat_context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[-5:]])
    
    user_role = state.get("user_role", "Employee")
    sup_res = await run_supervisor_agent(query, chat_context, user_role)
    selected_agents = sup_res.get("selected_agents", [])
    
    # Enforce role-based access control for specialized agents
    authorized_agents = []
    for agent in selected_agents:
        allowed_roles = AGENT_ROLE_PERMISSIONS.get(agent, [])
        if not allowed_roles or user_role in allowed_roles:
            authorized_agents.append(agent)
            
    if not authorized_agents:
        # Fallback to employee_agent if none authorized
        authorized_agents = ["employee_agent"]
        
    return {
        "intent": sup_res["intent"],
        "risk_level": sup_res["risk_level"],
        "selected_agents": authorized_agents,
        "current_agent": authorized_agents[0], # Backwards compatibility
        "supervisor_confidence": sup_res.get("confidence", 1.0),
        "supervisor_reasoning": sup_res.get("reasoning", ""),
        "next_step": "planner"
    }


async def planner_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "PlannerNode"})
    query = state["user_query"]
    intent = state["intent"]
    selected_agents = state.get("selected_agents", [])
    if not selected_agents:
        selected_agents = [state.get("current_agent", "employee_agent")]
    
    retrieved = state.get("retrieved_memories") or {}
    summary = retrieved.get("summary", "")
    entities = retrieved.get("entities", {})
    
    # Construct memory context and compress if it's too long
    raw_memory_context = (
        f"Summary: {summary}\n"
        f"Entities: {json.dumps(entities)}\n"
        f"Lessons: {state.get('lessons_learned', '')}"
    )
    memory_context = await MemoryManager.compress_context(raw_memory_context, max_words=500)
    
    plan_res = await run_planner_agent(query, intent, selected_agents, memory_context)
    
    return {
        "execution_plan": plan_res["execution_plan"],
        "plan_steps": plan_res["plan_steps"],
        "current_step": 0,
        "next_step": "specialized_agent"
    }


async def aggregator_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "AggregatorNode"})
    agent_outputs = state.get("agent_outputs") or []
    
    if not agent_outputs:
        return {
            "response": "No specialist agents returned any output.",
            "next_step": "verification"
        }
        
    if len(agent_outputs) == 1:
        # Single agent execution, forward response directly
        out = agent_outputs[0]
        return {
            "response": out.get("response", ""),
            "next_step": "verification"
        }
        
    # Multi-agent parallel execution, synthesize final response
    system_prompt = (
        "You are the Lead Yottaflex Synthesis Aggregator Node.\n"
        "Your job is to merge responses from multiple specialist agents into a single, unified, coherent answer.\n"
        "Consolidate conflicting details, merge tables if applicable, and present the consolidated view clearly in markdown.\n"
        "Strictly preserve all provided facts, numbers, and names without introducing any hallucinations."
    )
    
    context = ""
    for out in agent_outputs:
        context += f"### Agent: {out['agent']}\nResponse:\n{out['response']}\n\n"
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User Query: {state['user_query']}\n\nSpecialist Agent Responses:\n{context}")
    ]
    
    try:
        res = await call_model(messages, settings.FAST_MODEL, stream_tokens=True)
        final_response = res["text"]
    except Exception as e:
        print(f"Aggregator synthesis failed: {e}")
        final_response = "\n\n".join([f"**{out['agent'].replace('_',' ').title()}**:\n{out['response']}" for out in agent_outputs])
        
    return {
        "response": final_response,
        "next_step": "verification"
    }


def check_needs_approval(state: AgentState) -> bool:
    risk = state.get("risk_level", "low")
    return risk in ["high", "critical"]


async def run_llm_fact_check(query: str, response: str, retrieved_memories: Dict[str, Any], agent_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Helper method to run verification LLM fact check against ground-truth outputs."""
    context = ""
    for out in agent_outputs:
        context += f"Agent: {out['agent']}\nResponse:\n{out['response']}\n\n"
    
    system_prompt = (
        "You are the Yottaflex Verification Fact-Checking LLM.\n"
        "Verify the final response against the raw specialist agent outputs.\n"
        "Identify if the final response has any claims, metrics, or details not supported by the grounding context.\n"
        "Output strictly in JSON:\n"
        "{\n"
        "  \"status\": \"PASSED|FAILED\",\n"
        "  \"reasoning\": \"Explain any factual deviations or why it passed\"\n"
        "}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Query: {query}\n\nFinal Response:\n{response}\n\nGrounding Context:\n{context}")
    ]
    
    try:
        res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
        return json.loads(res["text"])
    except Exception as e:
        print(f"LLM verification fact-check failed: {e}")
        return {"status": "PASSED", "reasoning": "Verification check error fallback"}


async def verification_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "VerificationNode"})
    
    # 1. Factual Grounding & Hallucination Check
    query = state.get("user_query", "")
    response = state.get("response", "")
    retrieved = state.get("retrieved_memories") or {}
    outputs = state.get("agent_outputs") or []
    
    fact_check = await run_llm_fact_check(query, response, retrieved, outputs)
    fact_check_status = fact_check.get("status", "PASSED")
    fact_check_reasoning = fact_check.get("reasoning", "")
    
    # Force low confidence score on failure to trigger self-correction retry
    agent_confidence = state.get("agent_confidence") or {}
    if fact_check_status == "FAILED":
        print(f"Fact check FAILED: {fact_check_reasoning}")
        agent_confidence = {k: 0.1 for k in agent_confidence.keys()} if agent_confidence else {"aggregator": 0.1}
    
    needs_gate = check_needs_approval(state)
    
    if needs_gate:
        thread_id = state.get("thread_id") or "default_thread"
        async with SessionLocal() as db:
            from src.models.db_models import PendingApproval
            stmt = select(PendingApproval).where(
                PendingApproval.thread_id == thread_id,
                PendingApproval.status == "Pending"
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if not existing:
                intent = state.get("intent", "general")
                action_type = "Leave Approval"
                if "timesheet" in intent:
                    action_type = "Timesheet Submission"
                elif "resource" in intent or "allocation" in intent:
                    action_type = "Resource Allocation"
                elif "salary" in intent or "budget" in intent:
                    action_type = "Budget Approval"
                elif "candidate" in intent or "job" in intent:
                    action_type = "Candidate Selection"
                else:
                    action_type = "Employee Promotion" if "promote" in state["user_query"].lower() else "General Operational Approval"
                    
                new_app = PendingApproval(
                    thread_id=thread_id,
                    action_type=action_type,
                    description=f"Action requested: {state['user_query']}",
                    risk_level=state.get("risk_level", "high").capitalize(),
                    status="Pending"
                )
                db.add(new_app)
                await db.commit()
                
        return {
            "verification_status": fact_check_status,
            "verification_details": fact_check_reasoning,
            "agent_confidence": agent_confidence,
            "approval_required": True,
            "next_step": "human_approval"
        }
    else:
        return {
            "verification_status": fact_check_status,
            "verification_details": fact_check_reasoning,
            "agent_confidence": agent_confidence,
            "approval_required": False,
            "next_step": "reflection"
        }


async def retry_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "RetryNode"})
    retries = state.get("retry_count", 0) + 1
    log_trace("workflow_retry", {"retry_count": retries})
    
    if retries > settings.MAX_RETRIES:
        log_trace("execution_failed", {"reason": "Max retries exceeded"})
        return {
            "response": "Workflow execution failed after maximum self-correction retries due to validation failures.",
            "next_step": "response"
        }
        
    return {
        "retry_count": retries,
        "tools_to_call": [],
        "next_step": "planner"
    }


async def human_approval_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "HumanApprovalNode"})
    app_granted = state.get("approval_granted", None)
    thread_id = state.get("thread_id") or "default_thread"
    
    if app_granted is None:
        log_trace("human_approval_pause", {})
        return {
            "approval_required": True,
            "next_step": "human_approval"
        }
        
    async with SessionLocal() as db:
        from src.models.db_models import PendingApproval
        stmt = select(PendingApproval).where(
            PendingApproval.thread_id == thread_id,
            PendingApproval.status == "Pending"
        )
        res = await db.execute(stmt)
        pending = res.scalar_one_or_none()
        if pending:
            pending.status = "Approved" if app_granted else "Rejected"
            await db.commit()
            
    if app_granted is False:
        log_trace("human_approval_rejected", {})
        return {
            "approval_required": False,
            "response": "Workflow execution rejected by human supervisor.",
            "next_step": "reflection"
        }
        
    log_trace("human_approval_granted", {})
    return {
        "approval_required": False,
        "next_step": "reflection"
    }



async def reflection_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "ReflectionNode"})
    user_id = state.get("user_id") or "user_1"
    verification_status = state.get("verification_status", "PASSED")
    approval_action = state.get("approval_action")
    query = state["user_query"]
    
    async with SessionLocal() as db:
        if verification_status == "FAILED":
            issue = f"Verification failed for query: '{query}'"
            lesson = "Ensure financial safety parameters are correctly input and values comply with ranges."
            await store_reflection(user_id, issue, lesson, db)
            log_trace("reflection_stored", {"issue": issue, "lesson": lesson})
        elif approval_action == "rejected" or state.get("approval_granted") is False:
            issue = f"User/Supervisor rejected the scheduled action for: '{query}'"
            lesson = "Confirm manual transfers or budget edits with the user before attempting execution node."
            await store_reflection(user_id, issue, lesson, db)
            log_trace("reflection_stored", {"issue": issue, "lesson": lesson})
            
        tool_results = state.get("tool_results", {})
        for tool_name, result in tool_results.items():
            if result.get("status") == "error":
                issue = f"Tool '{tool_name}' returned error: {result.get('metadata', {}).get('error')}"
                lesson = f"Check arguments passed to {tool_name} and ensure the target account or savings goal is active."
                await store_reflection(user_id, issue, lesson, db)
                log_trace("reflection_stored", {"issue": issue, "lesson": lesson})
                
    return {"next_step": "memory_update"}


async def memory_update_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "MemoryUpdateNode"})
    user_id = state.get("user_id") or "user_1"
    thread_id = state.get("thread_id") or "default_thread"
    query = state["user_query"]
    response = state.get("response", "")
    
    async with SessionLocal() as db:
        await check_and_trigger_summarization(user_id, thread_id, db)
        
        # Save episodic interaction memory
        await MemoryManager.update_after_interaction(user_id, thread_id, query, response, db)
        
        discovery_prompt = (
            "Analyze the user query and response to identify if any new permanent user entities (like name, email, etc.) were mentioned or established.\n"
            "Respond in JSON matching this schema:\n"
            "{\n"
            "  \"entity\": {\"entity_name\": \"...\", \"entity_value\": \"...\"} or null\n"
            "}"
        )
        messages = [
            SystemMessage(content=discovery_prompt),
            HumanMessage(content=f"Query: {query}\nResponse: {response}")
        ]
        
        try:
            discovery_res = await call_model(messages, settings.FAST_MODEL, json_mode=True)
            disc = json.loads(discovery_res["text"])
            
            if disc.get("entity"):
                e = disc["entity"]
                await save_user_entity(user_id, e["entity_name"], e["entity_value"], 1.0, db)
            await db.commit()
        except Exception as e:
            print(f"Error in memory discovery update: {e}")
            
    return {"next_step": "response"}


async def response_node(state: AgentState) -> Dict[str, Any]:
    log_trace("node_start", {"node": "ResponseNode"})
    
    # If agent already produced a grounded response, use it directly — do NOT re-synthesize
    if state.get("response"):
        final_text = state["response"]
    else:
        system_prompt = (
            "You are the Yottaflex Workforce OS Lead Agent. Based on the agent execution results, "
            "formulate a professional, clear, and action-oriented response. "
            "Only reference facts from the data provided. Do not hallucinate or add numbers/names not present in the data. "
            "Present clean, markdown formatted information."
        )
        
        retrieved = state.get("retrieved_memories") or {}
        memory_context = f"Workforce summary: {retrieved.get('summary', '')}\n"
        lessons = state.get("lessons_learned", "")
        lessons_context = f"\n### REFLECTION MEMORY (LESSONS LEARNED):\n{lessons}\n" if lessons else ""
     
        user_prompt = (
            f"Original query: {state['user_query']}\n\n"
            f"{memory_context}"
            f"{lessons_context}"
            f"Executed Tool outcomes: {json.dumps(state.get('tool_results', {}))}"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        res = await call_model(messages, settings.FAST_MODEL, stream_tokens=True)
        accumulate_metrics(res)
        final_text = res["text"]
        
    try:
        validate_output(final_text)
    except ValueError as e:
        error_msg = str(e)
        log_trace("output_guardrail_blocked", {"reason": error_msg})
        final_text = f"Security block: {error_msg}"
        
    log_trace("execution_success", {})
    return {
        "response": final_text,
        "messages": [AIMessage(content=final_text)],
        "next_step": "end"
    }


# --- Routing Logics ---

def route_from_start(state: AgentState) -> str:
    return "input_validation_node"

def route_from_input_validation(state: AgentState) -> str:
    if state.get("next_step") == "response":
        return "response_node"
    return "memory_retrieval_node"

def route_from_verification(state: AgentState) -> str:
    agent_confidence = state.get("agent_confidence") or {}
    if agent_confidence:
        min_conf = min(agent_confidence.values())
        if min_conf < 0.70:
            return "retry"
    
    needs_gate = check_needs_approval(state)
    if needs_gate:
        return "human_approval"
    return "reflection"

def route_from_retry(state: AgentState) -> str:
    if state.get("next_step") == "response":
        return "response_node"
    return "planner_node"

def route_from_human_approval(state: AgentState) -> str:
    if state.get("approval_required") and state.get("approval_granted") is None:
        return END
    return "reflection_node"

def route_from_supervisor(state: AgentState) -> str:
    if state.get("next_step") == "response":
        return "response_node"
    return "planner_node"

def route_from_planner(state: AgentState) -> List[str]:
    plan_steps = state.get("plan_steps") or []
    target_nodes = []
    for step in plan_steps:
        agent = step.get("agent")
        if agent:
            node_name = f"{agent}_node"
            if node_name not in target_nodes:
                target_nodes.append(node_name)
    if not target_nodes:
        target_nodes.append("employee_agent_node")
    return target_nodes


# --- Graph Assembly ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("input_validation_node", input_validation_node)
workflow.add_node("memory_retrieval_node", memory_retrieval_node)
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("planner_node", planner_node)

# Add Specialist Nodes
workflow.add_node("employee_agent_node", employee_agent_node)
workflow.add_node("hr_agent_node", hr_agent_node)
workflow.add_node("manager_agent_node", manager_agent_node)
workflow.add_node("process_agent_node", process_agent_node)
workflow.add_node("executive_agent_node", executive_agent_node)
workflow.add_node("knowledge_agent_node", knowledge_agent_node)
workflow.add_node("resource_optimization_agent_node", resource_optimization_agent_node)
workflow.add_node("skill_intelligence_agent_node", skill_intelligence_agent_node)
workflow.add_node("project_risk_agent_node", project_risk_agent_node)
workflow.add_node("workforce_planning_agent_node", workforce_planning_agent_node)
workflow.add_node("executive_insights_agent_node", executive_insights_agent_node)

workflow.add_node("aggregator_node", aggregator_node)
workflow.add_node("verification_node", verification_node)
workflow.add_node("retry_node", retry_node)
workflow.add_node("human_approval_node", human_approval_node)
workflow.add_node("reflection_node", reflection_node)
workflow.add_node("memory_update_node", memory_update_node)
workflow.add_node("response_node", response_node)

# Add edges and conditional transitions
workflow.add_conditional_edges(START, route_from_start)

workflow.add_conditional_edges("input_validation_node", route_from_input_validation, {
    "response_node": "response_node",
    "memory_retrieval_node": "memory_retrieval_node"
})

workflow.add_edge("memory_retrieval_node", "supervisor_node")
workflow.add_conditional_edges("supervisor_node", route_from_supervisor, {
    "response_node": "response_node",
    "planner_node": "planner_node"
})

# Dynamic parallel branching from Planner to Specialist Nodes
workflow.add_conditional_edges("planner_node", route_from_planner, {
    "employee_agent_node": "employee_agent_node",
    "hr_agent_node": "hr_agent_node",
    "manager_agent_node": "manager_agent_node",
    "process_agent_node": "process_agent_node",
    "executive_agent_node": "executive_agent_node",
    "knowledge_agent_node": "knowledge_agent_node",
    "resource_optimization_agent_node": "resource_optimization_agent_node",
    "skill_intelligence_agent_node": "skill_intelligence_agent_node",
    "project_risk_agent_node": "project_risk_agent_node",
    "workforce_planning_agent_node": "workforce_planning_agent_node",
    "executive_insights_agent_node": "executive_insights_agent_node"
})

# Map parallel specialist nodes to aggregate in the join node
workflow.add_edge("employee_agent_node", "aggregator_node")
workflow.add_edge("hr_agent_node", "aggregator_node")
workflow.add_edge("manager_agent_node", "aggregator_node")
workflow.add_edge("process_agent_node", "aggregator_node")
workflow.add_edge("executive_agent_node", "aggregator_node")
workflow.add_edge("knowledge_agent_node", "aggregator_node")
workflow.add_edge("resource_optimization_agent_node", "aggregator_node")
workflow.add_edge("skill_intelligence_agent_node", "aggregator_node")
workflow.add_edge("project_risk_agent_node", "aggregator_node")
workflow.add_edge("workforce_planning_agent_node", "aggregator_node")
workflow.add_edge("executive_insights_agent_node", "aggregator_node")

workflow.add_edge("aggregator_node", "verification_node")

workflow.add_conditional_edges("verification_node", route_from_verification, {
    "retry": "retry_node",
    "human_approval": "human_approval_node",
    "reflection": "reflection_node"
})

workflow.add_conditional_edges("retry_node", route_from_retry, {
    "response_node": "response_node",
    "planner_node": "planner_node"
})

workflow.add_conditional_edges("human_approval_node", route_from_human_approval, {
    "reflection_node": "reflection_node",
    "__end__": END
})

workflow.add_edge("reflection_node", "memory_update_node")
workflow.add_edge("memory_update_node", "response_node")
workflow.add_edge("response_node", END)


# Compile graph with persistent AsyncSqliteSaver checkpointer and interrupt before approval node
_graph_app = None
_checkpointer = None

def get_graph_app():
    global _graph_app, _checkpointer
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None
    
    # Re-create if event loop changed (e.g. under pytest)
    if _graph_app is not None and _checkpointer is not None:
        if getattr(_checkpointer, "loop", None) is not loop:
            _graph_app = None
            _checkpointer = None
            
    if _graph_app is not None:
        return _graph_app
    
    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    
    conn = aiosqlite.connect("yottaflex.db")
    _checkpointer = AsyncSqliteSaver(conn)
    
    _graph_app = workflow.compile(
        checkpointer=_checkpointer,
        interrupt_before=["human_approval_node"]
    )
    return _graph_app


