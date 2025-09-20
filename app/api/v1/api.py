from fastapi import APIRouter

from app.api.v1.endpoints import auth, user_files, approval_requests, approval_tasks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/account", tags=["authentication"])
api_router.include_router(user_files.router, prefix="/file", tags=["files"])
api_router.include_router(approval_requests.router, prefix="/request", tags=["approval-requests"])
api_router.include_router(approval_tasks.router, prefix="/task", tags=["approval-tasks"])