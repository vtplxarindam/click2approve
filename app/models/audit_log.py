from sqlalchemy import Column, String, DateTime, BigInteger, Text
from datetime import datetime
from app.core.database import Base


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id = Column(BigInteger, primary_key=True, index=True)
    who = Column(String(256), nullable=False)
    when = Column(DateTime, default=datetime.utcnow)
    what = Column(String(500), nullable=False)
    data = Column(Text, nullable=False)