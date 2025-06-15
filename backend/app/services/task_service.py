from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.redis_utils import redis_manager
from app.utils.file_handler import get_file_url


class TaskService:
    def __init__(self, db: Session):
        self.db = db   
    def create_task(self, task_create: TaskCreate, user_id: int, image_path: str) -> Task:
        """Create a new task"""
        db_task = Task(
            user_id=user_id,
            title=task_create.title,
            description=task_create.description,
            processing_metadata=task_create.processing_metadata,  # Changed to match new field name
            original_image_path=image_path,
            status="queued"
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_task_by_id(self, task_id: int, user_id: Optional[int] = None) -> Optional[Task]:
        """Get task by ID, optionally filtered by user"""
        query = self.db.query(Task).filter(Task.id == task_id)
        if user_id:
            query = query.filter(Task.user_id == user_id)
        return query.first()

    def get_user_tasks(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks for a user"""
        return (
            self.db.query(Task)
            .filter(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_tasks(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks (admin only)"""
        return (
            self.db.query(Task)
            .order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )    
    
    def update_task_status(self, task_id: int, status: str, **kwargs) -> Optional[Task]:
        """Update task status and other fields with immediate Redis publishing"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            old_status = task.status
            task.status = status
            
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # Update timestamp
            task.updated_at = datetime.utcnow()
            
            # Set completed_at if task is completed or failed
            if status in ['completed', 'failed'] and not task.completed_at:
                task.completed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
            
            print(f"🔄 Task {task_id} status updated: {old_status} → {status}")
            
            # Immediately publish task update to Redis
            self._publish_task_update(task)
            
        return task

    def update_task_celery_id(self, task_id: int, celery_task_id: str) -> Optional[Task]:
        """Update task with Celery task ID"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.celery_task_id = celery_task_id
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def _publish_task_update(self, task: Task):
        """Publish task update to Redis for SSE with enhanced data"""
        try:
            task_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "original_image_url": get_file_url(task.original_image_path) if task.original_image_path else None,
                "processed_image_url": get_file_url(task.processed_image_path) if task.processed_image_path else None,
                "metadata": task.processing_metadata,
                "error_message": task.error_message,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "user_id": task.user_id,
                "processing_type": "real_time_update"
            }
            
            print(f"🚀 Publishing task update - ID: {task.id}, Status: {task.status}, User: {task.user_id}")
            result = redis_manager.publish_task_update(task.user_id, task_data)
            print(f"✅ Published to {result} subscribers")
            
        except Exception as e:
            # Log error but don't fail the task update
            print(f"❌ Failed to publish task update to Redis: {e}")
            import traceback
            traceback.print_exc()
