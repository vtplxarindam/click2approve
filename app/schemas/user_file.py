from pydantic import BaseModel
from typing import List
from datetime import datetime


class UserFileBase(BaseModel):
    name: str
    type: str
    size: int


class UserFileCreate(UserFileBase):
    pass


class UserFileResponse(UserFileBase):
    id: int
    created: datetime

    class Config:
        from_attributes = True


class UserFileListResponse(BaseModel):
    files: List[UserFileResponse]