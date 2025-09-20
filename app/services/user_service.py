from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.core.exceptions import ValidationException, AuthenticationException


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.normalized_email == email.upper())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password: str) -> User:
        # Check if user already exists
        existing_user = await self.get_by_email(email)
        if existing_user:
            raise ValidationException("User with this email already exists")

        # Validate password
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValidationException(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            normalized_email=email.upper(),
            password_hash=get_password_hash(password),
            email_confirmed=not settings.EMAIL_SERVICE_ENABLED,  # Auto-confirm if email service disabled
            lockout_enabled=settings.LOCKOUT_ENABLED
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user:
            return None

        # Check lockout
        if user.lockout_enabled and user.lockout_end and user.lockout_end > datetime.utcnow():
            raise AuthenticationException("Account is locked")

        if not verify_password(password, user.password_hash):
            # Increment failed attempts
            user.access_failed_count += 1
            if user.access_failed_count >= settings.LOCKOUT_MAX_ATTEMPTS:
                user.lockout_end = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_TIME_MINUTES)
            await self.db.commit()
            return None

        # Reset failed attempts on successful login
        if user.access_failed_count > 0:
            user.access_failed_count = 0
            user.lockout_end = None
            await self.db.commit()

        return user

    async def confirm_email(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.email_confirmed = True
        await self.db.commit()
        return True

    async def reset_password(self, email: str, new_password: str) -> bool:
        user = await self.get_by_email(email)
        if not user:
            return False
        
        user.password_hash = get_password_hash(new_password)
        user.access_failed_count = 0
        user.lockout_end = None
        await self.db.commit()
        return True