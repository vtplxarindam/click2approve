from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.user import User
from app.models.user_file import UserFile
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.approval_request_task import ApprovalRequestTask
from app.schemas.approval_request import ApprovalRequestSubmit, ApprovalRequestTaskComplete
from app.core.config import settings
from app.core.exceptions import ValidationException, NotFoundException
from app.services.audit_log_service import AuditLogService
from app.services.email_service import EmailService


class ApprovalRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditLogService(db)
        self.email_service = EmailService()

    async def check_limitations(self, user: User, payload: ApprovalRequestSubmit):
        # Check approval request count limit
        if settings.MAX_APPROVAL_REQUEST_COUNT > 0:
            result = await self.db.execute(
                select(ApprovalRequest).where(ApprovalRequest.author == user.normalized_email)
            )
            current_count = len(result.scalars().all())
            if current_count + 1 > settings.MAX_APPROVAL_REQUEST_COUNT:
                raise ValidationException(f"Maximum approval request count ({settings.MAX_APPROVAL_REQUEST_COUNT}) exceeded")

        # Check approver count limit
        if settings.MAX_APPROVER_COUNT > 0:
            if len(payload.emails) > settings.MAX_APPROVER_COUNT:
                raise ValidationException(f"Maximum approver count ({settings.MAX_APPROVER_COUNT}) exceeded")

    async def submit_approval_request(self, user: User, payload: ApprovalRequestSubmit):
        await self.check_limitations(user, payload)

        # Get user files
        result = await self.db.execute(
            select(UserFile).where(
                and_(
                    UserFile.id.in_(payload.user_file_ids),
                    UserFile.owner_id == user.id
                )
            )
        )
        user_files = result.scalars().all()
        
        if len(user_files) != len(payload.user_file_ids):
            raise ValidationException("Some files not found or not owned by user")

        # Create approval request
        approval_request = ApprovalRequest(
            author=user.normalized_email,
            author_id=user.id,
            approve_by=payload.approve_by,
            comment=payload.comment,
            user_files=user_files
        )
        
        self.db.add(approval_request)
        await self.db.flush()  # Get the ID

        # Create tasks for each approver
        normalized_emails = [email.upper() for email in payload.emails]
        for approver_email in normalized_emails:
            task = ApprovalRequestTask(
                approval_request_id=approval_request.id,
                approver=approver_email
            )
            self.db.add(task)

        await self.db.commit()

        # Audit log
        await self.audit_service.log(
            user.normalized_email,
            "Submitted approval request",
            f"Request ID: {approval_request.id}, Files: {len(user_files)}"
        )

        # Send email notifications
        for email in payload.emails:
            await self.email_service.send_approval_request_notification(
                email.lower(),
                user.email.lower(),
                [f.name for f in user_files]
            )

    async def delete_approval_request(self, user: User, request_id: int):
        result = await self.db.execute(
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.tasks), selectinload(ApprovalRequest.user_files))
            .where(and_(ApprovalRequest.id == request_id, ApprovalRequest.author == user.normalized_email))
        )
        approval_request = result.scalar_one_or_none()
        
        if not approval_request:
            raise NotFoundException("Approval request not found")

        # Get approvers for notification
        approvers = [task.approver for task in approval_request.tasks]
        file_names = [f.name for f in approval_request.user_files]

        await self.db.delete(approval_request)
        await self.db.commit()

        # Audit log
        await self.audit_service.log(
            user.normalized_email,
            "Deleted approval request",
            f"Request ID: {request_id}"
        )

        # Send email notifications
        for approver in approvers:
            await self.email_service.send_approval_request_deleted_notification(
                approver.lower(),
                user.email.lower(),
                file_names
            )

    async def list_approval_requests(self, user: User) -> List[ApprovalRequest]:
        result = await self.db.execute(
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.user_files), selectinload(ApprovalRequest.tasks))
            .where(ApprovalRequest.author == user.normalized_email)
            .order_by(ApprovalRequest.id.desc())
        )
        return result.scalars().all()

    async def list_tasks(self, user: User, statuses: List[ApprovalStatus]) -> List[ApprovalRequestTask]:
        result = await self.db.execute(
            select(ApprovalRequestTask)
            .options(selectinload(ApprovalRequestTask.approval_request).selectinload(ApprovalRequest.user_files))
            .where(
                and_(
                    ApprovalRequestTask.approver == user.normalized_email,
                    ApprovalRequestTask.status.in_(statuses)
                )
            )
            .order_by(ApprovalRequestTask.id.desc())
        )
        return result.scalars().all()

    async def complete_task(self, user: User, payload: ApprovalRequestTaskComplete):
        result = await self.db.execute(
            select(ApprovalRequestTask)
            .options(
                selectinload(ApprovalRequestTask.approval_request)
                .selectinload(ApprovalRequest.user_files),
                selectinload(ApprovalRequestTask.approval_request)
                .selectinload(ApprovalRequest.tasks)
            )
            .where(
                and_(
                    ApprovalRequestTask.id == payload.id,
                    ApprovalRequestTask.approver == user.normalized_email
                )
            )
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise NotFoundException("Task not found")
        
        if task.status != ApprovalStatus.SUBMITTED:
            raise ValidationException("Task is already completed")

        # Complete the task
        task.status = payload.status
        task.comment = payload.comment
        task.completed = datetime.utcnow()

        # Update approval request status if needed
        approval_request = task.approval_request
        if approval_request.status == ApprovalStatus.SUBMITTED:
            if payload.status == ApprovalStatus.REJECTED:
                approval_request.status = ApprovalStatus.REJECTED
            elif payload.status == ApprovalStatus.APPROVED:
                # Check if all other tasks are completed
                other_pending_tasks = [
                    t for t in approval_request.tasks 
                    if t.id != task.id and t.status == ApprovalStatus.SUBMITTED
                ]
                if not other_pending_tasks:
                    approval_request.status = ApprovalStatus.APPROVED

        await self.db.commit()

        # Audit log
        await self.audit_service.log(
            user.normalized_email,
            "Completed task",
            f"Task ID: {task.id}, Status: {payload.status.name}"
        )

        # Send email notification to requester
        await self.email_service.send_approval_request_reviewed_notification(
            approval_request.author.lower(),
            user.email.lower(),
            [f.name for f in approval_request.user_files]
        )

    async def count_uncompleted_tasks(self, user: User) -> int:
        result = await self.db.execute(
            select(ApprovalRequestTask).where(
                and_(
                    ApprovalRequestTask.approver == user.normalized_email,
                    ApprovalRequestTask.status == ApprovalStatus.SUBMITTED
                )
            )
        )
        return len(result.scalars().all())