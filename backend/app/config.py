from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # JWT - Enhanced security validation
    JWT_SECRET: str = Field(default=os.getenv("JWT_SECRET", ""), min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER: int = 30

    # Razorpay - Enhanced security validation
    RAZORPAY_KEY_ID: str = Field(default=os.getenv("RAZORPAY_KEY_ID", ""), min_length=1)
    RAZORPAY_KEY_SECRET: str = Field(
        default=os.getenv("RAZORPAY_KEY_SECRET", ""), min_length=10
    )
    RAZORPAY_WEBHOOK_SECRET: str = Field(
        default=os.getenv("RAZORPAY_WEBHOOK_SECRET", ""), min_length=10
    )
    WEBHOOK_SHARED_SECRET: str = Field(default=os.getenv("WEBHOOK_SHARED_SECRET", ""))

    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    
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
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Virtual Space Tech Backend"
    
    # Session Security
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_MAX_AGE: int = 7 * 24 * 3600  # 7 days in seconds

    # Enhanced Security Settings
    MAX_CONCURRENT_SESSIONS: int = 5
    TOKEN_CLEANUP_INTERVAL_HOURS: int = 24
    SECURITY_LOG_RETENTION_DAYS: int = 90
    ENABLE_DEVICE_TRACKING: bool = True
    ENABLE_LOCATION_TRACKING: bool = False
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 5

    BACKEND_CORS_ORIGINS: List[str] = ["https://async-image-task-with-credit-billin.vercel.app"] if ENVIRONMENT == "production" else ["http://localhost:3001"]
    SESSION_COOKIE_SECURE: bool = True if ENVIRONMENT == "production" else False
    SESSION_COOKIE_SAMESITE: str = "none" if ENVIRONMENT == "production" else "lax"


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

# Print the actual values
print(f"Environment: {settings.ENVIRONMENT}")
print(f"Using CORS origins: {settings.BACKEND_CORS_ORIGINS}")
print(f"Using SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
print(f"Using SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)