from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER: int = 30

    # Razorpay
    RAZORPAY_KEY_ID: str = Field(min_length=1)
    RAZORPAY_KEY_SECRET: str = Field(min_length=10)
    RAZORPAY_WEBHOOK_SECRET: str = Field(min_length=10)
    WEBHOOK_SHARED_SECRET: str = ""

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    # Application Settings
    APP_NAME: str = "Virtual Space Tech Backend"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Virtual Space Tech Backend"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Session Security
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "none" if ENVIRONMENT == 'development' else "lax"
    SESSION_COOKIE_MAX_AGE: int = 7 * 24 * 3600  # 7 days

    # Enhanced Security Settings
    MAX_CONCURRENT_SESSIONS: int = 5
    TOKEN_CLEANUP_INTERVAL_HOURS: int = 24
    SECURITY_LOG_RETENTION_DAYS: int = 90

    # Device and Session Tracking
    ENABLE_DEVICE_TRACKING: bool = True
    ENABLE_LOCATION_TRACKING: bool = False
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 5

    # Validators
    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @validator("RAZORPAY_KEY_SECRET")
    def validate_razorpay_secret(cls, v):
        if not v or len(v) < 10:
            raise ValueError("RAZORPAY_KEY_SECRET must be at least 10 characters long")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
