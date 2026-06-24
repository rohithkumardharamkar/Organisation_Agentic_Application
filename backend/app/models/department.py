from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Department(Base):
    __tablename__ = "departments"
    
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String(255), unique=True, nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    budget = Column(Float, nullable=True)

    # Relationships
    manager = relationship("Employee", foreign_keys=[manager_id])
