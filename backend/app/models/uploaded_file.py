from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.core.database import Base

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    category = Column(String(100), nullable=True)
    uploaded_by = Column(String(100), nullable=True)
    allowed_roles = Column(String(255), nullable=True) # comma-separated list of roles
    version = Column(Integer, default=1)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
