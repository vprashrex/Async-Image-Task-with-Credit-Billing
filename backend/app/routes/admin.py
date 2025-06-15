from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_admin_user
from app.schemas.user import UserResponse
from app.schemas.task import TaskResponse
from app.services.user_service import UserService
from app.services.task_service import TaskService
from app.utils.file_handler import get_file_url
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    user_service = UserService(db)
    users = user_service.get_all_users(skip, limit)
    return users


@router.get("/tasks", response_model=List[TaskResponse])
async def get_all_tasks(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all tasks across all users (admin only)"""
    task_service = TaskService(db)
    tasks = task_service.get_all_tasks(skip, limit)
    
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            original_image_url=get_file_url(task.original_image_path),
            processed_image_url=get_file_url(task.processed_image_path),
            metadata=task.metadata,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at
        )
        for task in tasks
    ]


@router.get("/stats")
async def get_admin_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    user_service = UserService(db)
    task_service = TaskService(db)
    
    # Get basic counts
    total_users = len(user_service.get_all_users(limit=10000))
    total_tasks = len(task_service.get_all_tasks(limit=10000))
    
    return {
        "total_users": total_users,
        "total_tasks": total_tasks,
        "active_users": len([u for u in user_service.get_all_users(limit=10000) if u.is_active]),
        "admin_users": len([u for u in user_service.get_all_users(limit=10000) if u.is_admin])
    }
