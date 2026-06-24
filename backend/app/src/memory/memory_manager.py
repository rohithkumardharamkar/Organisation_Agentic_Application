from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.router import call_model
from src.core.config import settings

class MemoryManager:
    @staticmethod
    async def select_sources(query: str, user_role: str) -> List[str]:
        """
        Dynamically analyzes the user query to choose relevant memory modules,
        preventing token overflow and unnecessary context window bloat.
        """
        query_lower = query.lower()
        
        # 1. Simple heuristic fallback to save latency on greeting or short queries
        if len(query) < 15 and any(g in query_lower for g in ["hello", "hi", "hey", "thanks", "thank you"]):
            return ["summary"]
            
        # 2. Use a fast LLM call to classify query intent and pick optimal memory sources
        system_prompt = (
            "You are the memory manager for the Yottaflex Workforce OS.\n"
            "Identify which memory categories are required to answer the user query.\n"
            "Categories:\n"
            "- 'summary': High-level profile/session summary (always relevant for context).\n"
            "- 'entities': Personal context (location, join date, name, my projects, my timesheets, etc.).\n"
            "- 'episodic': Past user commands, historical conversational interactions, or explicit notes to remember.\n"
            "- 'vector': General organizational policy documents, handbook guidelines, IT FAQs, or process standard PDFs.\n"
            "- 'lessons': Past mistakes, reflections on failures, or safety constraints from reflection logs.\n\n"
            "Respond ONLY with a JSON list of categories. Example: [\"summary\", \"entities\"]"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: '{query}'\nUser Role: {user_role}")
        ]
        
        try:
            res = await call_model(messages, model=settings.FAST_MODEL, json_mode=True)
            import json
            sources = json.loads(res["text"].strip())
            if isinstance(sources, list) and len(sources) > 0:
                # Ensure 'summary' is always included as a baseline context
                if "summary" not in sources:
                    sources.append("summary")
                return [s for s in sources if s in ["summary", "entities", "episodic", "vector", "lessons"]]
        except Exception as e:
            print(f"MemoryManager LLM selection failed: {e}. Falling back to all.")
            
        # 3. Default fallback: select all sources
        return ["summary", "entities", "episodic", "vector", "lessons"]

    @staticmethod
    async def compress_context(context_text: str, max_words: int = 400) -> str:
        """
        Compresses/summarizes long context strings if they exceed a certain length
        to prevent context window overflow.
        """
        if not context_text or len(context_text.split()) < max_words:
            return context_text
            
        system_prompt = (
            "You are an AI context compression assistant.\n"
            "Summarize the following context details into a concise list of key facts, "
            "preserving all names, metrics, and quantitative details. Do not lose key numeric values."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context to compress:\n{context_text}")
        ]
        
        try:
            res = await call_model(messages, model=settings.FAST_MODEL)
            return res["text"]
        except Exception as e:
            print(f"Memory compression failed: {e}")
            return context_text[:max_words * 5]  # Rough character cutoff fallback

    @staticmethod
    def get_agent_memory(agent_name: str, retrieved_memories: Dict[str, Any]) -> str:
        """
        Filters and formats retrieved memories specifically tailored for the target agent
        to keep prompts highly relevant.
        """
        summary = retrieved_memories.get("summary", "")
        entities = retrieved_memories.get("entities", {})
        episodic = retrieved_memories.get("episodic", [])
        vector = retrieved_memories.get("vector", {})

        # Build context based on agent specialty
        parts = []
        if summary:
            parts.append(f"Session Summary:\n{summary}")

        if entities:
            # Filter entities relevant to agent, or general if none
            import json
            parts.append(f"Identified Entities:\n{json.dumps(entities, indent=2)}")

        if episodic:
            episodic_lines = [f"- {m}" for m in episodic[:3]]
            parts.append("Recent Interactions:\n" + "\n".join(episodic_lines))

        if vector and agent_name in ["knowledge_agent", "hr_agent"]:
            parts.append(f"Relevant Policy/SOP Docs:\n{json.dumps(vector, indent=2)}")

        return "\n\n".join(parts)

    @staticmethod
    async def update_after_interaction(user_id: str, thread_id: str, query: str, response: str, db: Any):
        """
        Saves user query/response interaction into episodic memory.
        """
        from src.memory.episodic_memory import save_episodic_memory
        memory_text = f"User asked: '{query}'. Agent replied: '{response}'"
        await save_episodic_memory(user_id, memory_text, 0.8, db)

