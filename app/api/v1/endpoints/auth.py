from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.schemas.user import (
    UserCreate, UserLogin, TokenResponse, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ResendConfirmationRequest,
    UserInfo
)
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    await user_service.create_user(user_data.email, user_data.password)
    
    if settings.EMAIL_SERVICE_ENABLED:
        email_service = EmailService()
        # In a real implementation, you'd generate a proper confirmation token
        confirmation_link = f"{settings.UI_BASE_URL}/confirmEmail?userId=placeholder&code=placeholder"
        await email_service.send_confirmation_email(user_data.email, confirmation_link)
    
    return {"message": "User created successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if settings.EMAIL_SERVICE_ENABLED and not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not confirmed"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    email = await verify_token(token_data.refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_service = UserService(db)
    user = await user_service.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/confirmEmail")
async def confirm_email(
    userId: str = Query(...),
    code: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # In a real implementation, you'd validate the code properly
    user_service = UserService(db)
    success = await user_service.confirm_email(userId)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email confirmation failed"
        )
    
    return {"message": "Email confirmed successfully"}


@router.post("/resendConfirmationEmail")
async def resend_confirmation_email(
    request: ResendConfirmationRequest,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_by_email(request.email)
    
    if user and not user.email_confirmed:
        email_service = EmailService()
        confirmation_link = f"{settings.UI_BASE_URL}/confirmEmail?userId={user.id}&code=placeholder"
        await email_service.send_confirmation_email(request.email, confirmation_link)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a confirmation link has been sent"}


@router.post("/forgotPassword")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_by_email(request.email)
    
    if user:
        email_service = EmailService()
        reset_link = f"{settings.UI_BASE_URL}/resetPassword?email={request.email}&code=placeholder"
        await email_service.send_password_reset_email(request.email, reset_link)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/resetPassword")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # In a real implementation, you'd validate the reset code
    user_service = UserService(db)
    success = await user_service.reset_password(request.email, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed"
        )
    
    return {"message": "Password reset successfully"}


@router.get("/manage/info", response_model=UserInfo)
async def get_user_info(current_user: User = Depends(get_current_user)):
    return UserInfo(
        email=current_user.email,
        is_email_confirmed=current_user.email_confirmed
    )