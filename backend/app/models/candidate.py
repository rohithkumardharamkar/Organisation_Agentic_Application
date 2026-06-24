from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base

class Candidate(Base):
    __tablename__ = "candidates"
    
    candidate_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    job_id = Column(Integer, ForeignKey("job_openings.job_id"), nullable=False)
    status = Column(String(50), default="Applied")  # Applied, Screening, Interviewing, Offered, Rejected
    resume_url = Column(String(255), nullable=True)
    applied_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("JobOpening")
