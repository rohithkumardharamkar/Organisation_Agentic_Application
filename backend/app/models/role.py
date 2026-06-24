from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(255), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    base_salary = Column(Float, nullable=True)

    # Relationships
    department = relationship("Department")
