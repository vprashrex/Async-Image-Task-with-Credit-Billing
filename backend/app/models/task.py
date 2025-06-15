from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="queued")  # queued, processing, completed, failed
    original_image_path = Column(String)
    processed_image_path = Column(String)
    processing_metadata = Column(JSON)  # Changed from task_metadata to processing_metadata
    celery_task_id = Column(String, unique=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationship
    user = relationship("User", back_populates="tasks")


# Add tasks relationship to User model
from app.models.user import User
User.tasks = relationship("Task", back_populates="user")
