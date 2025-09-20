from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.audit_log import AuditLogEntry


class AuditLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, who: str, what: str, data: str):
        entry = AuditLogEntry(
            who=who,
            when=datetime.utcnow(),
            what=what,
            data=data
        )
        self.db.add(entry)
        await self.db.commit()