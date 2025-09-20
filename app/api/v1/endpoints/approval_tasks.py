from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.approval_request import ApprovalStatus
from app.schemas.approval_request import ApprovalRequestTaskComplete, ApprovalRequestTaskResponse
from app.services.approval_request_service import ApprovalRequestService

router = APIRouter()


@router.post("/complete")
async def complete_task(
    task_data: ApprovalRequestTaskComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    await service.complete_task(current_user, task_data)
    return {"message": "Task completed successfully"}


@router.get("/listUncompleted", response_model=List[ApprovalRequestTaskResponse])
async def list_uncompleted_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    tasks = await service.list_tasks(current_user, [ApprovalStatus.SUBMITTED])
    return tasks


@router.get("/listCompleted", response_model=List[ApprovalRequestTaskResponse])
async def list_completed_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    tasks = await service.list_tasks(current_user, [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED])
    return tasks


@router.get("/countUncompleted")
async def count_uncompleted_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    count = await service.count_uncompleted_tasks(current_user)
    return count