from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.approval_request import ApprovalStatus


class ApprovalRequestTask(Base):
    __tablename__ = "approval_request_tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    approval_request_id = Column(BigInteger, ForeignKey("approval_requests.id"), nullable=False)
    approver = Column(String(256), nullable=False)
    approver_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.SUBMITTED)
    completed = Column(DateTime, nullable=True)
    comment = Column(Text, nullable=True)
    
    # Relationships
    approval_request = relationship("ApprovalRequest", back_populates="tasks")
    approver_user = relationship("User", back_populates="approval_tasks")