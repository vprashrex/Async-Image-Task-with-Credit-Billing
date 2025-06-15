from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)   
    
    @validator('username')
    def validate_username(cls, v):
        # Only allow alphanumeric, underscore, and hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscore, and hyphen')
        # Check for reserved usernames
        if v.lower() in ['admin', 'root', 'system', 'api', 'null', 'undefined', 'test', 'guest']:
            raise ValueError('Username not allowed')
        return v.lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)    
    
    @validator('password')
    def validate_password(cls, v):
        # Enhanced password strength validation
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        # Check for common weak passwords
        weak_patterns = ['password', '123456', 'qwerty', 'abc123', 'admin']
        if any(pattern in v.lower() for pattern in weak_patterns):
            raise ValueError('Password contains common weak patterns')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    credits: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    credits: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionInfo(BaseModel):
    session_id: str
    device_type: str
    ip_address: str
    location: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_remember_me: bool


class SecuritySummary(BaseModel):
    active_sessions: int
    session_details: list[SessionInfo]
    recent_security_events: list[dict]


class SecurityEvent(BaseModel):
    event_type: str
    severity: str
    created_at: datetime
    ip_address: str
    success: bool
