from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from src.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(100), nullable=False)
    agent = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # PASSED, FAILED, BLOCKED, etc.
    details = Column(Text, nullable=True)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    document_name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON string
    embedding = Column(Text, nullable=False)     # JSON representation of vector

class SummaryMemory(Base):
    __tablename__ = "summary_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    profile_id = Column(Integer, default=1)
    summary_text = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReflectionMemory(Base):
    __tablename__ = "reflections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    issue = Column(Text, nullable=False)
    lesson_learned = Column(Text, nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    thread_id = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # human, ai
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class EntityMemory(Base):
    __tablename__ = "entity_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    entity_name = Column(String(100), nullable=False)
    entity_value = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EpisodicMemory(Base):
    __tablename__ = "episodic_memories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default="user_1", nullable=False)
    memory = Column(Text, nullable=False)
    importance = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class PendingApproval(Base):
    __tablename__ = "pending_approvals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(100), nullable=False)
    action_type = Column(String(100), nullable=False)  # Leave Approval, Employee Promotion, Resource Allocation, Candidate Selection, Budget Approval
    description = Column(Text, nullable=False)
    risk_level = Column(String(50), default="medium")  # Medium, High, Critical
    status = Column(String(50), default="Pending")      # Pending, Approved, Rejected
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_cases = Column(Integer, default=0)
    routing_accuracy = Column(Float, default=0.0)
    tool_selection_accuracy = Column(Float, default=0.0)
    hallucination_rate = Column(Float, default=0.0)
    rag_precision = Column(Float, default=0.0)
    rag_recall = Column(Float, default=0.0)
    agent_success_rate = Column(Float, default=0.0)
    workflow_completion_rate = Column(Float, default=0.0)
    user_satisfaction_score = Column(Float, default=0.0)

class EvaluationCaseResult(Base):
    __tablename__ = "evaluation_case_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, nullable=False)  # FK to evaluation_runs
    query = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)
    expected_agent = Column(String(100), nullable=True)
    actual_agent = Column(String(100), nullable=True)
    routing_correct = Column(Boolean, default=False)
    tool_selected = Column(String(150), nullable=True)
    tool_correct = Column(Boolean, default=False)
    hallucination_detected = Column(Boolean, default=False)
    rag_precision = Column(Float, default=0.0)
    rag_recall = Column(Float, default=0.0)
    success = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)

