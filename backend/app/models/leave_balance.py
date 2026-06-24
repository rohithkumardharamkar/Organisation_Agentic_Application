from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class LeaveBalance(Base):
    __tablename__ = "leave_balance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    leave_type = Column(String(50), nullable=False)  # Sick, Vacation, Personal, Casual, Compensatory
    allocated = Column(Integer, default=0)
    used = Column(Integer, default=0)
    pending = Column(Integer, default=0)

    # Relationships
    employee = relationship("Employee")
