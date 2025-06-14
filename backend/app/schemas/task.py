from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    processing_metadata: Optional[Dict[str, Any]] = None

    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        # Remove excessive whitespace and sanitize
        cleaned = re.sub(r'\s+', ' ', v.strip())
        if len(cleaned) < 1:
            raise ValueError('Title must contain at least one character')
        return cleaned

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            # Sanitize description
            cleaned = re.sub(r'\s+', ' ', v.strip())
            return cleaned if cleaned else None
        return v

    @validator('processing_metadata')
    def validate_processing_metadata(cls, v):
        if v is not None:
            # Limit metadata size and validate structure
            if len(str(v)) > 1000:
                raise ValueError('Processing metadata too large')
            
            # Ensure it's a simple dict with string keys
            if not isinstance(v, dict):
                raise ValueError('Processing metadata must be a dictionary')
            
            for key, value in v.items():
                if not isinstance(key, str) or len(key) > 50:
                    raise ValueError('Invalid metadata key')
                if isinstance(value, str) and len(value) > 200:
                    raise ValueError('Metadata value too long')
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = None


class Task(TaskBase):
    id: int
    user_id: int
    status: str
    original_image_path: Optional[str] = None
    processed_image_path: Optional[str] = None
    celery_task_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    original_image_url: Optional[str] = None
    processed_image_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Frontend expects 'metadata', not 'processing_metadata'
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
