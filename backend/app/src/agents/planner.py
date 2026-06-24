import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings
from src.agents.registry import AGENT_REGISTRY

async def run_planner_agent(
    user_query: str,
    intent: str,
    selected_agents: List[str],
    memory_context: str
) -> Dict[str, Any]:
    """
    Planner Agent that understands objectives, references memory context,
    and generates a structured execution plan with agent + tool assignments and dependencies.

    Acts as the workflow orchestrator by defining which agents run, what tools they should
    invoke, and whether steps can execute in parallel or must be sequential.
    """
    # Build agent capability context for the LLM
    agent_context_parts = []
    for agent_name in selected_agents:
        agent_def = AGENT_REGISTRY.get(agent_name)
        if agent_def:
            tools_str = ", ".join(agent_def.tools[:8]) if agent_def.tools else "none"
            caps_str = ", ".join(agent_def.capabilities)
            agent_context_parts.append(
                f"- {agent_name}: {agent_def.description}\n"
                f"  Tools: [{tools_str}]\n"
                f"  Capabilities: [{caps_str}]"
            )

    agents_detail = "\n".join(agent_context_parts) if agent_context_parts else "No agent details available."

    # Full registry for cross-reference
    all_agents_summary = "\n".join([
        f"- {a.name}: {a.description}"
        for a in AGENT_REGISTRY.values()
    ])

    system_prompt = (
        "You are the Lead Yottaflex Workforce OS Planner Agent and Workflow Orchestrator.\n"
        "Your job is to analyze the user's query, the selected agents from the supervisor, and memory context, "
        "then generate a structured, parallel-execution-friendly plan.\n\n"
        f"Selected Agents (from Supervisor):\n{agents_detail}\n\n"
        f"Full Agent Registry (for reference):\n{all_agents_summary}\n\n"
        "Output must be strictly in JSON matching this schema:\n"
        "{\n"
        '  "goal": "One-line summary of what needs to be accomplished",\n'
        '  "execution_plan": "A detailed description of what needs to be done and why",\n'
        '  "plan_steps": [\n'
        "    {\n"
        '      "agent": "agent_name_from_selected_list",\n'
        '      "tool": "optional_specific_tool_name_or_null",\n'
        '      "description": "Brief step description",\n'
        '      "depends_on": []  // list of step indices (0-based) this step depends on, empty = parallel\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Each step MUST use an agent from the selected_agents list.\n"
        "- If multiple agents are selected, create one step per agent minimum.\n"
        "- Steps with empty depends_on arrays will execute in parallel.\n"
        "- The tool field is optional — agents will auto-select tools if null.\n"
        "- Keep plans concise: 1-4 steps maximum."
    )

    user_message_content = (
        f"User Query: {user_query}\n"
        f"Intent: {intent}\n"
        f"Selected Agents: {json.dumps(selected_agents)}\n\n"
        f"Retrieved Memory Context:\n{memory_context}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message_content)
    ]

    res = await call_model(messages, settings.REASONING_MODEL, json_mode=True)

    try:
        parsed = json.loads(res["text"])
        plan_steps = parsed.get("plan_steps", [])

        # Validate and normalize steps
        validated_steps = []
        for step in plan_steps:
            if isinstance(step, dict) and "agent" in step:
                # Ensure agent is in the selected list
                if step["agent"] in selected_agents or step["agent"] in AGENT_REGISTRY:
                    validated_steps.append({
                        "agent": step["agent"],
                        "tool": step.get("tool"),
                        "description": step.get("description", "Execute agent operations"),
                        "depends_on": step.get("depends_on", [])
                    })
            elif isinstance(step, str):
                validated_steps.append({
                    "agent": selected_agents[0],
                    "tool": None,
                    "description": step,
                    "depends_on": []
                })

        # Ensure every selected agent has at least one step
        agents_with_steps = {s["agent"] for s in validated_steps}
        for agent_name in selected_agents:
            if agent_name not in agents_with_steps:
                validated_steps.append({
                    "agent": agent_name,
                    "tool": None,
                    "description": f"Execute {agent_name} operations for query",
                    "depends_on": []
                })

        if not validated_steps:
            validated_steps = [{
                "agent": selected_agents[0] if selected_agents else "employee_agent",
                "tool": None,
                "description": "Execute target agent actions",
                "depends_on": []
            }]

        return {
            "goal": parsed.get("goal", user_query),
            "execution_plan": parsed.get("execution_plan", "Run specialist tools to resolve the query."),
            "plan_steps": validated_steps,
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
    except Exception as e:
        print(f"Failed to parse plan JSON: {e}")
        # Fallback: create a step per selected agent
        fallback_steps = [
            {
                "agent": agent_name,
                "tool": None,
                "description": f"Execute operations for intent {intent}.",
                "depends_on": []
            }
            for agent_name in (selected_agents if selected_agents else ["employee_agent"])
        ]

        return {
            "goal": user_query,
            "execution_plan": f"Execute fallback plan for intent {intent}.",
            "plan_steps": fallback_steps,
            "metrics": {
                "selected_model": res["model"],
                "latency": res["latency"],
                "input_tokens": res["input_tokens"],
                "output_tokens": res["output_tokens"],
                "cost": res["cost"]
            }
        }
