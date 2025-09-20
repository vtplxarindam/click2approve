from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, BigInteger, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base
from app.models.user_file import approval_request_files


class ApprovalStatus(Enum):
    SUBMITTED = 0
    APPROVED = 1
    REJECTED = 2


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(BigInteger, primary_key=True, index=True)
    submitted = Column(DateTime, default=datetime.utcnow)
    author = Column(String(256), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.SUBMITTED)
    approve_by = Column(DateTime, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Relationships
    author_user = relationship("User", back_populates="approval_requests")
    user_files = relationship("UserFile", secondary=approval_request_files, back_populates="approval_requests")
    tasks = relationship("ApprovalRequestTask", back_populates="approval_request", cascade="all, delete-orphan")