from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.core.database import Base

class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    
    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # HR Policy, IT Guide, Travel Policy
    content = Column(Text, nullable=False)
    version = Column(String(50), default="1.0")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
