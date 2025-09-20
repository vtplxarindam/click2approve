from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import UploadFile
import os
import aiofiles

from app.models.user import User
from app.models.user_file import UserFile
from app.models.approval_request_task import ApprovalRequestTask
from app.core.config import settings
from app.core.exceptions import ValidationException, NotFoundException
from app.services.audit_log_service import AuditLogService


class UserFileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditLogService(db)

    async def check_limitations(self, user: User, files: List[UploadFile]):
        # Check file count limit
        if settings.MAX_FILE_COUNT > 0:
            result = await self.db.execute(
                select(UserFile).where(UserFile.owner_id == user.id)
            )
            current_count = len(result.scalars().all())
            if current_count + len(files) > settings.MAX_FILE_COUNT:
                raise ValidationException(f"Maximum file count ({settings.MAX_FILE_COUNT}) exceeded")

        # Check file size limit
        for file in files:
            if file.size and file.size > settings.MAX_FILE_SIZE_BYTES:
                raise ValidationException(f"File {file.filename} exceeds maximum size ({settings.MAX_FILE_SIZE_BYTES} bytes)")

    async def upload_files(self, user: User, files: List[UploadFile]) -> List[UserFile]:
        await self.check_limitations(user, files)
        
        uploaded_files = []
        for file in files:
            # Create user file record
            user_file = UserFile(
                name=file.filename,
                type=os.path.splitext(file.filename)[1] if file.filename else "",
                size=file.size or 0,
                owner_id=user.id
            )
            
            self.db.add(user_file)
            await self.db.flush()  # Get the ID
            
            # Save physical file
            file_path = self._get_file_path(user.id, str(user_file.id), file.filename)
            await self._save_file(file, file_path)
            
            uploaded_files.append(user_file)
            
            # Audit log
            await self.audit_service.log(
                user.normalized_email,
                "Uploaded user file",
                f"File: {user_file.name}, Size: {user_file.size}"
            )
        
        await self.db.commit()
        return uploaded_files

    async def list_files(self, user: User) -> List[UserFile]:
        result = await self.db.execute(
            select(UserFile).where(UserFile.owner_id == user.id).order_by(UserFile.created.desc())
        )
        return result.scalars().all()

    async def download_file(self, user: User, file_id: int) -> Tuple[str, bytes]:
        # Check if user owns the file or is an approver
        result = await self.db.execute(
            select(UserFile).where(UserFile.id == file_id)
        )
        user_file = result.scalar_one_or_none()
        
        if not user_file:
            raise NotFoundException("File not found")
        
        # Check permissions
        can_access = user_file.owner_id == user.id
        
        if not can_access:
            # Check if user is an approver for this file
            result = await self.db.execute(
                select(ApprovalRequestTask).where(
                    and_(
                        ApprovalRequestTask.approver == user.normalized_email,
                        ApprovalRequestTask.approval_request.has(
                            user_files=user_file
                        )
                    )
                )
            )
            can_access = result.scalar_one_or_none() is not None
        
        if not can_access:
            raise NotFoundException("File not found")
        
        # Read file
        file_path = self._get_file_path(user_file.owner_id, str(user_file.id), user_file.name)
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            return user_file.name, content
        except FileNotFoundError:
            raise NotFoundException("File not found on disk")

    async def delete_file(self, user: User, file_id: int):
        result = await self.db.execute(
            select(UserFile).where(and_(UserFile.id == file_id, UserFile.owner_id == user.id))
        )
        user_file = result.scalar_one_or_none()
        
        if not user_file:
            raise NotFoundException("File not found")
        
        # Delete physical file
        file_path = self._get_file_path(user.id, str(file_id), user_file.name)
        try:
            os.remove(file_path)
            # Remove directory if empty
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)
        except FileNotFoundError:
            pass  # File already deleted
        
        # Delete from database
        await self.db.delete(user_file)
        
        # Audit log
        await self.audit_service.log(
            user.normalized_email,
            "Deleted user file",
            f"File: {user_file.name}"
        )
        
        await self.db.commit()

    def _get_file_path(self, user_id: str, file_id: str, filename: str) -> str:
        return os.path.join(settings.FILE_STORAGE_ROOT_PATH, user_id, file_id, filename)

    async def _save_file(self, upload_file: UploadFile, file_path: str):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()
            await f.write(content)