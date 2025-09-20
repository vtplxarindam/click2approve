from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app.models.approval_request import ApprovalStatus
from app.schemas.user_file import UserFileResponse


class ApprovalRequestSubmit(BaseModel):
    user_file_ids: List[int]
    emails: List[EmailStr]
    approve_by: Optional[datetime] = None
    comment: Optional[str] = None


class ApprovalRequestTaskResponse(BaseModel):
    id: int
    approver: str
    status: ApprovalStatus
    completed: Optional[datetime] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalRequestResponse(BaseModel):
    id: int
    submitted: datetime
    author: str
    status: ApprovalStatus
    user_files: List[UserFileResponse]
    approvers: List[str]
    approve_by: Optional[datetime] = None
    comment: Optional[str] = None
    tasks: List[ApprovalRequestTaskResponse]

    class Config:
        from_attributes = True


class ApprovalRequestTaskComplete(BaseModel):
    id: int
    status: ApprovalStatus
    comment: Optional[str] = None