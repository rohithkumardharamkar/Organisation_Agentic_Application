import time
import hashlib
import json
import httpx
import contextvars
import asyncio

stream_callback_var = contextvars.ContextVar("stream_callback", default=None)
from typing import Dict, Any, List, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from src.core.config import settings

# Global simple cache for Token Optimization
# In production, this can be backed by Redis or SQLite
_RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}
_TOOL_CACHE: Dict[str, Dict[str, Any]] = {}

def get_cache_key(messages: List[BaseMessage], model: str) -> str:
    """Generate a hash of the messages and model for caching."""
    serialized = []
    for m in messages:
        role = "system" if isinstance(m, SystemMessage) else "user" if isinstance(m, HumanMessage) else "assistant"
        serialized.append(f"{role}:{m.content}")
    content_str = "\n".join(serialized) + f"\nmodel:{model}"
    return hashlib.sha256(content_str.encode("utf-8")).hexdigest()

def estimate_tokens(text: str) -> int:
    """Fall back token estimator: ~1.3 tokens per word."""
    return int(len(text.split()) * 1.3) + 4

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost estimate in USD based on Groq pricing."""
    # Pricing per 1M tokens
    pricing = {
        settings.FAST_MODEL: {"input": 0.05, "output": 0.08},
        settings.REASONING_MODEL: {"input": 0.59, "output": 0.79},
        settings.FALLBACK_MODEL: {"input": 0.20, "output": 0.20},
        "mock": {"input": 0.0, "output": 0.0}
    }
    rates = pricing.get(model, {"input": 0.10, "output": 0.10})
    cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    return cost

async def get_mock_response(messages: List[BaseMessage], model: str) -> Dict[str, Any]:
    """Fallback high-fidelity mock engine when Groq API keys are not provided."""
    sys_prompt = ""
    user_query = ""
    for m in messages:
        if isinstance(m, SystemMessage):
            sys_prompt += m.content
        elif isinstance(m, HumanMessage):
            user_query += m.content
            
    content = ""
    query_lower = user_query.lower()
    sys_lower = sys_prompt.lower()
    
    if "lead yottaflex workforce os supervisor" in sys_lower:
        intent = "executive_summary"
        target = "executive_agent"
        risk = "low"
        
        if "bench" in query_lower or "underutilized" in query_lower:
            intent = "resource_optimization"
            target = "resource_optimization_agent"
        elif "leave" in query_lower or "absent" in query_lower:
            intent = "hr_queries"
            target = "hr_agent"
        elif "project" in query_lower or "delay" in query_lower or "risk" in query_lower:
            intent = "project_risk"
            target = "project_risk_agent"
        elif "timesheet" in query_lower or "compliance" in query_lower:
            intent = "manager_queries"
            target = "manager_agent"
        elif "skill" in query_lower or "react" in query_lower:
            intent = "skill_intelligence"
            target = "skill_intelligence_agent"
        elif "hire" in query_lower or "forecast" in query_lower or "capacity" in query_lower:
            intent = "workforce_planning"
            target = "workforce_planning_agent"
        elif "health" in query_lower or "insights" in query_lower or "c-suite" in query_lower:
            intent = "executive_insights"
            target = "executive_insights_agent"
        elif "policy" in query_lower or "handbook" in query_lower or "sop" in query_lower:
            intent = "knowledge_retrieval"
            target = "knowledge_agent"
        elif "evaluate" in query_lower or "review" in query_lower or "performance" in query_lower:
            intent = "employee_queries"
            target = "employee_agent"
            risk = "medium"
        elif "sprint" in query_lower or "process" in query_lower:
            intent = "process_engineering"
            target = "process_agent"
            
        content = json.dumps({
            "intent": intent,
            "risk_level": risk,
            "target_agent": target,
            "reasoning": f"Query classified as {intent} with risk {risk}.",
            "plan": f"1. Run tool, 2. Synthesize {intent} response"
        })
        
    # 2. Resource Agent Mock
    elif "resource intelligence agent" in sys_lower:
        content = (
            "### 📊 Workforce Resource Optimization Report\n\n"
            "- **Overview**: There are currently 5 underutilized employees on the bench.\n"
            "- **Bench Employees**:\n"
            "  1. Amit Kumar (Engineering) - 0% utilized\n"
            "  2. Neha Patel (Marketing) - 0% utilized\n"
            "  3. Priya Singh (Design) - 0% utilized\n"
            "- **Over-allocated Employees**: None\n"
            "- **Recommendations**: Reallocate Amit Kumar to the upcoming 'Yottaflex AI Migration' project to optimize resource usage."
        )
        
    # 3. Leave Agent Mock
    elif "leave impact intelligence agent" in sys_lower:
        content = (
            "### 🌴 Leave Impact Report\n\n"
            "- **Pending Leaves**: 2 leaves awaiting approval.\n"
            "- **Approved Leaves**: Rohit Sharma is on leave from June 25 to June 30. This may impact 'Enterprise Dashboard V2' delivery.\n"
            "- **Recommended Actions**: Assign timesheet oversight to Amit Kumar during the absence."
        )
        
    # 4. Project Health Agent Mock
    elif "project health intelligence agent" in sys_lower:
        content = (
            "### 📁 Project Portfolio Health Report\n\n"
            "- **Overview**: Out of 10 active projects, 8 are on track, and 2 are 'At Risk'.\n"
            "- **At Risk Projects**:\n"
            "  - *Sales CRM Overhaul*: Burn rate is 120% of budget.\n"
            "  - *Cloud Infrastructure Optimization*: Running 2 weeks behind schedule.\n"
            "- **Recommendations**: Reallocate bench developers to the Sales CRM project to balance delivery velocity."
        )
        
    # 5. Timesheet Compliance Agent Mock
    elif "timesheet compliance agent" in sys_lower:
        content = (
            "### 🕐 Timesheet Compliance Report\n\n"
            "- **Overall Compliance**: 88% (Warning status).\n"
            "- **Breakdown**:\n"
            "  - Submitted: 44\n"
            "  - Approved: 38\n"
            "  - Pending Approval: 6\n"
            "  - Draft: 4\n"
            "- **Non-compliant Employees**: Sanjay Gupta, Pooja Das.\n"
            "- **Recommended Actions**: Send automated reminders to non-compliant employees to submit drafts."
        )
        
    # 6. Skill Intelligence Agent Mock
    elif "talent & skill intelligence agent" in sys_lower:
        content = (
            "### 🧠 Talent & Skill Intelligence Report\n\n"
            "- **Overview**: Organization possesses 16 unique skills across 50 employees.\n"
            "- **Top Skills**: Python (18 employees), React (15 employees), SQL (12 employees).\n"
            "- **Critical Risk (Single point of failure)**: Salesforce (only 1 expert: Divya Rao).\n"
            "- **Recommendations**: Cross-train at least two mid-level engineers in Salesforce integration."
        )
        
    # 7. Executive Agent Mock
    elif "executive intelligence agent" in sys_lower:
        content = (
            "### 🏢 Executive Workforce Intelligence Brief\n\n"
            "1. **Workforce Overview**: 50 active employees. 5 currently on the bench.\n"
            "2. **Project Portfolio Health**: 10 projects. 2 at risk ('Sales CRM Overhaul', 'Cloud Infrastructure Optimization').\n"
            "3. **Timesheet Compliance**: 88% compliance rate. 2 employees non-compliant.\n"
            "4. **Leave Impact**: 2 pending leaves, minimal immediate roadmap disruption.\n"
            "5. **Skill Intelligence**: Salesforce identified as critical single-point-of-failure risk.\n"
            "6. **Top Priority Actions**: Approve John Doe reallocation to Project Beta; initiate Salesforce cross-training."
        )
        
    # 8. Performance Agent Mock
    elif "performance evaluation agent" in sys_lower:
        content = (
            "### 📋 Employee Performance Evaluation\n\n"
            "- **Employee Name**: Rahul Sharma\n"
            "- **Department**: Engineering (Senior Software Engineer)\n"
            "- **Timesheet Compliance**: 100% submission rate.\n"
            "- **Project Contribution**: Lead developer on 'Yottaflex AI Migration'. Burned 120 hours out of 120 planned.\n"
            "- **Skill Profile**: Python (Expert), AWS (Expert), SQL (Intermediate).\n"
            "- **Overall Assessment**: Outstanding performance. Exceeds expectations in technical leadership and project delivery."
        )
        
    # 9. Process Agent Mock
    elif "process engineering intelligence agent" in sys_lower:
        content = (
            "### 📊 Process Report: Yottaflex AI Migration\n\n"
            "- ✅ **Key Achievements**: Completed migration of database schemas; initial LangGraph workflow setup.\n"
            "- ⚠️ **Risks Identified**: Groq rate-limiting could affect response times.\n"
            "- ❌ **Missing Requirements**: Clear guidelines on fallback Ollama endpoints.\n"
            "- 🚀 **Future Improvements**: Optimize SQLite checkpointer state reads.\n"
            "- 💡 **Recommended Next Steps**: Implement streaming API response to decrease perceived latency."
        )
        
    # 10. QA / Verification Agent Mock
    elif "verification agent" in sys_lower or "qa" in sys_lower:
        if "e2e" in sys_lower or "final output" in sys_lower:
            content = json.dumps({
                "passed": True,
                "details": "The response matches the original query and is safe."
            })
        else:
            content = json.dumps({
                "passed": True,
                "reason": "Plan goals matches executed tools and database results."
            })
            
    # 11. Response Node / General Mock Response
    else:
        # Check if there are tool outcomes in prompt and serialize a response
        if "tool_results" in query_lower or "outcomes:" in query_lower:
            content = "I have successfully completed the requested workforce operations. The database records have been verified."
        else:
            content = "I have processed your request. Please let me know how I can assist you further with Workforce OS."

    # Return structured simulation
    in_tok = estimate_tokens(sys_prompt + user_query)
    out_tok = estimate_tokens(content)
    
    return {
        "text": content,
        "model": f"{model}-mock",
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost": 0.0,
        "latency": 0.05,
        "cached": False
    }

# Global Circuit Breaker State
_CIRCUIT_STATE: Dict[str, Dict[str, Any]] = {}
FAILURE_THRESHOLD = 3
COOLDOWN_PERIOD = 30.0  # seconds

def check_circuit_breaker(model: str) -> str:
    """Check the circuit state for a model and return 'open', 'closed', or 'half-open'."""
    if model not in _CIRCUIT_STATE:
        _CIRCUIT_STATE[model] = {"state": "closed", "failures": 0, "last_failure_time": 0.0}
        return "closed"
        
    state_info = _CIRCUIT_STATE[model]
    if state_info["state"] == "open":
        # Check cooldown
        if time.time() - state_info["last_failure_time"] > COOLDOWN_PERIOD:
            state_info["state"] = "half-open"
            print(f"[CIRCUIT BREAKER] Model {model} circuit entered half-open state.")
            return "half-open"
        return "open"
    return state_info["state"]

def record_success(model: str):
    """Record a successful model invocation to close/reset the circuit."""
    if model in _CIRCUIT_STATE:
        state_info = _CIRCUIT_STATE[model]
        state_info["state"] = "closed"
        state_info["failures"] = 0
        state_info["last_failure_time"] = 0.0

def record_failure(model: str):
    """Record a failure for the model, possibly tripping the circuit breaker."""
    if model not in _CIRCUIT_STATE:
        _CIRCUIT_STATE[model] = {"state": "closed", "failures": 0, "last_failure_time": 0.0}
    state_info = _CIRCUIT_STATE[model]
    state_info["failures"] += 1
    state_info["last_failure_time"] = time.time()
    if state_info["failures"] >= FAILURE_THRESHOLD:
        state_info["state"] = "open"
        print(f"[CIRCUIT BREAKER] Model {model} circuit TRIPPED to OPEN due to {state_info['failures']} consecutive failures.")


async def call_model(
    messages: List[BaseMessage],
    model: str,
    temperature: float = 0.0,
    json_mode: bool = False,
    stream_tokens: bool = False
) -> Dict[str, Any]:
    """
    Call Groq Model with circuit breaker, failover logic, latency monitoring, cost calculation, and response caching.
    """
    cache_key = get_cache_key(messages, model)
    if cache_key in _RESPONSE_CACHE:
        cached_res = _RESPONSE_CACHE[cache_key].copy()
        cached_res["cached"] = True
        
        # If streaming is requested and we have cached content, stream it out
        callback = stream_callback_var.get()
        if stream_tokens and callback:
            text = cached_res["text"]
            chunk_size = 8
            for i in range(0, len(text), chunk_size):
                await callback(text[i:i+chunk_size])
                await asyncio.sleep(0.01)
                
        return cached_res
        
    start_time = time.time()
    
    # Check for empty API Key (force mock)
    if not settings.GROQ_API_KEY:
        res = await get_mock_response(messages, model)
        callback = stream_callback_var.get()
        if stream_tokens and callback:
            text = res["text"]
            chunk_size = 8
            for i in range(0, len(text), chunk_size):
                await callback(text[i:i+chunk_size])
                await asyncio.sleep(0.01)
        _RESPONSE_CACHE[cache_key] = res
        return res

    # 1. Circuit Breaker Check
    circuit_state = check_circuit_breaker(model)
    if circuit_state == "open":
        print(f"[CIRCUIT BREAKER] Model {model} circuit is OPEN. Bypassing to fallback immediately.")
        raise RuntimeError(f"Circuit breaker is open for model {model}")
        
    try:
        # Initialize Groq client
        extra_args = {"response_format": {"type": "json_object"}} if json_mode else {}
        chat = ChatGroq(
            model_name=model,
            temperature=temperature,
            api_key=settings.GROQ_API_KEY,
            model_kwargs=extra_args,
            timeout=10.0
        )
        
        callback = stream_callback_var.get()
        if stream_tokens and callback:
            full_content = ""
            async for chunk in chat.astream(messages):
                content_chunk = chunk.content
                full_content += content_chunk
                await callback(content_chunk)
                
            latency = time.time() - start_time
            prompt_text = "".join([m.content for m in messages])
            input_tokens = estimate_tokens(prompt_text)
            output_tokens = estimate_tokens(full_content)
            cost = calculate_cost(model, input_tokens, output_tokens)
            
            res = {
                "text": full_content,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "latency": latency,
                "cached": False
            }
            record_success(model)
            _RESPONSE_CACHE[cache_key] = res
            return res
        else:
            response = await chat.ainvoke(messages)
            latency = time.time() - start_time
        
        # Retrieve token counts from response metadata
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
            usage = response.response_metadata["token_usage"]
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
        else:
            # Estimate if not provided
            prompt_text = "".join([m.content for m in messages])
            input_tokens = estimate_tokens(prompt_text)
            output_tokens = estimate_tokens(response.content)
            
        cost = calculate_cost(model, input_tokens, output_tokens)
        
        res = {
            "text": response.content,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "latency": latency,
            "cached": False
        }
        
        # Cache response
        record_success(model)
        _RESPONSE_CACHE[cache_key] = res
        return res
        
    except Exception as e:
        print(f"Error calling model {model}: {e}")
        record_failure(model)
        # Failover / Fallback logic: if they limit or error, use the local models
        if model in [settings.FAST_MODEL, settings.REASONING_MODEL]:
            print(f"Groq model {model} failed (rate limit or error). Attempting immediate local Ollama fallback...")
            local_res = await call_local_ollama(messages, temperature, json_mode)
            if local_res:
                callback = stream_callback_var.get()
                if stream_tokens and callback:
                    text = local_res["text"]
                    chunk_size = 8
                    for i in range(0, len(text), chunk_size):
                        await callback(text[i:i+chunk_size])
                        await asyncio.sleep(0.01)
                _RESPONSE_CACHE[cache_key] = local_res
                return local_res
                
        # If model is already something else, or if local Ollama failed, try other fallbacks
        if model != settings.FALLBACK_MODEL:
            print(f"Falling back to Groq fallback model {settings.FALLBACK_MODEL}...")
            try:
                res = await call_model(messages, settings.FALLBACK_MODEL, temperature, json_mode, stream_tokens=stream_tokens)
                _RESPONSE_CACHE[cache_key] = res
                return res
            except Exception as fe:
                print(f"Groq fallback model also failed: {fe}")
                
        # Last resort fallback: try local Ollama if not tried yet, then mock engine
        print("Attempting final local Ollama fallback...")
        local_res = await call_local_ollama(messages, temperature, json_mode)
        if local_res:
            callback = stream_callback_var.get()
            if stream_tokens and callback:
                text = local_res["text"]
                chunk_size = 8
                for i in range(0, len(text), chunk_size):
                    await callback(text[i:i+chunk_size])
                    await asyncio.sleep(0.01)
            _RESPONSE_CACHE[cache_key] = local_res
            return local_res
            
        print("All models failed. Returning mock engine response.")
        res = await get_mock_response(messages, model)
        callback = stream_callback_var.get()
        if stream_tokens and callback:
            text = res["text"]
            chunk_size = 8
            for i in range(0, len(text), chunk_size):
                await callback(text[i:i+chunk_size])
                await asyncio.sleep(0.01)
        _RESPONSE_CACHE[cache_key] = res
        return res


async def get_local_ollama_model() -> Optional[str]:
    """
    Discover available models from local and network Ollama instances.
    Tries both localhost and the LAN server. Returns the best available model name.
    """
    # Priority list of preferred models for general-purpose tasks
    preferred_models = [
        "qwen3:32b", "qwen3-coder:30b", "qwen2.5-coder:14b",
        "gemma4:e2b", "llama3.2:latest", "llama3:latest",
        "qwen2.5:3b", "phi3:latest", "gemma3:270m"
    ]
    
    ollama_urls = [settings.OLLAMA_URL, settings.LOCAL_OLLAMA_URL]
    
    for url in ollama_urls:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{url}/api/tags", timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json()
                    available = [m["name"] for m in data.get("models", [])]
                    if not available:
                        continue
                    # Try preferred models first
                    for pref in preferred_models:
                        if pref in available:
                            return f"{url}|{pref}"
                        # Partial match (e.g. "qwen3" matches "qwen3:32b")
                        for avail in available:
                            if avail.startswith(pref.split(":")[0]):
                                return f"{url}|{avail}"
                    # Return first available model
                    return f"{url}|{available[0]}"
        except Exception as e:
            print(f"Failed to discover models at {url}: {e}")
    
    return None


async def call_local_ollama(
    messages: List[BaseMessage],
    temperature: float = 0.0,
    json_mode: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Call a local Ollama model as fallback when Groq cloud models fail.
    Discovers available models from both localhost and network Ollama instances.
    """
    discovery = await get_local_ollama_model()
    if not discovery:
        print("No local Ollama models discovered.")
        return None
    
    url, model_name = discovery.split("|", 1)
    print(f"Using local Ollama fallback: {model_name} at {url}")
    
    # Convert LangChain messages to Ollama format
    ollama_messages = []
    for m in messages:
        if isinstance(m, SystemMessage):
            ollama_messages.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            ollama_messages.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            ollama_messages.append({"role": "assistant", "content": m.content})
    
    payload = {
        "model": model_name,
        "messages": ollama_messages,
        "options": {"temperature": temperature},
        "stream": False
    }
    if json_mode:
        payload["format"] = "json"
    
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{url}/api/chat",
                json=payload,
                timeout=5.0
            )
            if resp.status_code != 200:
                print(f"Ollama API returned status {resp.status_code}")
                return None
            
            result = resp.json()
            content = result["message"]["content"]
            latency = time.time() - start_time
            
            prompt_text = "".join([m.content for m in messages])
            input_tokens = estimate_tokens(prompt_text)
            output_tokens = estimate_tokens(content)
            
            return {
                "text": content,
                "model": f"{model_name}-ollama-fallback",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": 0.0,
                "latency": latency,
                "cached": False
            }
    except Exception as e:
        print(f"Local Ollama call failed: {e}")
        return None
