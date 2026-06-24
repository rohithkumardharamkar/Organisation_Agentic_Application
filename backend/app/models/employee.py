from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from src.core.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    joining_date = Column(Date, nullable=True)
    location = Column(String(100), nullable=True)
    employment_status = Column(String(50), nullable=True, default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    manager = relationship("Employee", remote_side=[employee_id], backref="subordinates")
    skills = relationship("EmployeeSkill", back_populates="employee")
    allocations = relationship("ResourceAllocation", back_populates="employee")
    timesheets = relationship("Timesheet", back_populates="employee")
    leaves = relationship("LeaveRecord", back_populates="employee")

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=True)

    employee_skills = relationship("EmployeeSkill", back_populates="skill")

class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.skill_id"), nullable=False)
    proficiency = Column(String(50), nullable=True) # e.g. Beginner, Intermediate, Expert

    employee = relationship("Employee", back_populates="skills")
    skill = relationship("Skill", back_populates="employee_skills")
