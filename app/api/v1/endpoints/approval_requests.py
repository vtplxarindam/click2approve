from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.approval_request import ApprovalRequestSubmit, ApprovalRequestResponse
from app.services.approval_request_service import ApprovalRequestService

router = APIRouter()


@router.post("/")
async def submit_approval_request(
    request_data: ApprovalRequestSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    await service.submit_approval_request(current_user, request_data)
    return {"message": "Approval request submitted successfully"}


@router.delete("/")
async def delete_approval_request(
    id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    await service.delete_approval_request(current_user, id)
    return {"message": "Approval request deleted successfully"}


@router.get("/list", response_model=List[ApprovalRequestResponse])
async def list_approval_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ApprovalRequestService(db)
    requests = await service.list_approval_requests(current_user)
    
    # Convert to response format
    response_data = []
    for req in requests:
        response_data.append(ApprovalRequestResponse(
            id=req.id,
            submitted=req.submitted,
            author=req.author,
            status=req.status,
            user_files=req.user_files,
            approvers=[task.approver for task in req.tasks],
            approve_by=req.approve_by,
            comment=req.comment,
            tasks=req.tasks
        ))
    
    return response_data