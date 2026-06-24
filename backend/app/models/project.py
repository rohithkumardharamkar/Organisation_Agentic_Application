from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from src.core.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True, default="Active")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    budget = Column(Float, nullable=True)
    planned_hours = Column(Float, nullable=True)
    project_manager_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    priority = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    manager = relationship("Employee", foreign_keys=[project_manager_id])
    allocations = relationship("ResourceAllocation", back_populates="project")
    timesheets = relationship("Timesheet", back_populates="project")

class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"
    
    allocation_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    allocation_percentage = Column(Float, nullable=False, default=100.0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    employee = relationship("Employee", back_populates="allocations")
    project = relationship("Project", back_populates="allocations")
