from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
import logging
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.task import TaskResponse, TaskCreate
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.utils.file_handler import save_file, get_file_url
from app.utils.redis_utils import RedisManager
from app.utils.security import handle_service_error, validate_user_input, log_security_event
from app.workers.image_processor import process_image_task
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def task_updates_stream(request: Request, user_id: int):
    """SSE stream for task updates with heartbeat and infinite listening"""
    redis_manager = RedisManager()
    pubsub = redis_manager.subscribe_to_user_tasks(user_id)
    
    import time
    last_heartbeat = time.time()
    heartbeat_interval = 15  # Send heartbeat every 15 seconds
    
    try:
        print(f"🔥 SSE stream started for user {user_id}")
        
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'message': f'Connected to task updates for user {user_id}', 'user_id': user_id})}\n\n"
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                print(f"💀 Client disconnected for user {user_id}")
                break
                
            try:
                # Non-blocking check for Redis messages (no timeout for infinite listening)
                message = redis_manager.get_message(timeout=0.1)
                
                if message and message['type'] == 'message':
                    try:
                        # Forward the task update immediately
                        task_data = json.loads(message['data'])
                        print(f"📢 Broadcasting task update for user {user_id}: {task_data.get('status', 'unknown')}")
                        yield f"data: {json.dumps({'type': 'task_update', 'data': task_data, 'timestamp': time.time()})}\n\n"
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        continue
                
                # Send heartbeat to keep connection alive
                current_time = time.time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': current_time, 'user_id': user_id})}\n\n"
                    last_heartbeat = current_time
                    print(f"💓 Heartbeat sent for user {user_id}")
                
                # Very small delay to prevent CPU spinning while maintaining responsiveness
                await asyncio.sleep(0.05)
                
            except Exception as e:
                print(f"⚠️ SSE stream error for user {user_id}: {e}")
                # Send error message but continue streaming
                yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': time.time()})}\n\n"
                await asyncio.sleep(0.5)
                
    except Exception as e:
        print(f"💥 SSE stream connection error for user {user_id}: {e}")
    finally:
        print(f"🔚 Cleaning up SSE stream for user {user_id}")
        redis_manager.unsubscribe_from_user_tasks(user_id)
        redis_manager.close()


@router.get("/stream")
async def stream_task_updates(
    request: Request,
    db: Session = Depends(get_db)
):
    """SSE endpoint for real-time task updates"""   
    from app.dependencies import get_current_user_from_cookie
    
    # Get user from cookie since EventSource can't send custom headers
    try:
        current_user = await get_current_user_from_cookie(request, db)
        print(f"Authenticated user: {current_user.email}")
    except Exception as e:
        print(f"Authentication failed: {e}")
        error_message = str(e)  # Capture the error message
        
        # Return error stream
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': f'Authentication failed: {error_message}'})}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Headers": "Cache-Control, Accept",
                "Access-Control-Allow-Methods": "GET",
            }
        )    
    
    return StreamingResponse(
        task_updates_stream(request, current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true", 
            "Access-Control-Allow-Headers": "Cache-Control, Accept",
            "Access-Control-Allow-Methods": "GET",
        }
    )


@router.post("/", response_model=TaskResponse)
async def create_task(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    processing_operation: str = Form("grayscale"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new image processing task"""
    try:
        print(f"Creating task for user {current_user.id} with operation {processing_operation}")
        # Validate and sanitize inputs
        title = validate_user_input(title, "title", 200)
        if description:
            description = validate_user_input(description, "description", 1000)
        
        user_service = UserService(db)
        task_service = TaskService(db)
        
        # Check if user has credits
        if current_user.credits <= 0:
            log_security_event("insufficient_credits", current_user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient credits. Please purchase more credits."
            )
        
        # Save uploaded file with validation
        image_path = save_file(file, "original")
        
        # Create task
        task_create = TaskCreate(
            title=title,
            description=description,
            processing_metadata={"processing_operation": processing_operation}
        )
        
        task = task_service.create_task(task_create, current_user.id, image_path)
        
        # Deduct credit atomically
        if not user_service.deduct_credit(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to process payment. Please try again."
            )
        
        # Start async processing
        celery_task = process_image_task.delay(
            task.id, 
            image_path, 
            current_user.id,
            {"operation": processing_operation}
        )
        
        # Update task with Celery task ID
        task_service.update_task_celery_id(task.id, celery_task.id)
        
        logger.info(f"Task created successfully: {task.id} for user {current_user.id}")
        
        # Return response
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            original_image_url=get_file_url(task.original_image_path),
            processed_image_url=None,
            metadata=task.processing_metadata,
            error_message=None,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task creation failed for user {current_user.id}: {str(e)}")
        raise handle_service_error(e, "Failed to create task")


@router.get("/", response_model=List[TaskResponse])
async def get_user_tasks(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for the current user"""
    task_service = TaskService(db)
    tasks = task_service.get_user_tasks(current_user.id, skip, limit)
    
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            original_image_url=get_file_url(task.original_image_path),
            processed_image_url=get_file_url(task.processed_image_path),
            metadata=task.processing_metadata if isinstance(task.processing_metadata, dict) else {},
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific task"""
    task_service = TaskService(db)
    task = task_service.get_task_by_id(task_id, current_user.id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        original_image_url=get_file_url(task.original_image_path),
        processed_image_url=get_file_url(task.processed_image_path),
        metadata=task.processing_metadata,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at
    )
