from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, BigInteger, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Association table for many-to-many relationship between UserFile and ApprovalRequest
approval_request_files = Table(
    'approval_request_files',
    Base.metadata,
    Column('approval_request_id', BigInteger, ForeignKey('approval_requests.id')),
    Column('user_file_id', BigInteger, ForeignKey('user_files.id'))
)


class UserFile(Base):
    __tablename__ = "user_files"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    size = Column(BigInteger, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="user_files")
    approval_requests = relationship("ApprovalRequest", secondary=approval_request_files, back_populates="user_files")