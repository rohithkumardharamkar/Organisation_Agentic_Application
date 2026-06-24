from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from src.core.database import Base

class Timesheet(Base):
    __tablename__ = "timesheets"
    
    timesheet_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    work_date = Column(Date, nullable=False)
    hours_logged = Column(Float, nullable=False)
    activity_type = Column(String(100), nullable=True) # e.g., Development, Meeting
    note = Column(String(500), nullable=True)
    submission_status = Column(String(50), nullable=True, default="Draft") # Draft, Submitted
    approval_status = Column(String(50), nullable=True, default="Pending") # Pending, Approved, Rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="timesheets")
    project = relationship("Project", back_populates="timesheets")

class LeaveRecord(Base):
    __tablename__ = "leave_records"
    
    leave_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    leave_type = Column(String(50), nullable=False) # Sick, Vacation, Personal, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    approval_status = Column(String(50), nullable=True, default="Pending") # Pending, Approved, Rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="leaves")
