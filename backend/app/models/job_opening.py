from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.core.database import Base

class JobOpening(Base):
    __tablename__ = "job_openings"
    
    job_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    status = Column(String(50), default="Open")  # Open, Closed
    created_at = Column(DateTime, default=datetime.utcnow)
