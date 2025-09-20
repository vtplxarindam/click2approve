from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import base64
import io
import mimetypes

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user_file import UserFileResponse
from app.services.user_file_service import UserFileService

router = APIRouter()


@router.post("/upload", response_model=List[UserFileResponse])
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_service = UserFileService(db)
    uploaded_files = await file_service.upload_files(current_user, files)
    return uploaded_files


@router.get("/list", response_model=List[UserFileResponse])
async def list_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_service = UserFileService(db)
    files = await file_service.list_files(current_user)
    return files


@router.get("/download")
async def download_file(
    id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_service = UserFileService(db)
    filename, content = await file_service.download_file(current_user, id)
    
    # Determine content type
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/downloadBase64")
async def download_file_base64(
    id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_service = UserFileService(db)
    filename, content = await file_service.download_file(current_user, id)
    
    # Determine content type
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    # Encode to base64
    base64_content = base64.b64encode(content).decode('utf-8')
    return f"data:{content_type};base64,{base64_content}"


@router.delete("/")
async def delete_file(
    id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_service = UserFileService(db)
    await file_service.delete_file(current_user, id)
    return {"message": "File deleted successfully"}