from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    normalized_email = Column(String(256), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    email_confirmed = Column(Boolean, default=False)
    lockout_end = Column(DateTime, nullable=True)
    lockout_enabled = Column(Boolean, default=True)
    access_failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_files = relationship("UserFile", back_populates="owner", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="author_user", cascade="all, delete-orphan")
    approval_tasks = relationship("ApprovalRequestTask", back_populates="approver_user", cascade="all, delete-orphan")