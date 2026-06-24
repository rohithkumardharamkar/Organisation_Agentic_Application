import json
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from src.agents.state import AgentState
from src.tools.workforce_tools import (
    resource_utilization_tool,
    leave_intelligence_tool,
    project_health_tool,
    timesheet_compliance_tool,
    skill_intelligence_tool,
    executive_summary_tool,
    evaluate_employee_performance_tool,
    generate_process_report_tool,
    recommend_resources,
    analyze_skill_gap,
    recommend_upskilling,
    predict_project_risk,
    bench_optimization,
    hiring_forecast,
    forecast_project_completion,
    project_cost_analysis,
    knowledge_usage_analytics,
    promotion_readiness,
    identify_successors,
    organization_health,
    generate_executive_actions,
    generate_meeting_summary,
    predict_client_escalation,
    employee_intelligence_tool,
    employee_skill_lookup,
    availability_lookup,
    allocation_lookup,
    project_requirement_lookup,
    experience_lookup,
    employee_skill_tool,
    project_skill_tool,
    skill_gap_analysis_tool,
    learning_recommendation_tool,
    certification_recommendation_tool,
    resource_availability_tool,
    blocker_tool,
    risk_scoring_tool,
    resource_forecast_tool,
    project_demand_tool,
    skill_forecast_tool,
    hiring_forecast_tool,
    organization_health_tool,
    project_portfolio_tool,
    skill_gap_tool,
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
from src.core.database import SessionLocal
from src.agents.router import call_model
from src.core.config import settings
from services.qdrant_service import QdrantService
from models.user import User
from models.employee import Employee
from sqlalchemy import select

import time
from datetime import datetime
from src.agents.registry import AGENT_REGISTRY

# Map tool names to their corresponding functions imported above
TOOL_FUNCTIONS = {
    "employee_intelligence_tool": employee_intelligence_tool,
    "get_employee_profile": get_employee_profile,
    "get_leave_balance": get_leave_balance,
    "get_attendance_summary": get_attendance_summary,
    "get_timesheet_status": get_timesheet_status,
    "get_salary_slip": get_salary_slip,
    "apply_leave": apply_leave,
    "submit_timesheet": submit_timesheet,
    "search_policy": search_policy,
    "create_ticket": create_ticket,
    "get_ticket_status": get_ticket_status,
    "get_job_openings": get_job_openings,
    "apply_for_job": apply_for_job,
    "send_notification": send_notification,
    "save_memory": save_memory,
    "retrieve_memory": retrieve_memory,
    "leave_intelligence_tool": leave_intelligence_tool,
    "timesheet_compliance_tool": timesheet_compliance_tool,
    "generate_process_report_tool": generate_process_report_tool,
    "executive_summary_tool": executive_summary_tool,
    "bench_optimization": bench_optimization,
    "employee_skill_lookup": employee_skill_lookup,
    "availability_lookup": availability_lookup,
    "allocation_lookup": allocation_lookup,
    "project_requirement_lookup": project_requirement_lookup,
    "experience_lookup": experience_lookup,
    "recommend_resources": recommend_resources,
    "skill_gap_analysis_tool": skill_gap_analysis_tool,
    "learning_recommendation_tool": learning_recommendation_tool,
    "certification_recommendation_tool": certification_recommendation_tool,
    "project_skill_tool": project_skill_tool,
    "employee_skill_tool": employee_skill_tool,
    "recommend_upskilling": recommend_upskilling,
    "analyze_skill_gap": analyze_skill_gap,
    "resource_availability_tool": resource_availability_tool,
    "blocker_tool": blocker_tool,
    "risk_scoring_tool": risk_scoring_tool,
    "project_health_tool": project_health_tool,
    "predict_project_risk": predict_project_risk,
    "resource_forecast_tool": resource_forecast_tool,
    "project_demand_tool": project_demand_tool,
    "skill_forecast_tool": skill_forecast_tool,
    "hiring_forecast_tool": hiring_forecast_tool,
    "organization_health_tool": organization_health_tool,
    "project_portfolio_tool": project_portfolio_tool,
    "skill_gap_tool": skill_gap_tool,
    "resource_utilization_tool": resource_utilization_tool
}

async def run_agentic_node(agent_name: str, state: AgentState) -> Dict[str, Any]:
    """
    Generic execution runner for all registered workforce specialist agents.
    Handles RBAC authorization, dynamic tool selection, parameter building,
    tool calling, self-confidence scoring, citations, and model fallbacks.
    """
    start_time = time.time()
    agent_def = AGENT_REGISTRY.get(agent_name)
    if not agent_def:
        return {"response": f"Agent '{agent_name}' not defined in registry."}

    role = state.get("user_role", "Employee")
    
    # 1. RBAC Check
    if role not in agent_def.permissions:
        content = f"Access Denied: Your role ({role}) is not authorized to access {agent_def.display_name}."
        return {
            "response": content,
            "messages": [AIMessage(content=content)],
            "agent_outputs": [{
                "agent": agent_name,
                "response": content,
                "confidence": 0.0,
                "reasoning": "RBAC Authorization Denied",
                "tool_used": None,
                "tool_status": "denied"
            }],
            "agent_confidence": {agent_name: 0.0},
            "agent_trace": [{
                "node": agent_name,
                "action": "RBAC Check Failed",
                "confidence": 0.0,
                "reasoning": f"Role '{role}' is not authorized.",
                "timestamp": str(datetime.utcnow()),
                "latency": 0.0
            }]
        }

    query = state.get("user_query", "")
    user_id = state.get("user_id", "user_1")

    # Resolve active employee's profile to pass logged-in user details to LLM
    logged_in_name = "Rahul Sharma"
    async with SessionLocal() as db:
        stmt = select(User).where(User.id == int(user_id) if str(user_id).isdigit() else User.id == user_id)
        user_res = await db.execute(stmt)
        user = user_res.scalar_one_or_none()
        if user:
            emp_stmt = select(Employee).where(Employee.email == user.email)
            emp_res = await db.execute(emp_stmt)
            emp = emp_res.scalar_one_or_none()
            if emp:
                logged_in_name = emp.employee_name

    # 2. Sequential Multi-Tool Calling Loop
    tool_history = []
    trace_steps = []
    
    if agent_name == "knowledge_agent":
        # Semantic search direct call
        tool_used = "qdrant_semantic_search"
        try:
            results = await QdrantService.search(query=query, user_role=role, limit=5)
            tool_data = results
            tool_status = "success"
            tool_history.append({
                "tool_name": "qdrant_semantic_search",
                "arguments": {"query": query},
                "status": "success",
                "outcome": results
            })
            trace_steps.append({
                "node": agent_name,
                "action": "Executed tool: qdrant_semantic_search",
                "confidence": 1.0,
                "reasoning": "Semantic search retrieval",
                "timestamp": str(datetime.utcnow()),
                "latency": 0.0
            })
        except Exception as e:
            tool_status = "error"
            tool_data = {"error": str(e)}
            tool_history.append({
                "tool_name": "qdrant_semantic_search",
                "arguments": {"query": query},
                "status": "error",
                "outcome": str(e)
            })
    elif agent_def.tools:
        # Run up to 3 sequential tool executions
        for step in range(3):
            tool_select_prompt = (
                f"You are the tool execution planner for the Yottaflex {agent_def.display_name}.\n"
                f"Your target role is {role}. The logged-in employee is '{logged_in_name}'.\n"
                "Review the user query and the outcomes of previously run tools, then choose the NEXT tool to execute.\n"
                "If you have enough information to completely answer the query, or if no further tools will help, select 'null' for tool_name.\n\n"
                f"Allowed Tools: {agent_def.tools}\n"
                f"User Query: {query}\n\n"
                f"Previous Tool Executions History:\n{json.dumps(tool_history, indent=2)}\n\n"
                "Output ONLY a JSON object of this structure:\n"
                "{\n"
                "  \"tool_name\": \"name_of_the_tool_or_null\",\n"
                "  \"arguments\": {\"arg_name\": \"value\"}\n"
                "}"
            )
            try:
                res = await call_model([SystemMessage(content=tool_select_prompt)], settings.FAST_MODEL, json_mode=True)
                decision = json.loads(res["text"].strip())
                selected_tool = decision.get("tool_name")
                arguments = decision.get("arguments", {})

                if not selected_tool or selected_tool == "null" or selected_tool not in agent_def.tools or selected_tool not in TOOL_FUNCTIONS:
                    break  # Exit loop if no tool selected or invalid

                # Strict RBAC override for Employee Agent
                if agent_name == "employee_agent" and role == "Employee":
                    for key in ["employee_id_or_name", "target_name", "employee_name"]:
                        if key in arguments:
                            arguments[key] = logged_in_name

                # Execute target tool
                step_start = time.time()
                tool_fn = TOOL_FUNCTIONS[selected_tool]
                async with SessionLocal() as db:
                    res_tool = await tool_fn(db, **arguments)
                    
                status = "success" if res_tool.get("status") != "error" else "error"
                tool_history.append({
                    "tool_name": selected_tool,
                    "arguments": arguments,
                    "status": status,
                    "outcome": res_tool
                })
                trace_steps.append({
                    "node": agent_name,
                    "action": f"Executed tool: {selected_tool}",
                    "confidence": 1.0,
                    "reasoning": f"Step {step+1} tool execution",
                    "timestamp": str(datetime.utcnow()),
                    "latency": time.time() - step_start
                })
            except Exception as e:
                print(f"Tool call execution step {step} failed: {e}")
                tool_history.append({
                    "tool_name": selected_tool if 'selected_tool' in locals() else "unknown",
                    "arguments": arguments if 'arguments' in locals() else {},
                    "status": "error",
                    "outcome": {"error": str(e)}
                })
                break

    # Determine final outcome status and last tool details
    if tool_history:
        tool_used = ", ".join([h["tool_name"] for h in tool_history])
        tool_status = "success" if all(h["status"] == "success" for h in tool_history) else "error"
        tool_data = tool_history[-1]["outcome"] if len(tool_history) == 1 else {"history": tool_history}
    else:
        tool_used = None
        tool_status = "none"
        tool_data = None

    # 3. LLM Response Synthesis and Confidence Score Verification
    system_prompt = (
        f"You are the Yottaflex {agent_def.display_name}.\n"
        f"Capabilities: {agent_def.capabilities}\n"
        "Draft a professional, clear response to the user query based on the executed tool results and retrieved context.\n"
        "Strict rules:\n"
        "1. Only reference facts directly present in the context. Do not invent or extrapolate numbers, dates, or names.\n"
        "2. Estimate a confidence score from 0.0 to 1.0 that your response is correct and free of hallucinations.\n"
        "3. Provide structured citations pointing to source databases or documents if applicable.\n"
        "   - For knowledge agent document references, specify \"chunk_id\" (using the chunk_index integer) and \"source\" (using the filename).\n\n"
        "Output strictly in JSON format matching this schema:\n"
        "{\n"
        "  \"response\": \"markdown formatted response text\",\n"
        "  \"confidence\": 0.95,\n"
        "  \"reasoning\": \"brief reasoning for confidence score\",\n"
        "  \"citations\": [\n"
        "    {\"source\": \"source name (e.g. employee_profile, handbook.pdf)\", \"chunk_id\": 0, \"confidence\": 1.0}\n"
        "  ]\n"
        "}"
    )

    user_prompt = (
        f"User Query: {query}\n"
        f"Logged-in User Identity: {logged_in_name} ({role})\n"
        f"Executed Tool(s): {tool_used}\n"
        f"Tool Execution Outcomes:\n{json.dumps(tool_history if tool_history else tool_data, indent=2)}"
    )

    confidence_score = 0.0
    reasoning = "Failed to synthesize"
    citations = []
    response_text = ""

    # Primary call to fast model
    try:
        synthesis_res = await call_model([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ], settings.FAST_MODEL, json_mode=True)
        
        parsed_synth = json.loads(synthesis_res["text"])
        response_text = parsed_synth.get("response", "")
        confidence_score = float(parsed_synth.get("confidence", 0.85))
        reasoning = parsed_synth.get("reasoning", "Synthesized response")
        citations = parsed_synth.get("citations", [])
    except Exception as e:
        print(f"Primary synthesis call failed: {e}")

    # 4. Fallback logic: Execute reasoning model if confidence is low (< 0.70)
    if confidence_score < 0.70 or not response_text:
        print(f"Confidence score {confidence_score} is below threshold. Invoking fallback reasoning model.")
        try:
            synthesis_res = await call_model([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ], settings.REASONING_MODEL, json_mode=True)
            
            parsed_synth = json.loads(synthesis_res["text"])
            response_text = parsed_synth.get("response", response_text)
            confidence_score = float(parsed_synth.get("confidence", confidence_score))
            reasoning = parsed_synth.get("reasoning", reasoning) + " (via Fallback Model)"
            citations = parsed_synth.get("citations", citations)
        except Exception as fallback_err:
            print(f"Fallback model failed: {fallback_err}")
            if not response_text:
                response_text = "I encountered an issue retrieving high-confidence information to answer your request."
                confidence_score = 0.10
                reasoning = f"Critical error during synthesis: {fallback_err}"

    latency = time.time() - start_time
    
    # Consolidate all step latencies and trace data
    final_trace = trace_steps if trace_steps else [{
        "node": agent_name,
        "action": "Direct response synthesis",
        "confidence": confidence_score,
        "reasoning": reasoning,
        "timestamp": str(datetime.utcnow()),
        "latency": latency
    }]

    # Return state update dictionary
    return {
        "messages": [AIMessage(content=response_text)],
        "agent_outputs": [{
            "agent": agent_name,
            "response": response_text,
            "confidence": confidence_score,
            "reasoning": reasoning,
            "tool_used": tool_used,
            "tool_status": tool_status
        }],
        "agent_confidence": {agent_name: confidence_score},
        "agent_trace": final_trace,
        "citations": citations,
        "current_agent": agent_name,
        "next_step": "verification"
    }

# Specialist Node Wrappers

async def employee_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Employee Agent Node ---")
    return await run_agentic_node("employee_agent", state)

async def hr_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- HR Agent Node ---")
    return await run_agentic_node("hr_agent", state)

async def manager_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Manager Agent Node ---")
    return await run_agentic_node("manager_agent", state)

async def process_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Process Agent Node ---")
    return await run_agentic_node("process_agent", state)

async def executive_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Executive Agent Node ---")
    return await run_agentic_node("executive_agent", state)

async def knowledge_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Knowledge Agent Node ---")
    return await run_agentic_node("knowledge_agent", state)

async def resource_optimization_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Resource Optimization Agent Node ---")
    return await run_agentic_node("resource_optimization_agent", state)

async def skill_intelligence_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Skill Intelligence Agent Node ---")
    return await run_agentic_node("skill_intelligence_agent", state)

async def project_risk_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Project Risk Agent Node ---")
    return await run_agentic_node("project_risk_agent", state)

async def workforce_planning_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Workforce Planning Agent Node ---")
    return await run_agentic_node("workforce_planning_agent", state)

async def executive_insights_agent_node(state: AgentState) -> Dict[str, Any]:
    print("--- Executive Insights Agent Node ---")
    return await run_agentic_node("executive_insights_agent", state)
