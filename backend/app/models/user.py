from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Employee") # Employee, Process Engineer, HR, Reporting Manager
    created_at = Column(DateTime, default=datetime.utcnow)
