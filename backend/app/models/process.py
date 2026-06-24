from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from src.core.database import Base

class ProcessReport(Base):
    __tablename__ = "process_reports"
    
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    
    report_date = Column(Date, nullable=False)
    report_type = Column(String(50), nullable=False) # Daily, Weekly, Sprint, Monthly
    timeframe_label = Column(String(100), nullable=False) # e.g., "Sprint 42"
    
    achievements = Column(Text, nullable=True)
    risks_identified = Column(Text, nullable=True)
    missing_requirements = Column(Text, nullable=True)
    future_improvements = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", backref="process_reports")
    employee = relationship("Employee", backref="process_reports")
