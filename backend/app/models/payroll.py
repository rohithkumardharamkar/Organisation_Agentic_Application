from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base

class Payroll(Base):
    __tablename__ = "payroll"
    
    payroll_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, nullable=False)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_salary = Column(Float, nullable=False)
    payment_status = Column(String(50), default="Paid")  # Paid, Pending
    payment_date = Column(DateTime, nullable=True)

    # Relationships
    employee = relationship("Employee")
