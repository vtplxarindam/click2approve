from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import validator


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+aiomysql://user:password@localhost/click2approve"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3333"]
    
    # File Storage
    FILE_STORAGE_ROOT_PATH: str = "/filestorage"
    
    # Email Settings
    EMAIL_SERVICE_ENABLED: bool = False
    EMAIL_DEFAULT_FROM: Optional[str] = None
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    # UI Settings
    UI_BASE_URL: str = "http://localhost:3333/ui"
    
    # Limitations
    MAX_FILE_COUNT: int = 10
    MAX_FILE_SIZE_BYTES: int = 4194304  # 4MB
    MAX_APPROVAL_REQUEST_COUNT: int = 10
    MAX_APPROVER_COUNT: int = 10
    
    # Identity Settings
    PASSWORD_MIN_LENGTH: int = 8
    LOCKOUT_MAX_ATTEMPTS: int = 3
    LOCKOUT_TIME_MINUTES: int = 5
    LOCKOUT_ENABLED: bool = True
    
    # Hangfire/Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    JOB_EXPIRATION_TIMEOUT_MIN: int = 30

    class Config:
        env_file = ".env"


settings = Settings()