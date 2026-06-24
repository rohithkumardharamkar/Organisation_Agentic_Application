from typing import Dict, Any, List

class AgentDefinition:
    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        capabilities: List[str],
        tools: List[str],
        permissions: List[str],
        confidence_threshold: float = 0.70
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.capabilities = capabilities
        self.tools = tools
        self.permissions = permissions
        self.confidence_threshold = confidence_threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "permissions": self.permissions,
            "confidence_threshold": self.confidence_threshold
        }

AGENT_REGISTRY: Dict[str, AgentDefinition] = {
    "employee_agent": AgentDefinition(
        name="employee_agent",
        display_name="Employee Self-Service Agent",
        description="Handles self-service queries for individual employees, including personal profiles, locations, joining dates, leave balances, attendance, and timesheets.",
        capabilities=["Profile summary retrieval", "Leave balance lookup", "Attendance overview", "Timesheet logging history"],
        tools=[
            "employee_intelligence_tool",
            "get_employee_profile",
            "get_leave_balance",
            "get_attendance_summary",
            "get_timesheet_status",
            "get_salary_slip"
        ],
        permissions=["Employee", "HR", "Reporting Manager", "Process Engineer"]
    ),
    "hr_agent": AgentDefinition(
        name="hr_agent",
        display_name="Human Resources Operations Agent",
        description="Manages HR administrative actions: updating profiles, filing leaves, viewing salary slips, posting job openings, registering candidates, and managing policies.",
        capabilities=["Leave submission", "Salary slip lookup", "Job recruitment actions", "Policy documentation lookup"],
        tools=[
            "get_employee_profile",
            "get_leave_balance",
            "apply_leave",
            "get_attendance_summary",
            "submit_timesheet",
            "get_timesheet_status",
            "get_salary_slip",
            "search_policy",
            "create_ticket",
            "get_ticket_status",
            "get_job_openings",
            "apply_for_job",
            "send_notification",
            "save_memory",
            "retrieve_memory",
            "leave_intelligence_tool"
        ],
        permissions=["HR"]
    ),
    "manager_agent": AgentDefinition(
        name="manager_agent",
        display_name="Manager Operations Agent",
        description="Aids reporting managers in reviewing leaves, approving timesheets, checking team compliance levels, and managing departmental assignments.",
        capabilities=["Leave review", "Timesheet compliance analysis", "Team management"],
        tools=[
            "leave_intelligence_tool",
            "timesheet_compliance_tool"
        ],
        permissions=["Reporting Manager", "HR"]
    ),
    "process_agent": AgentDefinition(
        name="process_agent",
        display_name="Process Engineering Agent",
        description="Generates, inspects, and analyzes sprint process reports, listing achievements, risks, requirements status, and future playbook improvements.",
        capabilities=["Sprint report analysis", "Process bottleneck detection", "Achievement logging"],
        tools=[
            "generate_process_report_tool"
        ],
        permissions=["Process Engineer", "Reporting Manager"]
    ),
    "executive_agent": AgentDefinition(
        name="executive_agent",
        display_name="Executive Portfolio Agent",
        description="Creates high-level C-Suite summaries detailing all project parameters: budgets, total headcount, client distributions, and compliance targets.",
        capabilities=["Portfolio health summaries", "Budget overview reports", "Staffing index analysis"],
        tools=[
            "executive_summary_tool"
        ],
        permissions=["HR", "Reporting Manager"]
    ),
    "knowledge_agent": AgentDefinition(
        name="knowledge_agent",
        display_name="Organizational Knowledge RAG Agent",
        description="Answers general questions about remote policies, handbook guidelines, IT rules, security parameters, and training standards using document embeddings.",
        capabilities=["Policy search", "Handbook reading", "Semantic document RAG"],
        tools=[
            "search_policy"
        ],
        permissions=["Employee", "HR", "Reporting Manager", "Process Engineer"]
    ),
    "resource_optimization_agent": AgentDefinition(
        name="resource_optimization_agent",
        display_name="Resource Optimization Agent",
        description="Finds resource allocations, identifies idle bench assets, recommends engineers for project demands, and measures skill overlaps.",
        capabilities=["Bench optimization", "Resource scheduling", "Allocation balancing"],
        tools=[
            "bench_optimization",
            "employee_skill_lookup",
            "availability_lookup",
            "allocation_lookup",
            "project_requirement_lookup",
            "experience_lookup",
            "recommend_resources"
        ],
        permissions=["HR", "Reporting Manager"]
    ),
    "skill_intelligence_agent": AgentDefinition(
        name="skill_intelligence_agent",
        display_name="Skill Intelligence Agent",
        description="Analyzes skill levels across the company, performs project skill gap audits, and recommends upskilling and learning pathways.",
        capabilities=["Skill gap auditing", "Upskilling pathway suggestions", "Certifications matching"],
        tools=[
            "skill_gap_analysis_tool",
            "learning_recommendation_tool",
            "certification_recommendation_tool",
            "project_skill_tool",
            "employee_skill_tool",
            "recommend_upskilling",
            "analyze_skill_gap"
        ],
        permissions=["HR", "Reporting Manager"]
    ),
    "project_risk_agent": AgentDefinition(
        name="project_risk_agent",
        display_name="Project Risk Diagnostics Agent",
        description="Calculates risk levels, tracks timesheet SLA compliance, detects blockers, and projects budget burn rate warnings.",
        capabilities=["Risk scoring", "Timesheet SLA checks", "Blocker logging", "Burn rate prediction"],
        tools=[
            "timesheet_compliance_tool",
            "resource_availability_tool",
            "blocker_tool",
            "risk_scoring_tool",
            "project_health_tool",
            "predict_project_risk"
        ],
        permissions=["Reporting Manager", "HR"]
    ),
    "workforce_planning_agent": AgentDefinition(
        name="workforce_planning_agent",
        display_name="Workforce Capacity Planner",
        description="Models future headcount requirements, predicts skills demand, generates recruitment forecasts, and audits single-point-of-failure skills.",
        capabilities=["Headcount forecasting", "Recruitment demand modeling", "Capacity mapping"],
        tools=[
            "resource_forecast_tool",
            "project_demand_tool",
            "skill_forecast_tool",
            "hiring_forecast_tool",
            "bench_optimization"
        ],
        permissions=["HR", "Reporting Manager"]
    ),
    "executive_insights_agent": AgentDefinition(
        name="executive_insights_agent",
        display_name="Executive Insights Agent",
        description="Extracts deep corporate insights: organization health index, project cost analyses, RAG search analytics, and successor planning indicators.",
        capabilities=["Health index modeling", "Department cost analysis", "Succession planning"],
        tools=[
            "organization_health_tool",
            "project_portfolio_tool",
            "skill_gap_tool",
            "resource_utilization_tool",
            "executive_summary_tool"
        ],
        permissions=["HR"]
    )
}


# --- Dynamic Discovery Helpers ---

def get_agents_for_role(role: str) -> List[AgentDefinition]:
    """Return all agents accessible by a given user role."""
    return [a for a in AGENT_REGISTRY.values() if role in a.permissions]


def get_agent_by_capability(keyword: str) -> List[AgentDefinition]:
    """Search agents whose capabilities or description match a keyword."""
    keyword_lower = keyword.lower()
    results = []
    for agent_def in AGENT_REGISTRY.values():
        if keyword_lower in agent_def.description.lower():
            results.append(agent_def)
            continue
        for cap in agent_def.capabilities:
            if keyword_lower in cap.lower():
                results.append(agent_def)
                break
    return results


def get_registry_summary(role: str = None) -> str:
    """
    Generate a compact agent summary string suitable for LLM prompts.
    If role is provided, only include agents accessible to that role.
    """
    agents = get_agents_for_role(role) if role else list(AGENT_REGISTRY.values())
    lines = []
    for i, a in enumerate(agents, 1):
        caps = ", ".join(a.capabilities[:3])
        lines.append(f"{i}. {a.name}: {a.description} Capabilities: [{caps}]")
    return "\n".join(lines)
